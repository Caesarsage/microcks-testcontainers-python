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

"""MicrocksContainer - Main testcontainer for Microcks API mocking and testing."""

from __future__ import annotations

import time
from datetime import date
from typing import Self
from urllib.parse import quote

from testcontainers.core.container import DockerContainer
from testcontainers.core.wait_strategies import LogMessageWaitStrategy

from . import _api_client as api
from .models import (
    RemoteArtifact,
    RequestResponsePair,
    Secret,
    TestRequest,
    TestResult,
    UnidirectionalEvent,
)

class MicrocksContainer(DockerContainer):
    """Testcontainer for Microcks - API mocking and testing.

    Provides mock endpoints for REST, SOAP, GraphQL, and gRPC services,
    as well as contract testing capabilities.

    Usage::

        with MicrocksContainer().with_main_artifacts(["my-api.yaml"]) as mc:
            endpoint = mc.get_rest_mock_endpoint("My API", "1.0")
    """

    MICROCKS_HTTP_PORT = 8080
    MICROCKS_GRPC_PORT = 9090
    DEFAULT_IMAGE = "quay.io/microcks/microcks-uber:1.13.2"

    def __init__(self, image: str = DEFAULT_IMAGE, **kwargs) -> None:
        super().__init__(image, **kwargs)
        self.with_exposed_ports(self.MICROCKS_HTTP_PORT, self.MICROCKS_GRPC_PORT)
        self._snapshots: list[str] = []
        self._main_artifacts: list[str] = []
        self._secondary_artifacts: list[str] = []
        self._main_remote_artifacts: list[RemoteArtifact] = []
        self._secondary_remote_artifacts: list[RemoteArtifact] = []
        self._secrets: list[Secret] = []

    # --- Configuration methods (all return self for chaining) ---

    def with_debug_log_level(self) -> Self:
        """Enable DEBUG level logging on the Microcks container."""
        self.with_env("LOGGING_LEVEL_IO_GITHUB_MICROCKS", "DEBUG")
        return self

    def with_main_artifacts(self, artifacts: list[str]) -> Self:
        """Provide paths to artifacts that will be imported as primary ones."""
        self._main_artifacts.extend(artifacts)
        return self

    def with_secondary_artifacts(self, artifacts: list[str]) -> Self:
        """Provide paths to artifacts that will be imported as secondary ones."""
        self._secondary_artifacts.extend(artifacts)
        return self

    def with_snapshots(self, snapshots: list[str]) -> Self:
        """Provide paths to repository snapshots that will be imported."""
        self._snapshots.extend(snapshots)
        return self

    def with_main_remote_artifacts(self, remote_artifacts: list[RemoteArtifact]) -> Self:
        """Provide URLs of remote artifacts to import as primary ones."""
        self._main_remote_artifacts.extend(remote_artifacts)
        return self

    def with_secondary_remote_artifacts(self, remote_artifacts: list[RemoteArtifact]) -> Self:
        """Provide URLs of remote artifacts to import as secondary ones."""
        self._secondary_remote_artifacts.extend(remote_artifacts)
        return self

    def with_secret(self, secret: Secret) -> Self:
        """Provide a secret to be imported after startup."""
        self._secrets.append(secret)
        return self

    # --- Lifecycle ---

    def start(self) -> Self:
        """Start the container and load configured artifacts."""
        self.waiting_for(LogMessageWaitStrategy("Started MicrocksApplication"))
        super().start()

        # Load in prescribed order: snapshots -> secrets -> remote -> local
        for snapshot in self._snapshots:
            self.import_snapshot(snapshot)
        for secret in self._secrets:
            self.create_secret(secret)
        for artifact in self._main_remote_artifacts:
            url, secret_name = self._extract_artifact_info(artifact)
            self.download_as_main_remote_artifact(url, secret_name)
        for artifact in self._secondary_remote_artifacts:
            url, secret_name = self._extract_artifact_info(artifact)
            self.download_as_secondary_remote_artifact(url, secret_name)
        for artifact in self._main_artifacts:
            self.import_as_main_artifact(artifact)
        for artifact in self._secondary_artifacts:
            self.import_as_secondary_artifact(artifact)

        return self

    # --- Endpoint properties and methods ---

    @property
    def http_endpoint(self) -> str:
        """The HTTP endpoint for connecting to the Microcks container API."""
        host = self.get_container_host_ip()
        port = self.get_exposed_port(self.MICROCKS_HTTP_PORT)
        return f"http://{host}:{port}"

    @property
    def grpc_mock_endpoint(self) -> str:
        """The gRPC mock endpoint."""
        host = self.get_container_host_ip()
        port = self.get_exposed_port(self.MICROCKS_GRPC_PORT)
        return f"grpc://{host}:{port}"

    def get_rest_mock_endpoint(self, service: str, version: str) -> str:
        """Get the exposed mock endpoint for a REST API."""
        return f"{self.http_endpoint}/rest/{service}/{version}"

    def get_rest_mock_endpoint_path(self, service: str, version: str) -> str:
        """Get the exposed mock endpoint path for a REST API."""
        return f"/rest/{service}/{version}"

    def get_validating_rest_mock_endpoint(self, service: str, version: str) -> str:
        """Get the exposed mock endpoint with request validation for a REST API."""
        return f"{self.http_endpoint}/rest-valid/{service}/{version}"

    def get_validating_rest_mock_endpoint_path(self, service: str, version: str) -> str:
        """Get the exposed mock endpoint path with request validation for a REST API."""
        return f"/rest-valid/{service}/{version}"

    def get_soap_mock_endpoint(self, service: str, version: str) -> str:
        """Get the exposed mock endpoint for a SOAP service."""
        return f"{self.http_endpoint}/soap/{service}/{version}"

    def get_soap_mock_endpoint_path(self, service: str, version: str) -> str:
        """Get the exposed mock endpoint path for a SOAP service."""
        return f"/soap/{service}/{version}"

    def get_validating_soap_mock_endpoint(self, service: str, version: str) -> str:
        """Get the exposed mock endpoint with request validation for a SOAP service."""
        return f"{self.http_endpoint}/soap/{service}/{version}?validate=true"

    def get_validating_soap_mock_endpoint_path(self, service: str, version: str) -> str:
        """Get the exposed mock endpoint path with request validation for a SOAP service."""
        return f"/soap/{service}/{version}?validate=true"

    def get_graphql_mock_endpoint(self, service: str, version: str) -> str:
        """Get the exposed mock endpoint for a GraphQL API."""
        return f"{self.http_endpoint}/graphql/{service}/{version}"

    def get_graphql_mock_endpoint_path(self, service: str, version: str) -> str:
        """Get the exposed mock endpoint path for a GraphQL API."""
        return f"/graphql/{service}/{version}"

    # --- Post-startup artifact management ---

    def import_as_main_artifact(self, artifact_path: str) -> None:
        """Import an artifact as a primary one within the Microcks container."""
        api.upload_artifact(self.http_endpoint, artifact_path, main_artifact=True)

    def import_as_secondary_artifact(self, artifact_path: str) -> None:
        """Import an artifact as a secondary one within the Microcks container."""
        api.upload_artifact(self.http_endpoint, artifact_path, main_artifact=False)

    def import_snapshot(self, snapshot_path: str) -> None:
        """Import a repository snapshot within the Microcks container."""
        api.import_snapshot(self.http_endpoint, snapshot_path)

    def download_as_main_remote_artifact(self, url: str, secret_name: str | None = None) -> None:
        """Download a remote artifact as a primary one."""
        api.download_remote_artifact(self.http_endpoint, url, main_artifact=True, secret_name=secret_name)

    def download_as_secondary_remote_artifact(self, url: str, secret_name: str | None = None) -> None:
        """Download a remote artifact as a secondary one."""
        api.download_remote_artifact(self.http_endpoint, url, main_artifact=False, secret_name=secret_name)

    def create_secret(self, secret: Secret) -> None:
        """Create a secret to access remote Git repository, test endpoint or broker."""
        api.create_secret(self.http_endpoint, secret)

    # --- Contract testing ---

    def test_endpoint(self, test_request: TestRequest) -> TestResult:
        """Launch a conformance test on an endpoint and poll until complete.

        Args:
            test_request: The test specifications (service, endpoint, runner, timeout).

        Returns:
            The final TestResult with success/failure details.
        """
        response_json = api.launch_test(self.http_endpoint, test_request)
        test_result_id = response_json["id"]

        deadline = time.time() + (test_request.timeout / 1000) + 1.0
        test_result = api.get_test_result(self.http_endpoint, test_result_id)

        while test_result.in_progress and time.time() < deadline:
            time.sleep(0.25)
            test_result = api.get_test_result(self.http_endpoint, test_result_id)

        return test_result

    def get_messages_for_test_case(
        self, test_result: TestResult, operation_name: str
    ) -> list[RequestResponsePair]:
        """Retrieve request/response pairs exchanged during a test case."""
        test_case_id = self._build_test_case_id(test_result, operation_name)
        return api.get_messages_for_test_case(self.http_endpoint, test_result.id, test_case_id)

    def get_event_messages_for_test_case(
        self, test_result: TestResult, operation_name: str
    ) -> list[UnidirectionalEvent]:
        """Retrieve event messages received during an async test case."""
        test_case_id = self._build_test_case_id(test_result, operation_name)
        return api.get_event_messages_for_test_case(self.http_endpoint, test_result.id, test_case_id)

    # --- Verification ---

    def verify(self, service_name: str, service_version: str, invocation_date: date | None = None) -> bool:
        """Check if a service has been invoked at least once."""
        time.sleep(0.1)  # Avoid race condition with async metrics processing
        day_str = self._format_date(invocation_date) if invocation_date else None
        stats = api.get_invocation_stats(self.http_endpoint, service_name, service_version, day_str)
        return stats is not None and stats.daily_count > 0

    def get_service_invocations_count(
        self, service_name: str, service_version: str, invocation_date: date | None = None
    ) -> int:
        """Get the total invocation count for a service."""
        time.sleep(0.1)  # Avoid race condition with async metrics processing
        day_str = self._format_date(invocation_date) if invocation_date else None
        stats = api.get_invocation_stats(self.http_endpoint, service_name, service_version, day_str)
        return stats.daily_count if stats else 0

    # --- Private helpers ---

    @staticmethod
    def _extract_artifact_info(artifact: RemoteArtifact) -> tuple[str, str | None]:
        """Extract URL and optional secret name from a RemoteArtifact."""
        if isinstance(artifact, str):
            return artifact, None
        return artifact.url, artifact.secret_name

    @staticmethod
    def _build_test_case_id(test_result: TestResult, operation_name: str) -> str:
        """Build test case ID: {resultId}-{testNumber}-{encodedOperation}."""
        encoded = quote(operation_name.replace("/", "!"))
        return f"{test_result.id}-{test_result.test_number}-{encoded}"

    @staticmethod
    def _format_date(d: date) -> str:
        """Format a date as YYYYMMDD for the Microcks API."""
        return d.strftime("%Y%m%d")
