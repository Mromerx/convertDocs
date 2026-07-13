import subprocess
import platform
import shutil
from pathlib import Path

def _get_libreoffice_executable():
    """Detects LibreOffice executable based on the OS."""
    system = platform.system()
    if system == "Windows":
        # Common paths for Windows
        paths = [
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"
        ]
        for p in paths:
            if Path(p).exists():
                return p
        return "soffice"  # Assumes it's in PATH
    elif system == "Darwin":
        return "/Applications/LibreOffice.app/Contents/MacOS/soffice"
    else:
        # Linux and others
        return "soffice"

def check_libreoffice_installed():
    """Checks if LibreOffice is installed and accessible."""
    executable = _get_libreoffice_executable()
    if shutil.which(executable) or Path(executable).exists():
        return True
    return False

def convert_with_libreoffice(input_path: str, output_format: str, output_dir: str):
    """
    Converts a file to the specified format using LibreOffice headless mode.
    """
    if not check_libreoffice_installed():
        raise RuntimeError("LibreOffice is not installed or not found in PATH.")

    executable = _get_libreoffice_executable()
    
    # ensure output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    command = [
        executable,
        "--headless",
        "--convert-to",
        output_format,
        "--outdir",
        output_dir,
        input_path
    ]
    
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode('utf-8', errors='ignore')
        raise RuntimeError(f"LibreOffice conversion failed: {error_msg}")
    
    # Determine the expected output file path
    input_file_name = Path(input_path).name
    output_file_name = f"{Path(input_file_name).stem}.{output_format}"
    expected_output_path = Path(output_dir) / output_file_name
    
    if not expected_output_path.exists():
        raise RuntimeError(f"Conversion finished but output file not found at {expected_output_path}")
        
    return str(expected_output_path)
