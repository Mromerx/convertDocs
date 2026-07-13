import pdfplumber
import pdf2image
import pytesseract

def convert_pdf_to_txt(input_path: str, output_path: str, use_ocr: bool = False):
    """
    Extracts text from a PDF and saves it to a TXT file.
    If use_ocr is True, attempts to use Tesseract OCR to read images in the PDF.
    """
    text_content = []
    
    if use_ocr:
        # Check if tesseract is installed
        try:
            pytesseract.get_tesseract_version()
        except pytesseract.TesseractNotFoundError:
            raise RuntimeError("Tesseract OCR is not installed or not in PATH. Please install Tesseract to use the --ocr flag.")
        
        try:
            images = pdf2image.convert_from_path(input_path)
            for i, image in enumerate(images):
                page_text = pytesseract.image_to_string(image)
                text_content.append(f"--- Page {i + 1} ---\n{page_text}")
        except Exception as e:
            raise RuntimeError(f"OCR processing failed: {e}")
    else:
        try:
            with pdfplumber.open(input_path) as pdf:
                has_text = False
                for i, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text and page_text.strip():
                        has_text = True
                        text_content.append(f"--- Page {i + 1} ---\n{page_text}")
                    else:
                        text_content.append(f"--- Page {i + 1} ---\n[Could not extract text. This page may be a scanned image. Consider using the --ocr option.]")
                
                if not has_text:
                    print("WARNING: Could not extract text from PDF. It is likely a scanned document. Consider using --ocr.")
        except Exception as e:
            raise RuntimeError(f"Failed to read PDF: {e}")
            
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n\n".join(text_content))
    
    return output_path

