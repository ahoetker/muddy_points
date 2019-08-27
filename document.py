from data_processing import generate_report_contents
from export import create_dir, make_docx, make_texfile, make_archive

import os
import json
from jinja2 import FileSystemLoader
from latex.jinja2 import make_env
from latex import build_pdf
from pathlib import Path


if __name__ == "__main__":
    # Configuration
    course_name = "CHE 334"
    quiz_number = 1
    output_dir = Path("output")
    figures_dir = Path(output_dir / "figures")
    template_file = Path("report_template.tex")
    recipients_file = Path("recipients.txt")
    fetch_new_report = True

    # Create directories if needed
    for d in [output_dir, figures_dir]:
        create_dir(d)

    if fetch_new_report is True:
        contents = generate_report_contents(course_name, quiz_number, figures_dir, recipients_file)
        with open("contents.json", "w+") as f:
            json.dump(contents, f)
    else:
        with open("contents.json", "r") as f:
            contents = json.load(f)

    # Render LaTeX template
    print("Rendering LaTeX Template...")
    env = make_env(loader=FileSystemLoader("."))
    tpl = env.get_template("report_template.tex")
    rendered_latex = tpl.render(contents=contents)
    print("Render complete.")

    # Typeset PDF
    print("Typesetting PDF...")
    current_dir = os.path.abspath(os.path.dirname(__file__))
    base_filename = f"muddy_points_{contents.get('quiz_number')}"
    pdf_filename = Path(output_dir / f"{base_filename}.pdf")
    pdf = build_pdf(rendered_latex, texinputs=[current_dir, ""])
    pdf.save_to(str(pdf_filename))
    print("Typesetting complete.")

    # Export to Microsoft Word and LaTeX formats for further editing
    docx_filename =  Path(output_dir / f"{base_filename}.docx")
    latex_filename = Path(output_dir / f"{base_filename}.tex")
    make_texfile(rendered_latex, latex_filename)
    make_docx(latex_filename, docx_filename)

    # Create archive
    print("Creating archive...")
    zip_filename = Path(output_dir / f"{base_filename}.zip")
    make_archive(zip_filename, [pdf_filename, docx_filename, latex_filename], Path("figures"))
    print(f"Created archive: {zip_filename}")
