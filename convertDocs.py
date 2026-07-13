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

def _unique_path(ruta: str) -> str:
    """Return a non-existent path by appending (1), (2)... to the stem if needed."""
    path_obj = Path(ruta)
    if not path_obj.exists():
        return ruta
    stem = path_obj.stem
    ext = path_obj.suffix
    parent = path_obj.parent
    n = 1
    while True:
        new_name = f"{stem} ({n}){ext}"
        new_path = os.path.join(parent, new_name)
        if not os.path.exists(new_path):
            return new_path
        n += 1

def _convert_with_uniqueness(input_path, output_format, output_dir, converter_func, output_name=None):
    """Call converter_func, ensuring the output doesn't overwrite an existing file."""
    if output_name:
        expected = os.path.join(output_dir, output_name)
    else:
        expected = os.path.join(output_dir, f"{Path(input_path).stem}.{output_format}")

    unique = _unique_path(expected)

    if not output_name and unique == expected:
        return converter_func(input_path, output_format, output_dir)

    stem = Path(unique).stem
    ext = Path(input_path).suffix
    temp_input = os.path.join(output_dir, f"{stem}{ext}")
    shutil.copy2(input_path, temp_input)
    try:
        return converter_func(temp_input, output_format, output_dir)
    finally:
        if os.path.exists(temp_input):
            os.remove(temp_input)

def _convert_txt_to_target(txt_path: str, output_format: str, output_dir: str, output_name=None):
    """Convert a TXT file to the target format using the appropriate converter."""
    if output_format == 'txt':
        dest_name = output_name or Path(txt_path).name
        dest = Path(output_dir) / dest_name
        dest = Path(_unique_path(str(dest)))
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(txt_path, str(dest))
        return str(dest)

    cat = get_category(output_format)
    if cat == 'document':
        _convert_with_uniqueness(txt_path, output_format, output_dir, documento_converter.convert, output_name)
    elif cat == 'presentation':
        _convert_with_uniqueness(txt_path, output_format, output_dir, presentacion_converter.convert, output_name)
    elif cat == 'spreadsheet':
        _convert_with_uniqueness(txt_path, output_format, output_dir, hoja_calculo_converter.convert, output_name)
    else:
        raise ValueError(f"Cannot convert TXT to {output_format}")

def convert_file(input_path: str, output_format: str, output_dir: str, use_ocr: bool = False, output_name=None):
    if not os.path.exists(input_path):
        print(f"Error: File {input_path} does not exist.", file=sys.stderr)
        return False
        
    input_ext = Path(input_path).suffix.lower()[1:]
    output_format = output_format.lower().replace(".", "")
    
    try:
        if (input_ext == 'pdf' and output_format == 'txt'):
            out_name = output_name or f"{Path(input_path).stem}.txt"
            out_path = os.path.join(output_dir, out_name)
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            out_path = _unique_path(out_path)
            pdf_txt_converter.convert_pdf_to_txt(input_path, out_path, use_ocr)
            print("Success")
            return True
            
        if (input_ext == 'txt' and output_format == 'pdf'):
            _convert_with_uniqueness(input_path, output_format, output_dir, documento_converter.convert, output_name)
            print("Success")
            return True

        if use_ocr and input_ext != 'pdf':
            tmp_dir = str(Path(output_dir) / f"_ocr_tmp_{Path(input_path).stem}")
            Path(tmp_dir).mkdir(parents=True, exist_ok=True)
            try:
                cat = get_category(input_ext)
                if cat == 'document':
                    documento_converter.convert(input_path, 'pdf', tmp_dir)
                elif cat == 'presentation':
                    presentacion_converter.convert(input_path, 'pdf', tmp_dir)
                elif cat == 'spreadsheet':
                    hoja_calculo_converter.convert(input_path, 'pdf', tmp_dir)
                else:
                    raise ValueError(f"Cannot convert {input_ext} to PDF for OCR")

                tmp_pdf = str(Path(tmp_dir) / f"{Path(input_path).stem}.pdf")
                tmp_txt = str(Path(tmp_dir) / f"{Path(input_path).stem}.txt")
                pdf_txt_converter.convert_pdf_to_txt(tmp_pdf, tmp_txt, use_ocr=True)
                _convert_txt_to_target(tmp_txt, output_format, output_dir, output_name)
            finally:
                shutil.rmtree(tmp_dir, ignore_errors=True)
            print("Success")
            return True

        category = get_category(input_ext)
        if not category:
            print(f"Error: Unsupported or unknown input format ({input_ext}).", file=sys.stderr)
            return False

        if input_ext == 'pdf':
            tmp_dir = os.path.join(output_dir, f"_pdf_tmp_{Path(input_path).stem}")
            Path(tmp_dir).mkdir(parents=True, exist_ok=True)
            tmp_txt = os.path.join(tmp_dir, f"{Path(input_path).stem}.txt")
            pdf_txt_converter.convert_pdf_to_txt(input_path, tmp_txt, use_ocr)
            _convert_txt_to_target(tmp_txt, output_format, output_dir, output_name)
            shutil.rmtree(tmp_dir, ignore_errors=True)
            print("Success")
            return True

        if category == 'document':
            _convert_with_uniqueness(input_path, output_format, output_dir, documento_converter.convert, output_name)
        elif category == 'presentation':
            _convert_with_uniqueness(input_path, output_format, output_dir, presentacion_converter.convert, output_name)
        elif category == 'spreadsheet':
            _convert_with_uniqueness(input_path, output_format, output_dir, hoja_calculo_converter.convert, output_name)
        elif category == 'generic_or_target':
            out_category = get_category(output_format)
            if out_category == 'document':
                _convert_with_uniqueness(input_path, output_format, output_dir, documento_converter.convert, output_name)
            elif out_category == 'presentation':
                _convert_with_uniqueness(input_path, output_format, output_dir, presentacion_converter.convert, output_name)
            elif out_category == 'spreadsheet':
                _convert_with_uniqueness(input_path, output_format, output_dir, hoja_calculo_converter.convert, output_name)
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
    parser.add_argument("--ocr", action="store_true", help="Use OCR (pytesseract) to extract text from scanned documents")
    
    args = parser.parse_args()
    
    input_path = args.input_path
    output_spec = args.to
    use_ocr = args.ocr
    
    if '.' in output_spec and Path(output_spec).stem:
        output_name = output_spec
        output_format = Path(output_spec).suffix.lower().lstrip('.')
    else:
        output_name = None
        output_format = output_spec
    
    if os.path.isdir(input_path):
        output_dir = args.output if args.output else input_path
        success_count = 0
        fail_count = 0
        
        for file_name in os.listdir(input_path):
            file_path = os.path.join(input_path, file_name)
            if os.path.isfile(file_path):
                ext = Path(file_path).suffix.lower()[1:]
                cat = get_category(ext)
                if cat is not None:
                    if convert_file(file_path, output_format, output_dir, use_ocr):
                        success_count += 1
                    else:
                        fail_count += 1
        print(f"Batch finished. Success: {success_count}, Failures: {fail_count}")
        
    elif os.path.isfile(input_path):
        output_dir = args.output if args.output else os.path.dirname(os.path.abspath(input_path))
        if not output_dir:
            output_dir = "."
        
        convert_file(input_path, output_format, output_dir, use_ocr, output_name)
    else:
        print(f"Error: {input_path} is not a valid file or directory.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
