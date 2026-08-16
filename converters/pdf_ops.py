import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import fitz  # PyMuPDF

from .libreoffice_engine import check_libreoffice_installed, _get_libreoffice_executable, convert_with_libreoffice

SUPPORTED_EXTS = {'pdf', 'docx', 'odt', 'pptx', 'odp'}
REJECTED_EXTS = {'txt', 'xlsx', 'ods'}

_PAGE_RANGE_RE = re.compile(r'^\s*(\d+)(?:\s*-\s*(\d+))?\s*$')


def parse_page_range(spec: str, page_count: int):
    """
    Parse a page range 'A-B' (0-based, end exclusive) or a bare 'N' (single page).

    '0-1'  -> the first page only.
    '1-34' -> pages 2 to 34.
    Returns (start, end).

    The '-' separator avoids shell quoting (unlike ';', which bash splits into
    separate commands).
    """
    if ";" in spec:
        raise ValueError(
            f"Invalid page range '{spec}': use '-' instead of ';' "
            "(e.g. '0-1' -> first page only, '1-34' -> pages 2 to 34). "
            "The '-' form needs no shell quoting."
        )
    m = _PAGE_RANGE_RE.match(spec or "")
    if not m:
        raise ValueError(
            f"Invalid page range '{spec}'. Use 'start-end' with 0-based indices and "
            "exclusive end (e.g. '0-1' -> first page only, '1-34' -> pages 2 to 34, "
            "'3' -> page 4 only). No shell quoting needed."
        )
    start = int(m.group(1))
    end = int(m.group(2)) if m.group(2) is not None else start + 1

    if start >= end:
        raise ValueError(f"Invalid page range '{spec}': start must be less than end.")
    if end > page_count:
        raise ValueError(
            f"Page range '{spec}' is out of bounds: the document has {page_count} page(s) "
            f"(valid indices 0..{page_count - 1})."
        )
    return start, end


def _check_supported(ext: str, op: str) -> None:
    if ext in REJECTED_EXTS:
        raise ValueError(
            f"Cannot {op} a {ext}. Files without an explicit page model "
            "(txt, xlsx, ods) are not supported."
        )
    if ext not in SUPPORTED_EXTS:
        raise ValueError(
            f"Cannot {op}: unsupported format .{ext}. "
            f"Supported: {', '.join(sorted(SUPPORTED_EXTS))}."
        )


def _check_not_encrypted(doc, path: str) -> None:
    if doc.needs_pass:
        raise ValueError(f"PDF is encrypted (requires a password): {path}")


def _to_pdf(input_path: str, tmp_dir: str) -> str:
    if Path(input_path).suffix.lower() == '.pdf':
        return input_path
    return convert_with_libreoffice(input_path, 'pdf', tmp_dir)


# LibreOffice imports PDFs through a specific component's filter. Choosing the
# right one is required to (a) keep all pages and (b) allow the export back.
_PDF_BACK_TARGETS = {
    'docx': ('writer_pdf_import', 'docx'),
    'odt': ('writer_pdf_import', 'odt'),
    'pptx': ('impress_pdf_import', 'pptx:Impress MS PowerPoint 2007 XML'),
    'odp': ('impress_pdf_import', 'odp:impress8'),
}


def _convert_result_back(pdf_path: str, ext: str, tmp_dir: str) -> str:
    """
    Convert a result PDF back to the original non-PDF format via LibreOffice.
    The target-specific import filter keeps all pages and enables the export.
    """
    try:
        infilter, out_filter = _PDF_BACK_TARGETS[ext]
    except KeyError:
        raise ValueError(f"Unsupported target format .{ext}")

    if not check_libreoffice_installed():
        raise RuntimeError("LibreOffice is not installed or not found in PATH.")

    stem = Path(pdf_path).stem
    result_path = str(Path(tmp_dir) / f"{stem}.{ext}")
    profile = str(Path(tmp_dir) / "profile")
    command = [
        _get_libreoffice_executable(),
        f"-env:UserInstallation=file://{profile}",
        "--headless",
        "--infilter=" + infilter,
        "--convert-to",
        out_filter,
        "--outdir",
        tmp_dir,
        pdf_path,
    ]
    subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    if not Path(result_path).exists():
        raise RuntimeError(f"Conversion finished but output file not found at {result_path}")
    print(
        f"NOTE: keeping format as {ext}; the result is a re-imported reconstruction "
        "of the pages and may lose some original structure. Consider PDF for full "
        "fidelity.",
        file=sys.stderr,
    )
    return result_path


def cut_file(input_path: str, page_spec: str, output_path: str) -> str:
    """
    Cut a page range from a document, keeping the original format.
    Non-PDF formats are routed through PDF internally (round-trip).
    """
    ext = Path(input_path).suffix.lower().lstrip('.')
    _check_supported(ext, 'cut')

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    tmp_dir = tempfile.mkdtemp(prefix="convertdocs_cut_")
    try:
        pdf_path = _to_pdf(input_path, tmp_dir)
        doc = fitz.open(pdf_path)
        try:
            _check_not_encrypted(doc, input_path)
            start, end = parse_page_range(page_spec, doc.page_count)
            doc.select(list(range(start, end)))
            cut_pdf = str(Path(tmp_dir) / "result.pdf")
            doc.save(cut_pdf, garbage=4, deflate=True)
        finally:
            doc.close()

        if ext == 'pdf':
            shutil.copy2(cut_pdf, output_path)
        else:
            _convert_result_back(cut_pdf, ext, tmp_dir)
            shutil.copy2(str(Path(tmp_dir) / f"result.{ext}"), output_path)
        return output_path
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def merge_files(paths, output_path: str, target_ext=None) -> str:
    """
    Merge 2 or more documents, keeping target_ext (or the first file's format).
    Inputs may mix any supported format; each is routed through PDF internally.
    """
    if len(paths) < 2:
        raise ValueError("Merge requires at least 2 files.")

    ext = Path(paths[0]).suffix.lower().lstrip('.')
    _check_supported(ext, 'merge')

    for p in paths:
        if not Path(p).exists():
            raise ValueError(f"File {p} does not exist.")
        _check_supported(Path(p).suffix.lower().lstrip('.'), 'merge')

    if target_ext is None:
        target_ext = ext
    if target_ext not in SUPPORTED_EXTS or target_ext in REJECTED_EXTS:
        raise ValueError(
            f"Cannot merge to .{target_ext}. Supported: {', '.join(sorted(SUPPORTED_EXTS))}."
        )

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    tmp_dir = tempfile.mkdtemp(prefix="convertdocs_merge_")
    try:
        merged = fitz.open()
        try:
            for p in paths:
                pdf_path = _to_pdf(p, tmp_dir)
                src = fitz.open(pdf_path)
                try:
                    _check_not_encrypted(src, p)
                    if src.page_count == 0:
                        print(f"WARNING: Skipping empty document (0 pages): {p}", file=sys.stderr)
                        continue
                    merged.insert_pdf(src)
                finally:
                    src.close()
            if merged.page_count == 0:
                raise ValueError("Merge produced an empty document (no pages to merge).")
            merged_pdf = str(Path(tmp_dir) / "result.pdf")
            merged.save(merged_pdf, garbage=4, deflate=True)
        finally:
            merged.close()

        if target_ext == 'pdf':
            shutil.copy2(merged_pdf, output_path)
        else:
            _convert_result_back(merged_pdf, target_ext, tmp_dir)
            shutil.copy2(str(Path(tmp_dir) / f"result.{target_ext}"), output_path)
        return output_path
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)