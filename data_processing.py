from Canvas import Canvas

import requests
import math
import re
import pytz
import pandas as pd
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple
from wordcloud import WordCloud
from datetime import datetime
from pathlib import Path


def plot_attendance_by_section(questions_df: pd.DataFrame, filename: Path) -> Dict:
    attendance_text = list(
        filter(lambda q: "registered for" in q, questions_df.columns.values)
    )[0]
    attendance_question = questions_df[attendance_text]
    plt.figure(figsize=(7.5, 3), dpi=300)
    plt.style.use("seaborn")
    attendance_question.value_counts().plot(kind="bar", y="Responses", rot=0)
    plt.ylabel("Responses")
    plt.savefig(str(filename), bbox_inches="tight")
    # plt.show()
    return {
        "title": "Muddy Points responses by section.",
        "filename": str(filename),
        "count": len(attendance_question),
    }


def split_by_instructor(
    questions_df: pd.DataFrame
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    attendance_text = list(
        filter(lambda q: "registered for" in q, questions_df.columns.values)
    )[0]
    varman_df = questions_df[questions_df[attendance_text] == "Varman"]
    holloway_df = questions_df[questions_df[attendance_text] == "Holloway"]
    return varman_df, holloway_df


def points_wordcloud(q, df, number, title, filename: Path):
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
    # plt.show()


def confusion_histogram(responses: List[int], filename: Path):
    plt.figure(figsize=(7.5, 3), dpi=300)
    plt.hist(responses, bins=5)
    plt.yticks(range(min(responses), math.ceil(max(responses)) + 1))
    plt.xticks([1, 2, 3, 4, 5])
    plt.ylabel("Responses")
    plt.xlabel("Confusion (5 is most confused)")
    plt.savefig(str(filename), bbox_inches="tight")
    # plt.show()


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
    plt.style.use("seaborn")
    plots_created = {}

    for q in df.columns.values.tolist()[0:-1:2]:
        number, title = re.match(r"(\d+): ([^\"]+)", q).groups()
        blacklist = ["\xa0"]
        for item in blacklist:
            title = title.replace(item, " ")
        filename = Path(figures_dir / f"{instructor}_{number}.jpg")

        if "confusing or interesting topics" in q:
            points_wordcloud(q, df, number, title, filename)
            plots_created["short_response"] = {"title": title, "filename": str(filename)}

        elif "rank your confusion" in q:
            responses = [int(r) for r in df[q] if pd.notna(r)]
            confusion_histogram(responses, filename)
            plots_created["ranked_confusion"] = {
                "title": title,
                "filename": str(filename),
                "count": len(responses),
                "mean_confusion": pd.Series(responses).mean(),
                "median_confusion": pd.Series(responses).median(),
            }

    return plots_created


def generate_report_contents(
    course_name: str, quiz_number: int, figures_dir: Path, recipients_file: Path = None
) -> Dict:
    """Create a JSON-serializable Dict of the report contents
    """

    # Retrieve the report data from Canvas
    with open("canvas_token.txt", "r") as f:
        token = f.read()
    print("Fetching quiz report from Canvas API...")
    c = Canvas("asu.instructure.com", "v1", token)
    report_df = c.get_quiz_report_df(course_name, quiz_number)
    print("Fetch complete.")

    # Create plots and add them to contents
    print("Generating report contents...")
    questions_df = report_df.filter(regex=r"\d+", axis=1)
    combined_figures = {}
    attendance_filename = Path(figures_dir / "attendance.png")
    combined_figures["attendance"] = plot_attendance_by_section(questions_df, attendance_filename)
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
