import pypandoc
import zipfile
from typing import List
from pathlib import Path

"""Module for file export and archiving.

I have deliberately made this a module-of-functions, with no:
    - classes
    - module-level variables
    - Canvas objects
    
In my experience, this is a good pattern for file I/O. 
"""

# If zlib is available, use it to compress the archive.
try:
    import zlib

    compression = zipfile.ZIP_DEFLATED
except (ImportError, AttributeError):
    compression = zipfile.ZIP_STORED

modes = {zipfile.ZIP_DEFLATED: "deflated", zipfile.ZIP_STORED: "stored"}


def create_dir(dir_path: Path) -> None:
    """Create a directory, does nothing if dir already exists.

    :param dir_path: Path to directory to be created
    :return: None
    """
    dir_path.mkdir(parents=True, exist_ok=True)


def make_texfile(rendered_latex: str, latex_filepath: Path) -> None:
    """Write rendered LaTeX to a .tex file.

    :param rendered_latex: plaintext of rendered LaTeX document
    :param latex_filepath: destination Path to write LaTeX to file
    :return: None
    """
    with latex_filepath.open("w+") as f:
        f.write(rendered_latex)


def make_docx(latex_filepath: str, docx_filepath: Path) -> None:
    """Create .docx file from LaTeX document.

    Due to limitations in pypandoc/pandoc itself, pypandoc.convert_file must
    be used to create a .docx file. Otherwise, the LaTeX parameter could
    be a string of rendered LaTeX as in make_texfile.

    :param latex_filepath: source Path of LaTeX document
    :param docx_filepath: destination Path to write .docx to file
    :return: None
    """
    pypandoc.convert_file(str(latex_filepath), "docx", outputfile=str(docx_filepath))


def make_archive(archive_name: Path, files: List[Path], figures: Path) -> None:
    """Add files to .zip archive, compressing if possible.

    :param archive_name: destination Path to write .zip to file
    :param files: list of file Paths to include in archive
    :param figures: Path to directory containing all figures
    :return: None
    """
    with zipfile.ZipFile(str(archive_name), mode="w") as zf:
        for filename in files:
            zf.write(str(filename), compress_type=compression)

        for filename in figures.glob("**/*"):
            zf.write(str(filename), compress_type=compression)
