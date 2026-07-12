# Convertidor de Documentos Multi-formato

Una herramienta CLI para convertir documentos, presentaciones y hojas de cálculo entre múltiples formatos, incluyendo conversiones genéricas de PDF/texto.

## Requisitos

**LibreOffice** (sin interfaz gráfica) es el motor principal para conversiones fieles entre formatos de Office/OpenDocument y PDF.

- **Linux**: `sudo apt install libreoffice`
- **macOS**: `brew install libreoffice`
- **Windows**: Descargar desde [libreoffice.org](https://www.libreoffice.org/download/download/)

**Tesseract** (opcional, para OCR en PDFs escaneados):
- **Linux**: `sudo apt install tesseract-ocr`
- **macOS**: `brew install tesseract`
- **Windows**: Descargar desde [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki)

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## USO

```bash
python convertDocs.py <archivo_o_directorio> --to <formato> [--output <ruta>] [--ocr]
```

## Instalar como Comando Global

Después de instalar, puedes hacer que `convertDocs` esté disponible desde cualquier directorio.

### Linux / macOS

Crea un script envolvente en `~/.local/bin/` (asegúrate de que esté en tu PATH):

```bash
cat > ~/.local/bin/convertDocs << 'EOF'
#!/bin/bash
exec /ruta/a/convertDocs/.venv/bin/python /ruta/a/convertDocs/convertDocs.py "$@"
EOF
chmod +x ~/.local/bin/convertDocs
```

> Reemplaza `/ruta/a/convertDocs` con la ruta real (ej. `/home/usuario/Programas/convertDocs`).

Ahora puedes ejecutar `convertDocs` desde cualquier lugar:

```bash
convertDocs "documento.docx" --to pdf
```

### Windows

Crea un archivo batch llamado `convertDocs.cmd` en un directorio que esté en tu PATH (ej. `C:\Users\TuUsuario\AppData\Local\Microsoft\WindowsApps\`):

```batch
@echo off
"C:\ruta\a\convertDocs\.venv\Scripts\python.exe" "C:\ruta\a\convertDocs\convertDocs.py" %*
```

O agrega el directorio `.venv\Scripts` del proyecto a tu PATH y crea un alias:

```batch
doskey convertDocs=python C:\ruta\a\convertDocs\convertDocs.py $*
```

> Reemplaza `C:\ruta\a\convertDocs` con la ruta real (ej. `C:\Users\TuUsuario\Programas\convertDocs`).

## Formatos Soportados

| Categoría | Microsoft | OpenDocument | Universal |
|---|---|---|---|
| Documento | .docx | .odt | .pdf, .txt |
| Presentación | .pptx | .odp | .pdf, .txt |
| Hoja de cálculo | .xlsx | .ods | .pdf, .txt |

## Ejemplos

### Conversiones de documentos

| Comando | Descripción |
|---|---|
| `convertDocs archivo.docx --to pdf` | DOCX a PDF |
| `convertDocs archivo.docx --to odt` | DOCX a ODT |
| `convertDocs archivo.docx --to txt` | DOCX a TXT |
| `convertDocs archivo.odt --to pdf` | ODT a PDF |
| `convertDocs archivo.odt --to docx` | ODT a DOCX |
| `convertDocs archivo.odt --to txt` | ODT a TXT |
| `convertDocs archivo.txt --to pdf` | TXT a PDF |
| `convertDocs archivo.txt --to docx` | TXT a DOCX |
| `convertDocs archivo.txt --to odt` | TXT a ODT |
| `convertDocs archivo.pdf --to docx` | PDF a DOCX (vía extracción de texto) |
| `convertDocs archivo.pdf --to odt` | PDF a ODT (vía extracción de texto) |

### Conversiones de presentaciones

| Comando | Descripción |
|---|---|
| `convertDocs archivo.pptx --to pdf` | PPTX a PDF |
| `convertDocs archivo.pptx --to odp` | PPTX a ODP |
| `convertDocs archivo.pptx --to txt` | PPTX a TXT (extrae texto de diapositivas + notas del orador) |
| `convertDocs archivo.odp --to pdf` | ODP a PDF |
| `convertDocs archivo.odp --to pptx` | ODP a PPTX |
| `convertDocs archivo.odp --to txt` | ODP a TXT |
| `convertDocs archivo.txt --to pptx` | TXT a PPTX (párrafos separados por líneas en blanco) |
| `convertDocs archivo.txt --to odp` | TXT a ODP |
| `convertDocs archivo.pdf --to pptx` | PDF a PPTX (vía extracción de texto) |
| `convertDocs archivo.pdf --to odp` | PDF a ODP (vía extracción de texto) |

### Conversiones de hojas de cálculo

| Comando | Descripción |
|---|---|
| `convertDocs archivo.xlsx --to pdf` | XLSX a PDF |
| `convertDocs archivo.xlsx --to ods` | XLSX a ODS |
| `convertDocs archivo.xlsx --to txt` | XLSX a TXT (valores de celdas separados por tabulaciones) |
| `convertDocs archivo.ods --to pdf` | ODS a PDF |
| `convertDocs archivo.ods --to xlsx` | ODS a XLSX |
| `convertDocs archivo.ods --to txt` | ODS a TXT (valores de celdas separados por tabulaciones) |
| `convertDocs archivo.txt --to xlsx` | TXT a XLSX (valores separados por tabulaciones) |
| `convertDocs archivo.txt --to ods` | TXT a ODS |
| `convertDocs archivo.pdf --to xlsx` | PDF a XLSX (vía extracción de texto) |
| `convertDocs archivo.pdf --to ods` | PDF a ODS (vía extracción de texto) |

### PDF <-> TXT específico

| Comando | Descripción |
|---|---|
| `convertDocs archivo.pdf --to txt` | Extraer texto de PDF |
| `convertDocs archivo.pdf --to txt --ocr` | Extraer texto usando OCR (requiere Tesseract) |
| `convertDocs archivo.txt --to pdf` | Crear un PDF simple desde un archivo de texto |

### Conversión por lotes

| Comando | Descripción |
|---|---|
| `convertDocs . --to pdf` | Convertir todos los archivos soportados en el directorio actual a PDF |
| `convertDocs . --to pdf --output ./pdfs` | Convertir todo y guardar en `./pdfs/` |
| `convertDocs ./docs --to docx --output ./out` | Convertir todos los archivos en `./docs` a DOCX |
