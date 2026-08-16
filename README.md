# Multi-format Document Converter

A CLI tool for converting documents, presentations and spreadsheets between multiple formats, including generic PDF/text conversions and page-level cut/merge operations.

## Requirements

**LibreOffice** (headless) is the main engine for faithful conversions between Office/OpenDocument formats and PDF.

- **Linux**: `sudo apt install libreoffice`
- **macOS**: `brew install libreoffice`
- **Windows**: Download from [libreoffice.org](https://www.libreoffice.org/download/)

**Tesseract** (optional, for OCR on scanned PDFs):
- **Linux**: `sudo apt install tesseract-ocr`
- **macOS**: `brew install tesseract`
- **Windows**: Download from [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki)

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
python convertDocs.py <file_or_dir> --to <format> [--output <path>] [--ocr]
python convertDocs.py <file> --to <filename.ext> [--output <path>] [--ocr]
python convertDocs.py cut <file> <range> [--output <path>]
python convertDocs.py merge <file1> <file2> [<file3> ...] [--output <path>]
```

- `--to <format>` — saves as `<input_stem>.<format>` (e.g. `doc.docx --to pdf` → `doc.pdf`)
- `--to <filename.ext>` — saves with a custom filename (e.g. `doc.docx --to final.pdf` → `final.pdf`)
- If the output file already exists, it auto-renames with `(1)`, `(2)`, etc. (e.g. `final (1).pdf`)
- `cut` / `merge` — keep the same format as the input; `--output` may be a directory or a full output path (default: `<stem>_cut.<ext>` / `<stem>_merged.<ext>` next to the input). See [Cut & merge](#cut--merge).

## Install as Global Command

After installing, you can make `convertDocs` available from any directory.

### Linux / macOS

Create a wrapper script in `~/.local/bin/` (make sure it's in your PATH):

```bash
cat > ~/.local/bin/convertDocs << 'EOF'
#!/bin/bash
exec /path/to/convertDocs/.venv/bin/python /path/to/convertDocs/convertDocs.py "$@"
EOF
chmod +x ~/.local/bin/convertDocs
```

> Replace `/path/to/convertDocs` with the actual path (e.g. `/home/user/Programs/convertDocs`).

Now you can run `convertDocs` from anywhere:

```bash
convertDocs "document.docx" --to pdf
```

### Windows

Create a batch file named `convertDocs.cmd` in a directory that's in your PATH (e.g. `C:\Users\YourUser\AppData\Local\Microsoft\WindowsApps\`):

```batch
@echo off
"C:\path\to\convertDocs\.venv\Scripts\python.exe" "C:\path\to\convertDocs\convertDocs.py" %*
```

Or add the project's `.venv\Scripts` directory to your PATH and create an alias:

```batch
doskey convertDocs=python C:\path\to\convertDocs\convertDocs.py $*
```

> Replace `C:\path\to\convertDocs` with the actual path (e.g. `C:\Users\YourUser\Programs\convertDocs`).

## Supported Formats

| Category | Microsoft | OpenDocument | Universal |
|---|---|---|---|
| Document | .docx | .odt | .pdf, .txt |
| Presentation | .pptx | .odp | .pdf, .txt |
| Spreadsheet | .xlsx | .ods | .pdf, .txt |

## Examples

### Document conversions

| Command | Description |
|---|---|
| `convertDocs file.docx --to pdf` | DOCX to PDF |
| `convertDocs file.docx --to odt` | DOCX to ODT |
| `convertDocs file.docx --to txt` | DOCX to TXT |
| `convertDocs file.odt --to pdf` | ODT to PDF |
| `convertDocs file.odt --to docx` | ODT to DOCX |
| `convertDocs file.odt --to txt` | ODT to TXT |
| `convertDocs file.txt --to pdf` | TXT to PDF |
| `convertDocs file.txt --to docx` | TXT to DOCX |
| `convertDocs file.txt --to odt` | TXT to ODT |
| `convertDocs file.pdf --to docx` | PDF to DOCX (via text extraction) |
| `convertDocs file.pdf --to odt` | PDF to ODT (via text extraction) |

### Presentation conversions

| Command | Description |
|---|---|
| `convertDocs file.pptx --to pdf` | PPTX to PDF |
| `convertDocs file.pptx --to odp` | PPTX to ODP |
| `convertDocs file.pptx --to txt` | PPTX to TXT (extracts slide text + speaker notes) |
| `convertDocs file.odp --to pdf` | ODP to PDF |
| `convertDocs file.odp --to pptx` | ODP to PPTX |
| `convertDocs file.odp --to txt` | ODP to TXT |
| `convertDocs file.txt --to pptx` | TXT to PPTX (paragraphs split by blank lines) |
| `convertDocs file.txt --to odp` | TXT to ODP |
| `convertDocs file.pdf --to pptx` | PDF to PPTX (via text extraction) |
| `convertDocs file.pdf --to odp` | PDF to ODP (via text extraction) |

### Spreadsheet conversions

| Command | Description |
|---|---|
| `convertDocs file.xlsx --to pdf` | XLSX to PDF |
| `convertDocs file.xlsx --to ods` | XLSX to ODS |
| `convertDocs file.xlsx --to txt` | XLSX to TXT (tab-separated cell values) |
| `convertDocs file.ods --to pdf` | ODS to PDF |
| `convertDocs file.ods --to xlsx` | ODS to XLSX |
| `convertDocs file.ods --to txt` | ODS to TXT (tab-separated cell values) |
| `convertDocs file.txt --to xlsx` | TXT to XLSX (tab-separated values) |
| `convertDocs file.txt --to ods` | TXT to ODS |
| `convertDocs file.pdf --to xlsx` | PDF to XLSX (via text extraction) |
| `convertDocs file.pdf --to ods` | PDF to ODS (via text extraction) |

### PDF <-> TXT specific

| Command | Description |
|---|---|
| `convertDocs file.pdf --to txt` | Extract text from PDF |
| `convertDocs file.pdf --to txt --ocr` | Extract text using OCR (requires Tesseract) |
| `convertDocs file.txt --to pdf` | Create a simple PDF from a text file |

### Cut & merge

`cut` keeps one page range of a document; `merge` concatenates 2 or more documents. Output keeps the same format as the input (non-PDF formats are routed through PDF internally).

```bash
convertDocs cut <file> <range> [--output <path>]
convertDocs merge <file1> <file2> [<file3> ...] [--output <path>]
```

Ranges are 0-based with an exclusive end (`0-1` → page 1 only, `1-34` → pages 2 to 34, `3` → page 4 only). The `-` separator needs no shell quoting.

| Command | Description |
|---|---|
| `convertDocs cut doc.pdf 0-1` | Keep only the first page |
| `convertDocs cut doc.pdf 1-34` | Keep pages 2 to 34 |
| `convertDocs cut doc.pdf 5-20 --output out.pdf` | Keep pages 6 to 20, saved as `out.pdf` |
| `convertDocs cut doc.docx 3-10` | Cut a DOCX, result stays DOCX |
| `convertDocs merge a.pdf b.pdf c.pdf` | Merge 3 PDFs into `a_merged.pdf` |
| `convertDocs merge a.docx b.docx --output combo.docx` | Merge 2 DOCX files |
| `convertDocs merge a.pdf b.docx --output combo.docx` | Merge mixed PDF+DOCX into a DOCX |

Supported: `pdf`, `docx`, `odt`, `pptx`, `odp` — inputs and output can be any combination of these. Not supported (no page model): `txt`, `xlsx`, `ods`.

- Same-format inputs merge keeping that format (`--output` optional).
- Mixed-format inputs require `--output <name>.<ext>`; the extension defines the output format (e.g. `--output combo.pdf`). Each input is converted to PDF internally, merged, and converted back.

> Note: for non-PDF formats the cut/merge run through PDF internally (via LibreOffice), so the result is a re-imported reconstruction and may lose some original structure. PDF gives full fidelity.

### Batch conversion

| Command | Description |
|---|---|
| `convertDocs . --to pdf` | Convert all supported files in current dir to PDF |
| `convertDocs . --to pdf --output ./pdfs` | Convert all and save to `./pdfs/` |
| `convertDocs ./docs --to docx --output ./out` | Convert all files in `./docs` to DOCX |
