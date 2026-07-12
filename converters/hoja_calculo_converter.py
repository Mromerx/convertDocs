import os
import csv
import shutil
from pathlib import Path
import openpyxl
from .libreoffice_engine import convert_with_libreoffice

SUPPORTED_FORMATS = ['xlsx', 'ods', 'pdf', 'txt']

def is_supported(ext: str):
    return ext.lower() in SUPPORTED_FORMATS

def convert(input_path: str, output_format: str, output_dir: str):
    """
    Converts a spreadsheet to the specified format.
    """
    input_ext = Path(input_path).suffix.lower()[1:]
    output_format = output_format.lower()
    
    if input_ext == output_format:
        raise ValueError("Input and output format are the same.")
        
    if not is_supported(input_ext) or not is_supported(output_format):
        raise ValueError(f"Format not supported in spreadsheet category. (Supported: {', '.join(SUPPORTED_FORMATS)})")
    
    output_file_name = f"{Path(input_path).stem}.{output_format}"
    output_path = os.path.join(output_dir, output_file_name)
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Text Extraction: XLSX/ODS -> TXT
    if input_ext in ('xlsx', 'ods') and output_format == 'txt':
        if input_ext == 'xlsx':
            wb = openpyxl.load_workbook(input_path, data_only=True)
        else:
            csv_dir = os.path.join(output_dir, f"_csv_tmp_{Path(input_path).stem}")
            Path(csv_dir).mkdir(parents=True, exist_ok=True)
            convert_with_libreoffice(input_path, 'csv', csv_dir)
            csv_path = os.path.join(csv_dir, f"{Path(input_path).stem}.csv")
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = Path(csv_path).stem
            with open(csv_path, 'r', encoding='utf-8-sig') as csv_file:
                reader = csv.reader(csv_file)
                for row in reader:
                    ws.append(row)
            shutil.rmtree(csv_dir, ignore_errors=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            for sheet_name in wb.sheetnames:
                f.write(f"--- Sheet: {sheet_name} ---\n")
                sheet = wb[sheet_name]
                for row in sheet.iter_rows(values_only=True):
                    row_data = [str(cell) if cell is not None else "" for cell in row]
                    if any(row_data):
                        f.write("\t".join(row_data) + "\n")
                f.write("\n")
        return output_path
        
    # Text Generation: TXT -> XLSX/ODS
    elif input_ext == 'txt' and output_format in ('xlsx', 'ods'):
        wb = openpyxl.Workbook()
        ws = wb.active
        
        with open(input_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter='\t')
            for row in reader:
                ws.append(row)
        
        if output_format == 'xlsx':
            wb.save(output_path)
            return output_path
        else:
            tmp_dir = os.path.join(output_dir, f"_tmp_calc_{Path(input_path).stem}")
            Path(tmp_dir).mkdir(parents=True, exist_ok=True)
            tmp_xlsx = os.path.join(tmp_dir, f"{Path(input_path).stem}.xlsx")
            wb.save(tmp_xlsx)
            convert_with_libreoffice(tmp_xlsx, 'ods', tmp_dir)
            tmp_ods = os.path.join(tmp_dir, f"{Path(input_path).stem}.ods")
            shutil.move(tmp_ods, output_path)
            shutil.rmtree(tmp_dir, ignore_errors=True)
            return output_path
        
    elif input_ext in ['xlsx', 'ods', 'txt', 'pdf'] and output_format in ['xlsx', 'ods', 'pdf', 'txt']:
        return convert_with_libreoffice(input_path, output_format, output_dir)
        
    else:
        if input_ext == 'pdf' and output_format == 'txt':
            raise ValueError("Use the generic PDF <-> TXT conversion")
        raise ValueError(f"Conversion {input_ext} -> {output_format} not implemented here.")
