import argparse
import os
import shutil
import sys
from pathlib import Path
from converters import documento_converter, presentacion_converter, hoja_calculo_converter, pdf_txt_converter

def get_category(ext):
    ext = ext.lower().replace(".", "")
    if ext in ['docx', 'odt']:
        return 'document'
    if ext in ['pptx', 'odp']:
        return 'presentation'
    if ext in ['xlsx', 'ods']:
        return 'spreadsheet'
    if ext in ['pdf', 'txt']:
        return 'generic_or_target'
    return None

def _convert_txt_to_target(txt_path: str, output_format: str, output_dir: str):
    """Convert a TXT file to the target format using the appropriate converter."""
    cat = get_category(output_format)
    if cat == 'document':
        documento_converter.convert(txt_path, output_format, output_dir)
    elif cat == 'presentation':
        presentacion_converter.convert(txt_path, output_format, output_dir)
    elif cat == 'spreadsheet':
        hoja_calculo_converter.convert(txt_path, output_format, output_dir)
    else:
        raise ValueError(f"Cannot convert TXT to {output_format}")

def convert_file(input_path: str, output_format: str, output_dir: str, use_ocr: bool = False):
    if not os.path.exists(input_path):
        print(f"Error: File {input_path} does not exist.", file=sys.stderr)
        return False
        
    input_ext = Path(input_path).suffix.lower()[1:]
    output_format = output_format.lower().replace(".", "")
    
    try:
        # Special case for generic PDF <-> TXT conversion
        if (input_ext == 'pdf' and output_format == 'txt'):
            output_file_name = f"{Path(input_path).stem}.txt"
            out_path = os.path.join(output_dir, output_file_name)
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            pdf_txt_converter.convert_pdf_to_txt(input_path, out_path, use_ocr)
            print("Success")
            return True
            
        if (input_ext == 'txt' and output_format == 'pdf'):
            documento_converter.convert(input_path, output_format, output_dir)
            print("Success")
            return True

        category = get_category(input_ext)
        if not category:
            print(f"Error: Unsupported or unknown input format ({input_ext}).", file=sys.stderr)
            return False

        # PDF -> any non-TXT format: convert to temp TXT first, then to target
        if input_ext == 'pdf':
            tmp_dir = os.path.join(output_dir, f"_pdf_tmp_{Path(input_path).stem}")
            Path(tmp_dir).mkdir(parents=True, exist_ok=True)
            tmp_txt = os.path.join(tmp_dir, f"{Path(input_path).stem}.txt")
            pdf_txt_converter.convert_pdf_to_txt(input_path, tmp_txt, use_ocr)
            _convert_txt_to_target(tmp_txt, output_format, output_dir)
            shutil.rmtree(tmp_dir, ignore_errors=True)
            print("Success")
            return True

        if category == 'document':
            documento_converter.convert(input_path, output_format, output_dir)
        elif category == 'presentation':
            presentacion_converter.convert(input_path, output_format, output_dir)
        elif category == 'spreadsheet':
            hoja_calculo_converter.convert(input_path, output_format, output_dir)
        elif category == 'generic_or_target':
            # E.g. txt to docx needs to look at the output format
            out_category = get_category(output_format)
            if out_category == 'document':
                documento_converter.convert(input_path, output_format, output_dir)
            elif out_category == 'presentation':
                presentacion_converter.convert(input_path, output_format, output_dir)
            elif out_category == 'spreadsheet':
                hoja_calculo_converter.convert(input_path, output_format, output_dir)
            else:
                print(f"Error: Invalid conversion from {input_ext} to {output_format}", file=sys.stderr)
                return False
                
        print("Success")
        return True
        
    except ValueError as ve:
        print(f"Validation error for {input_path}: {ve}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Error processing {input_path}: {e}", file=sys.stderr)
        return False

def main():
    parser = argparse.ArgumentParser(description="Multi-format document conversion tool.")
    parser.add_argument("input_path", help="Input file or directory")
    parser.add_argument("--to", required=True, help="Desired output format (e.g. pdf, txt, docx)")
    parser.add_argument("--output", help="Output path or directory (default: same as input)")
    parser.add_argument("--ocr", action="store_true", help="Use OCR (pytesseract) to extract text from scanned PDFs")
    
    args = parser.parse_args()
    
    input_path = args.input_path
    output_format = args.to
    use_ocr = args.ocr
    
    if os.path.isdir(input_path):
        # Batch mode
        output_dir = args.output if args.output else input_path
        success_count = 0
        fail_count = 0
        
        for file_name in os.listdir(input_path):
            file_path = os.path.join(input_path, file_name)
            if os.path.isfile(file_path):
                # Attempt to convert, ignore unsupported quietly or print?
                # The requirements say: "incluyendo mezclas de formatos de entrada"
                # We should try to convert formats we know.
                ext = Path(file_path).suffix.lower()[1:]
                cat = get_category(ext)
                if cat is not None:
                    if convert_file(file_path, output_format, output_dir, use_ocr):
                        success_count += 1
                    else:
                        fail_count += 1
        print(f"Batch finished. Success: {success_count}, Failures: {fail_count}")
        
    elif os.path.isfile(input_path):
        # Single file
        output_dir = args.output if args.output else os.path.dirname(os.path.abspath(input_path))
        if not output_dir:
            output_dir = "."
        
        convert_file(input_path, output_format, output_dir, use_ocr)
    else:
        print(f"Error: {input_path} is not a valid file or directory.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
