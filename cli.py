import click
import json
from jinja2 import FileSystemLoader
from latex.jinja2 import make_env
from latex import build_pdf
from pathlib import Path

import Canvas
import data_processing
import export

@click.group()
def cli():
    pass

@click.command()
@click.argument("course_name", type=click.STRING)
@click.argument("quiz_number", type=click.INT)
@click.option("-o", "--output_dir", type=Path, default=Path("output"), help="Output directory")
@click.option("-t", "--template_file", type=Path, default=Path("report_template.tex"), help="LaTeX/Jinja2 template.")
@click.option("-r", "--recipients_file", type=Path, default=Path("recipients.txt"), help="List of recipient names.")
@click.option("--token_file", type=Path, default=Path("canvas_token.txt"), help="Canvas API auth token.")
@click.option("-s", help="Use previously generated data.")
def generate(course_name, quiz_number, output_dir, template_file, recipients_file, token_file, s):
    """Driver/interface function for generating a report.
    """
    # Create directories if needed
    figures_dir = Path(output_dir / "figures")
    for d in [output_dir, figures_dir]:
        export.create_dir(d)

    # Use the stale dataset, or grab a fresh one
    if s is True:
        with open("contents.json", "r") as f:
            contents = json.load(f)
    else:
        contents = data_processing.generate_report_contents(course_name, quiz_number, figures_dir, recipients_file)
        with open("contents.json", "w+") as f:
            json.dump(contents, f)

    # Render LaTeX template
    print("Rendering LaTeX Template...")
    env = make_env(loader=FileSystemLoader(str(template_file.parent)))
    tpl = env.get_template(str(template_file.name))
    rendered_latex = tpl.render(contents=contents)
    print("Render complete.")

    # Typeset PDF
    print("Typesetting PDF...")
    base_filename = f"muddy_points_{contents.get('quiz_number')}"
    pdf_filename = Path(output_dir / f"{base_filename}.pdf")
    pdf = build_pdf(rendered_latex, texinputs=[str(Path.cwd()), ""])
    pdf.save_to(str(pdf_filename))
    print("Typesetting complete.")

    # Export to Microsoft Word and LaTeX formats for further editing
    docx_filename =  Path(output_dir / f"{base_filename}.docx")
    latex_filename = Path(output_dir / f"{base_filename}.tex")
    export.make_texfile(rendered_latex, latex_filename)
    export.make_docx(latex_filename, docx_filename)

    # Create archive
    print("Creating archive...")
    zip_filename = Path(output_dir / f"{base_filename}.zip")
    export.make_archive(zip_filename, [pdf_filename, docx_filename, latex_filename], figures_dir)
    print(f"Created archive: {zip_filename}")


cli.add_command(generate)

if __name__ == "__main__":
    cli()