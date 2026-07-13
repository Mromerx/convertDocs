import io

import fitz  # PyMuPDF
import pytesseract
from PIL import Image, ImageEnhance

# psm 6: single uniform block of text — more reliable than psm 3 for
# pages that are entirely image-based (no complex layout analysis that
# could accidentally discard text regions).
# oem 1: LSTM engine only (faster and more accurate than legacy mode).
_TESS_CONFIG = "--psm 6 --oem 1"

# Language(s) for Tesseract. Run 'tesseract --list-langs' to see installed options.
_OCR_LANGUAGE = "spa+eng"

# Target DPI for upscaling low-resolution images before OCR.
_TARGET_DPI = 300


def _prepare_image(img: Image.Image, display_bbox: tuple) -> Image.Image:
    """
    Prepare an image for Tesseract:
    1. Convert to grayscale.
    2. Upscale with LANCZOS if the effective DPI (based on the image's
       actual display size in the PDF) is below the target.
    3. Apply contrast and sharpness enhancement.

    display_bbox: (x0, y0, x1, y1) in PDF points where the image is placed.
    """
    if img.mode != "L":
        img = img.convert("L")

    x0, y0, x1, y1 = display_bbox
    display_w_inches = (x1 - x0) / 72.0
    display_h_inches = (y1 - y0) / 72.0

    if display_w_inches > 0 and display_h_inches > 0:
        effective_dpi = min(
            img.width / display_w_inches,
            img.height / display_h_inches,
        )
        if effective_dpi < _TARGET_DPI:
            scale = _TARGET_DPI / effective_dpi
            img = img.resize(
                (int(img.width * scale), int(img.height * scale)),
                Image.LANCZOS,
            )

    img = ImageEnhance.Contrast(img).enhance(1.5)
    img = ImageEnhance.Sharpness(img).enhance(2.0)
    return img


def _extract_page_ordered(page: fitz.Page, doc: fitz.Document) -> str:
    """
    Extract all text from a page in visual reading order.

    Uses PyMuPDF's get_text("dict") which naturally returns text and image
    blocks interleaved in reading order as they appear on the page.
    """
    parts = []
    
    # sort=True is CRITICAL: it forces PyMuPDF to sort blocks in visual 
    # reading order (top-left to bottom-right). Without it, blocks are 
    # returned in the order they were inserted into the PDF file stream.
    page_dict = page.get_text("dict", sort=True)
    seen_images = set()

    for block in page_dict.get("blocks", []):
        if block.get("type") == 0:  # Text block
            # Reconstruct text from spans
            text_lines = []
            for line in block.get("lines", []):
                line_text = "".join(span.get("text", "") for span in line.get("spans", []))
                text_lines.append(line_text)
            text = "\n".join(text_lines).strip()
            if text:
                parts.append(text)
                
        elif block.get("type") == 1:  # Image block
            image_bytes = block.get("image")
            if not image_bytes:
                continue
                
            # Avoid processing the exact same image multiple times (e.g. logos)
            img_hash = hash(image_bytes)
            if img_hash in seen_images:
                continue
            seen_images.add(img_hash)
            
            bbox = block.get("bbox", (page.rect.x0, page.rect.y0, page.rect.x1, page.rect.y1))
            try:
                img = Image.open(io.BytesIO(image_bytes))
                img = _prepare_image(img, bbox)
                ocr_text = pytesseract.image_to_string(
                    img, lang=_OCR_LANGUAGE, config=_TESS_CONFIG
                ).strip()
                if ocr_text:
                    parts.append(ocr_text)
            except Exception as e:
                parts.append(f"[Image OCR failed: {e}]")

    if not parts:
        # No text or images found: render the full page as a bitmap
        pix = page.get_pixmap(dpi=_TARGET_DPI, colorspace=fitz.csGRAY)
        try:
            img = Image.frombytes("L", [pix.width, pix.height], pix.samples)
            img = ImageEnhance.Contrast(img).enhance(1.5)
            img = ImageEnhance.Sharpness(img).enhance(2.0)
            return pytesseract.image_to_string(img, lang=_OCR_LANGUAGE, config=_TESS_CONFIG)
        finally:
            del pix

    return "\n\n".join(parts)


def convert_pdf_to_txt(input_path: str, output_path: str, use_ocr: bool = False) -> str:
    """
    Extracts text from a PDF and saves it to a TXT file.

    Without --ocr: PyMuPDF native text extraction per page.
    With --ocr: per-page extraction in visual reading order, combining
    native text blocks and OCR'd image blocks sorted by their Y then X
    position on the page.
    """
    text_content: list[str] = []

    if use_ocr:
        try:
            pytesseract.get_tesseract_version()
        except pytesseract.TesseractNotFoundError:
            raise RuntimeError(
                "Tesseract OCR is not installed or not in PATH. "
                "Please install Tesseract to use the --ocr flag."
            )

        doc = fitz.open(input_path)
        try:
            for i, page in enumerate(doc):
                try:
                    text = _extract_page_ordered(page, doc)
                    text_content.append(f"--- Page {i + 1} ---\n{text}")
                except Exception as e:
                    text_content.append(
                        f"--- Page {i + 1} ---\n[Processing failed: {e}]"
                    )
            print(f"INFO: Processed {len(doc)} page(s) with OCR.")
        except Exception as e:
            raise RuntimeError(f"OCR processing failed: {e}") from e
        finally:
            doc.close()

    else:
        doc = fitz.open(input_path)
        try:
            has_text = False
            for i, page in enumerate(doc):
                text = page.get_text("text")
                if text and text.strip():
                    has_text = True
                    text_content.append(f"--- Page {i + 1} ---\n{text}")
                else:
                    text_content.append(
                        f"--- Page {i + 1} ---\n"
                        "[Could not extract text. This page may be a scanned image. "
                        "Consider using the --ocr option.]"
                    )
            if not has_text:
                print(
                    "WARNING: Could not extract text from PDF. "
                    "It is likely a scanned document. Consider using --ocr."
                )
        except Exception as e:
            raise RuntimeError(f"Failed to read PDF: {e}") from e
        finally:
            doc.close()

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n\n".join(text_content))

    return output_path
