import requests
import re
import pytz
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import seaborn as sns
from typing import Dict, Tuple
from wordcloud import WordCloud
from datetime import datetime
from pathlib import Path

from Canvas import Canvas

plt.style.use("seaborn")
plt.rcParams["font.family"] = "STIXGeneral"
plt.rcParams["mathtext.fontset"] = "stix"


def plot_attendance_by_section(questions_df: pd.DataFrame, filename: Path) -> Dict:
    attendance_text = list(
        filter(lambda q: "registered for" in q, questions_df.columns.values)
    )[0]
    attendance_question = questions_df[attendance_text]

    plt.figure(figsize=(7.5, 3), dpi=300)
    attendance_question.value_counts().plot(kind="bar", y="Responses", rot=0)
    plt.ylabel("Responses")
    plt.savefig(str(filename), bbox_inches="tight")

    attendance = {
        "title": "Muddy Points responses by section.",
        "filename": str(filename),
        "count": len(attendance_question),
    }

    if len(attendance_question.value_counts()) > 2:
        attendance["notes"] = """At least one student selected both instructors. This may be an error, 
        or it may indicate that the student attended a lecture in each section this week.
        """

    return attendance


def split_by_instructor(
    questions_df: pd.DataFrame
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    attendance_text = list(
        filter(lambda q: "registered for" in q, questions_df.columns.values)
    )[0]
    varman_df = questions_df[questions_df[attendance_text] == "Varman"]
    holloway_df = questions_df[questions_df[attendance_text] == "Holloway"]
    return varman_df, holloway_df


def combined_confusion_barplot(report_df: pd.DataFrame, filename: Path) -> Dict:
    df = report_df.filter(regex=r"(registered for)|(rank your)").dropna()
    df.columns = ["instructor", "confusion"]
    df = df[df["confusion"].apply(lambda x: str(x).isdigit())]
    df["confusion"] = pd.to_numeric(df["confusion"])
    df = df[df["instructor"].apply(lambda s: "," not in s)]

    v_df = df[df["instructor"] == "Varman"]
    value_counts = (v_df["confusion"].value_counts().get(i) for i in range(1, 6))
    v_counts = [x if x is not None else 0 for x in value_counts]

    h_df = df[df["instructor"] == "Holloway"]
    value_counts = (h_df["confusion"].value_counts().get(i) for i in range(1, 6))
    h_counts = [x if x is not None else 0 for x in value_counts]

    fig = plt.figure(figsize=(7.5, 3), dpi=300)
    ax = fig.add_subplot(1, 1, 1)
    ax.bar([1, 2, 3, 4, 5], v_counts, width=0.8, label="Varman")
    ax.bar([1, 2, 3, 4, 5], h_counts, bottom=v_counts, width=0.8, label="Holloway")
    ax.set_xlabel("Confusion")
    ax.set_ylabel("Responses")
    plt.legend()
    plt.savefig(str(filename), bbox_inches="tight")

    return {
        "title": "Stacked Bar Plot of Self-Assessed Confusion",
        "filename": str(filename),
    }


def combined_confusion_kdeplot(report_df: pd.DataFrame, filename: Path) -> Dict:
    varman_df, holloway_df = split_by_instructor(report_df)
    varman_df = varman_df.filter(regex="rank your").dropna()
    varman_df.columns = ["confusion"]
    varman_df = varman_df[varman_df["confusion"].apply(lambda x: str(x).isdigit())]
    holloway_df = holloway_df.filter(regex="rank your").dropna()
    holloway_df.columns = ["confusion"]
    holloway_df = holloway_df[holloway_df["confusion"].apply(lambda x: str(x).isdigit())]

    plt.figure(figsize=(7.5, 3), dpi=300)
    sns.kdeplot(varman_df["confusion"], shade=True, label="Varman")
    sns.kdeplot(holloway_df["confusion"], shade=True, label="Holloway")
    plt.savefig(str(filename), bbox_inches="tight")

    return {
        "title": "Kernel Density Estimate Plot of Self-Assessed Confusion",
        "filename": str(filename),
    }


def points_wordcloud(q, df, filename: Path):
    try:
        text = " ".join([str(response) for response in df[q]])
        wc = WordCloud(background_color="white").generate_from_text(text)
    except ValueError as e:
        print(f"Using the constitution, not enough responses: {e}")
        text = requests.get("https://www.usconstitution.net/const.txt").text
        wc = WordCloud(background_color="white").generate_from_text(text)

    plt.figure(figsize=(7.5, 3), dpi=300)
    plt.axis("off")
    plt.imshow(wc, interpolation="bilinear")
    plt.savefig(str(filename), bbox_inches="tight")


def confusion_histogram(report_df: pd.DataFrame, filename: Path) -> pd.Series:
    df = report_df.filter(regex=r"rank your").dropna()
    df.columns = ["confusion"]
    df = df[df["confusion"].apply(lambda x: str(x).isdigit())]
    df["confusion"] = pd.to_numeric(df["confusion"])
    value_counts = (df["confusion"].value_counts().get(i) for i in range(1, 6))
    counts = [x if x is not None else 0 for x in value_counts]

    fig = plt.figure(figsize=(7.5, 3), dpi=300)
    ax = fig.add_subplot(1, 1, 1)
    ax.bar([1, 2, 3, 4, 5], counts)
    ax.set_xlabel("Confusion (5 is most confused)")
    ax.set_ylabel("Responses")
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    plt.savefig(str(filename), bbox_inches="tight")

    return df["confusion"]


def most_confused_responses(df: pd.DataFrame) -> Dict:
    short_response_header = [
        h for h in df.columns.values if "confusing or interesting topics" in h
    ][0]

    confusion_header = [h for h in df.columns.values if "rank your confusion" in h][0]

    sorted_df = df.sort_values(by=confusion_header, ascending=False)
    number_of_responses = min(3, len(sorted_df))
    responses = [
        {row[short_response_header]: row[confusion_header]}
        for index, row in sorted_df[0:number_of_responses].iterrows()
    ]
    return {"most_confused": responses}


def process_instructor_results(df: pd.DataFrame, instructor: str, figures_dir: Path) -> Dict:
    if len(df) == 0:
        print("Could not plot, not enough entries.")
        return {}
    plots_created = {}

    for q in df.columns.values.tolist()[0:-1:2]:
        number, title = re.match(r"(\d+): ([^\"]+)", q).groups()
        blacklist = ["\xa0"]
        for item in blacklist:
            title = title.replace(item, " ")
        filename = Path(figures_dir / f"{instructor}_{number}.pdf")

        if "confusing or interesting topics" in q:
            points_wordcloud(q, df, filename)
            plots_created["short_response"] = {"title": title, "filename": str(filename)}

        elif "rank your confusion" in q:
            responses = confusion_histogram(df, filename)

            plots_created["ranked_confusion"] = {
                "title": title,
                "filename": str(filename),
                "count": len(responses),
                "mean_confusion": responses.mean(),
                "median_confusion": responses.median(),
            }

    return plots_created


def generate_report_contents(
        c: Canvas, report_df: pd.DataFrame, quiz_number: int, figures_dir: Path, recipients_file: Path = None
) -> Dict:
    """Create a JSON-serializable Dict of the report contents
    """
    # Create plots and add them to contents
    print("Generating report contents...")
    questions_df = report_df.filter(regex=r"\d+", axis=1)
    combined_figures = {}
    attendance_filename = Path(figures_dir / "attendance.pdf")
    combined_figures["attendance"] = plot_attendance_by_section(questions_df, attendance_filename)
    combined_confusion_filename = Path(figures_dir / "combined_kdeplot.pdf")
    combined_figures["kdeplot"] = combined_confusion_kdeplot(report_df, combined_confusion_filename)
    combined_barplot_filename = Path(figures_dir / "combined_barplot.pdf")
    combined_figures["stacked"] = combined_confusion_barplot(report_df, combined_barplot_filename)
    varman_df, holloway_df = split_by_instructor(questions_df)
    varman_data = process_instructor_results(varman_df, "Varman", figures_dir)
    holloway_data = process_instructor_results(holloway_df, "Holloway", figures_dir)

    # Get the most confused questions and add them to the contents
    varman_questions = most_confused_responses(varman_df)
    varman_data.update(varman_questions)
    holloway_questions = most_confused_responses(holloway_df)
    holloway_data.update(holloway_questions)

    # Generate a timestamp
    d = datetime.now()
    timezone = pytz.timezone("America/Phoenix")
    d_aware = timezone.localize(d)
    timestamp = d_aware.strftime("%Y-%m-%d %I:%M %p")

    # Create the contents data structure
    report_contents = {}
    report_contents["author"] = "Andrew Hoetker"
    report_contents["timestamp"] = timestamp
    report_contents["quiz_number"] = quiz_number
    report_contents["combined"] = combined_figures
    report_contents["instructors"] = {"Varman": varman_data, "Holloway": holloway_data}

    # Get recipient IDs
    if recipients_file is not None:
        with recipients_file.open("r") as f:
            names = [name.strip() for name in f.readlines()]
            recipients = c.get_recipient_ids(names)
            report_contents["recipients"] = recipients

    print("Generation complete.")
    return report_contents
