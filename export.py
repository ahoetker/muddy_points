import pypandoc
import zipfile
from typing import List
from pathlib import Path

try:
    import zlib
    compression = zipfile.ZIP_DEFLATED
except (ImportError, AttributeError):
    compression = zipfile.ZIP_STORED

modes = {
    zipfile.ZIP_DEFLATED: 'deflated',
    zipfile.ZIP_STORED: 'stored',
}

def create_dir(dir_path: Path) -> None:
    dir_path.mkdir(parents=True, exist_ok=True)

def make_texfile(rendered_latex: str, latex_filepath: Path) -> None:
    with latex_filepath.open("w+") as f:
        f.write(rendered_latex)

def make_docx(latex_filepath: str , docx_filepath: Path) -> None:
    pypandoc.convert_file(str(latex_filepath), "docx", outputfile=str(docx_filepath))

def make_archive(archive_name: Path, files: List[Path], figures: Path):
    with zipfile.ZipFile(str(archive_name), mode='w') as zf:
        for filename in files:
            zf.write(str(filename), compress_type=compression)

        for filename in figures.glob("**/*"):
            zf.write(str(filename), compress_type=compression)

