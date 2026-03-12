# Copyright The Microcks Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Internal HTTP client for communicating with the Microcks REST API."""

from __future__ import annotations

import os
from urllib.parse import quote

import requests

from .models import (
    DailyInvocationStatistic,
    RequestResponsePair,
    Secret,
    TestRequest,
    TestResult,
    UnidirectionalEvent,
)
from .exceptions import MicrocksException

def upload_artifact(endpoint: str, artifact_path: str, main_artifact: bool) -> None:
    """Upload a local artifact file to Microcks via multipart POST."""
    url = f"{endpoint}/api/artifact/upload"
    if not main_artifact:
        url += "?mainArtifact=false"

    if not os.path.isfile(artifact_path):
        raise FileNotFoundError(f"Artifact {artifact_path} does not exist or can't be read")

    filename = os.path.basename(artifact_path)
    with open(artifact_path, "rb") as f:
        files = {"file": (filename, f, "application/octet-stream")}
        response = requests.post(url, files=files)

    if response.status_code != 201:
        raise MicrocksException(f"Artifact was not correctly imported: {response.text}")


def download_remote_artifact(
    endpoint: str, url: str, main_artifact: bool, secret_name: str | None = None
) -> None:
    """Download a remote artifact into Microcks via form-encoded POST."""
    download_url = f"{endpoint}/api/artifact/download"
    data: dict[str, str] = {"mainArtifact": str(main_artifact).lower(), "url": url}
    if secret_name:
        data["secretName"] = secret_name

    response = requests.post(
        download_url,
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    if response.status_code != 201:
        raise MicrocksException(f"Artifact was not correctly downloaded: {response.text}")


def import_snapshot(endpoint: str, snapshot_path: str) -> None:
    """Import a repository snapshot into Microcks via multipart POST."""
    if not os.path.isfile(snapshot_path):
        raise FileNotFoundError(f"Snapshot {snapshot_path} does not exist or can't be read")

    filename = os.path.basename(snapshot_path)
    with open(snapshot_path, "rb") as f:
        files = {"file": (filename, f, "application/json")}
        response = requests.post(f"{endpoint}/api/import", files=files)

    if response.status_code != 201:
        raise MicrocksException(f"Snapshot was not correctly imported: {response.text}")


def create_secret(endpoint: str, secret: Secret) -> None:
    """Create a secret in Microcks via JSON POST."""
    response = requests.post(
        f"{endpoint}/api/secrets",
        json=secret.to_dict(),
        headers={"Accept": "application/json", "Content-Type": "application/json"},
    )

    if response.status_code != 201:
        raise MicrocksException(f"Secret has not been correctly created: {response.text}")


def launch_test(endpoint: str, test_request: TestRequest) -> dict:
    """Launch a conformance test on Microcks. Returns raw JSON dict with test result ID."""
    response = requests.post(
        f"{endpoint}/api/tests",
        json=test_request.to_dict(),
        headers={"Content-Type": "application/json"},
    )

    if response.status_code != 201:
        raise MicrocksException("Couldn't launch new test on Microcks. Check container logs.")

    return response.json()


def get_test_result(endpoint: str, test_result_id: str) -> TestResult:
    """Fetch a test result by ID. Returns parsed TestResult."""
    response = requests.get(f"{endpoint}/api/tests/{test_result_id}")

    if not response.ok:
        raise MicrocksException(f"Error fetching TestResult, status: {response.status_code}")

    return TestResult.from_dict(response.json())


def get_messages_for_test_case(
    endpoint: str, test_result_id: str, test_case_id: str
) -> list[RequestResponsePair]:
    """Fetch request/response pairs for a specific test case."""
    response = requests.get(
        f"{endpoint}/api/tests/{test_result_id}/messages/{test_case_id}",
        headers={"Accept": "application/json"},
    )

    if response.status_code != 200:
        raise MicrocksException("Couldn't retrieve messages. Check container logs.")

    return [RequestResponsePair.from_dict(item) for item in response.json()]


def get_event_messages_for_test_case(
    endpoint: str, test_result_id: str, test_case_id: str
) -> list[UnidirectionalEvent]:
    """Fetch event messages for a specific async test case."""
    response = requests.get(
        f"{endpoint}/api/tests/{test_result_id}/events/{test_case_id}",
        headers={"Accept": "application/json"},
    )

    if response.status_code != 200:
        raise MicrocksException("Couldn't retrieve event messages. Check container logs.")

    return [UnidirectionalEvent.from_dict(item) for item in response.json()]


def get_invocation_stats(
    endpoint: str, service_name: str, service_version: str, day: str | None = None
) -> DailyInvocationStatistic | None:
    """Fetch daily invocation statistics for a service."""
    url = f"{endpoint}/api/metrics/invocations/{quote(service_name)}/{quote(service_version)}"
    if day:
        url += f"?day={day}"

    response = requests.get(url, headers={"Accept": "application/json"})

    if response.status_code == 200:
        return DailyInvocationStatistic.from_dict(response.json())

    return None
