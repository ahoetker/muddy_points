import requests
import io
import pandas as pd
import os
from typing import Dict, List
from pathlib import Path


class Canvas():

    def __init__(self, install_url: str, api_version: str, access_token: str) -> None:
        """Create the Canvas API object.

        Args:
            install_url: Provided by your institution, e.g. "asu.instructure.edu".
            api_version: Version of Canvas API, almost certainly "v1".
            access_token: Generate at Canvas > Profile > Approved Integrations.

        """
        self.install_url = install_url
        self.api_version = api_version
        self.access_token = access_token
        self.api_base = f"https://{install_url}/api/{api_version}"

    def _get_with_token(self, url: str, params: Dict = None) -> requests.Response:
        """Make HTTP GET request using the generated access token.

        Args:
            url: The URL of a canvas API endpoint.

        Returns:
            The HTTP Response for this request.

        """
        payload = {"access_token": self.access_token}
        if params:
            payload.update(params)
        return requests.get(url, params=payload)

    def _post_with_token(self, url: str, data: Dict = None) -> requests.Response:
        """Make HTTP POST request using the generated access token.

        Args:
            url: The URL of a canvas API endpoint.

        Returns:
            The HTTP Response for this request.

        """
        payload = {"access_token": self.access_token}
        if data:
            payload.update(data)
        return requests.post(url, data=payload)

    def _get_course_id(self, course_name: str) -> str:
        """Get Canvas course ID corresponding to course name.

        Args:
            class_name: Partial or complete name of the course, e.g. "CHE 334"

        Returns:
            The course ID.

        """
        response = self._get_with_token(self.api_base + "/courses")
        course = list(filter(lambda x: course_name in x.get("name"), response.json()))
        assert len(course) == 1, f"Multiple {course_name} courses in Canvas"
        return course[0].get("id")

    def _get_muddy_points_id(self, course_id: str, number: int) -> str:
        """Get the quiz ID for a numbered Muddy Points survey.

        Args:
            course_id: The ID of the course to look in.
            number: Which Muddy Points survey to check, e.g. 1

        Returns:
            The quiz ID.

        """
        url = self.api_base + f"/courses/{course_id}/quizzes"
        quizzes = self._get_with_token(url).json()
        title = f"Muddy and Interesting Points #{number}"
        muddy_points = list(filter(lambda x: x.get("title") == title, quizzes))
        assert len(muddy_points) == 1, f"Multiple quizzes matching {title}"
        return muddy_points[0].get("id")

    def _post_fetch_quiz_report(self, course_id: str, quiz_id: str) -> requests.Response:
        url = self.api_base + f"/courses/{course_id}/quizzes/{quiz_id}/reports"
        return self._post_with_token(url, data={
            "quiz_report[report_type]": "student_analysis",
            "include": ["file", "progress"],
            })

    def _get_quiz_report(self, course_id: str, quiz_id: str) -> Dict:
        """Creates and returns a quiz report.

        """
        WAIT_SECONDS = 10
        NUM_ATTEMPTS = 3
        response = self._post_fetch_quiz_report(course_id, quiz_id)

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 409:
            num_attempts = NUM_ATTEMPTS - 1
            while (response.status_code == 409 and NUM_ATTEMPTS > 0):
                print(f"Report is already being generated: {response}")
                print(f"{NUM_ATTEMPTS} attempts remaining, waiting {WAIT_SECONDS}s.")
                response = self._post_fetch_quiz_report(course_id, quiz_id)
        else:
            print(f"Report could not be fetched: {response.text}")

        return response.json()

    def get_recipient_ids(self, recipient_names: List[str]) -> Dict:
        recipients = {}

        for name in recipient_names:
            url = self.api_base + f"/search/recipients?search={name.strip()}&type=user"
            response = self._get_with_token(url)
            if response.status_code == 200:
                person = response.json()[0]
                recipients[person.get("full_name")] = person.get("id")

        return recipients

    def upload_file(self, file_to_upload: Path, parent_folder: Path) -> bool:

        # Step 1
        url = self.api_base + "/users/self/files"

        name = file_to_upload.name
        fsize = os.path.getsize(str(file_to_upload))

        content_type = None
        if file_to_upload.suffix == ".png":
            content_type = "image/png"
        elif file_to_upload.suffix == ".zip":
            content_type = "application/zip"

        parent_folder_path = parent_folder

        response = self._post_with_token(url, data={
            "name": name,
            "size": fsize,
            "content_type": content_type,
            "parent_folder_path": parent_folder_path,
        })

        # Step 2
        print(response.status_code)
        print(response.text)
        if response.status_code != 200:
            return False

        response_data = response.json()
        upload_url = response_data.get("upload_url")
        upload_params = response_data.get("upload_params") or {}
        with file_to_upload.open("rb") as f:
            print("Upload params: ", upload_params)
            response = requests.post(upload_url, data=upload_params, files={name: f})

        # Step 3
        # Successful Creation
        print(response.status_code)
        print(response.text)
        if response.status_code == 201:
            return True

        # Need to confirm upload
        elif response.status_code == 301:
            print(response.text)
            return False

    def get_quiz_report_df(self, course_name: str, number: int) -> pd.DataFrame:
        course_id = self._get_course_id(course_name)
        quiz_id = self._get_muddy_points_id(course_id, number)
        report = self._get_quiz_report(course_id, quiz_id)

        download_url = report.get("file").get("url")
        response = self._get_with_token(download_url)
        content = response.content
        df = pd.read_csv(io.StringIO(content.decode('utf-8')))
        return df
