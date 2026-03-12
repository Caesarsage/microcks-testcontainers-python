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

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class TestRunnerType(str, Enum):
    """Supported test runner types for contract testing."""

    HTTP = "HTTP"
    SOAP_HTTP = "SOAP_HTTP"
    SOAP_UI = "SOAP_UI"
    POSTMAN = "POSTMAN"
    OPEN_API_SCHEMA = "OPEN_API_SCHEMA"
    ASYNC_API_SCHEMA = "ASYNC_API_SCHEMA"
    GRPC_PROTOBUF = "GRPC_PROTOBUF"
    GRAPHQL_SCHEMA = "GRAPHQL_SCHEMA"


class OAuth2GrantType(str, Enum):
    """OAuth2 grant types supported by Microcks."""

    PASSWORD = "PASSWORD"
    CLIENT_CREDENTIALS = "CLIENT_CREDENTIALS"
    REFRESH_TOKEN = "REFRESH_TOKEN"


@dataclass
class Secret:
    """A secret to access remote Git repository, test endpoint or broker."""

    name: str
    description: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    token: Optional[str] = None
    token_header: Optional[str] = None
    ca_cert_pem: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict with camelCase keys for Microcks API."""
        result: dict[str, Any] = {"name": self.name}
        if self.description is not None:
            result["description"] = self.description
        if self.username is not None:
            result["username"] = self.username
        if self.password is not None:
            result["password"] = self.password
        if self.token is not None:
            result["token"] = self.token
        if self.token_header is not None:
            result["tokenHeader"] = self.token_header
        if self.ca_cert_pem is not None:
            result["caCertPem"] = self.ca_cert_pem
        return result


@dataclass
class OAuth2ClientContext:
    """OAuth2 client context for authenticated contract testing."""

    client_id: str
    token_uri: str
    grant_type: OAuth2GrantType
    client_secret: Optional[str] = None
    scopes: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    refresh_token: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict with camelCase keys for Microcks API."""
        result: dict[str, Any] = {
            "clientId": self.client_id,
            "tokenUri": self.token_uri,
            "grantType": self.grant_type.value,
        }
        if self.client_secret is not None:
            result["clientSecret"] = self.client_secret
        if self.scopes is not None:
            result["scopes"] = self.scopes
        if self.username is not None:
            result["username"] = self.username
        if self.password is not None:
            result["password"] = self.password
        if self.refresh_token is not None:
            result["refreshToken"] = self.refresh_token
        return result


@dataclass
class TestRequest:
    """Specifications for a conformance test to launch on Microcks."""

    service_id: str
    test_endpoint: str
    runner_type: TestRunnerType
    timeout: int
    secret_name: Optional[str] = None
    filtered_operations: Optional[list[str]] = None
    operations_headers: Optional[dict[str, list[dict[str, Any]]]] = None
    oauth2_context: Optional[OAuth2ClientContext] = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict with camelCase keys for Microcks API."""
        result: dict[str, Any] = {
            "serviceId": self.service_id,
            "testEndpoint": self.test_endpoint,
            "runnerType": self.runner_type.value,
            "timeout": self.timeout,
        }
        if self.secret_name is not None:
            result["secretName"] = self.secret_name
        if self.filtered_operations is not None:
            result["filteredOperations"] = self.filtered_operations
        if self.operations_headers is not None:
            result["operationsHeaders"] = self.operations_headers
        if self.oauth2_context is not None:
            result["oAuth2Context"] = self.oauth2_context.to_dict()
        return result


@dataclass
class Header:
    """An HTTP header with name and values."""

    name: str
    values: list[str] = field(default_factory=list)


@dataclass
class Parameter:
    """A query parameter with name and value."""

    name: str
    value: str


@dataclass
class Request:
    """A request message from a test execution."""

    name: str = ""
    content: str = ""
    operation_id: str = ""
    test_case_id: str = ""
    source_artifact: str = ""
    headers: list[Header] = field(default_factory=list)
    id: str = ""
    response_id: str = ""
    query_parameters: list[Parameter] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Request:
        """Create from a JSON dict with camelCase keys."""
        return cls(
            name=data.get("name", ""),
            content=data.get("content", ""),
            operation_id=data.get("operationId", ""),
            test_case_id=data.get("testCaseId", ""),
            source_artifact=data.get("sourceArtifact", ""),
            headers=[Header(name=h["name"], values=h.get("values", [])) for h in data.get("headers", [])],
            id=data.get("id", ""),
            response_id=data.get("responseId", ""),
            query_parameters=[Parameter(name=p["name"], value=p["value"]) for p in data.get("queryParameters", [])],
        )


@dataclass
class Response:
    """A response message from a test execution."""

    name: str = ""
    content: str = ""
    operation_id: str = ""
    test_case_id: str = ""
    source_artifact: str = ""
    headers: list[Header] = field(default_factory=list)
    id: str = ""
    status: str = ""
    media_type: str = ""
    dispatch_criteria: str = ""
    is_fault: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Response:
        """Create from a JSON dict with camelCase keys."""
        return cls(
            name=data.get("name", ""),
            content=data.get("content", ""),
            operation_id=data.get("operationId", ""),
            test_case_id=data.get("testCaseId", ""),
            source_artifact=data.get("sourceArtifact", ""),
            headers=[Header(name=h["name"], values=h.get("values", [])) for h in data.get("headers", [])],
            id=data.get("id", ""),
            status=data.get("status", ""),
            media_type=data.get("mediaType", ""),
            dispatch_criteria=data.get("dispatchCriteria", ""),
            is_fault=data.get("isFault", False),
        )


@dataclass
class EventMessage:
    """An event message from an async test execution."""

    name: str = ""
    content: str = ""
    operation_id: str = ""
    test_case_id: str = ""
    source_artifact: str = ""
    headers: list[Header] = field(default_factory=list)
    id: str = ""
    media_type: str = ""
    dispatch_criteria: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EventMessage:
        """Create from a JSON dict with camelCase keys."""
        return cls(
            name=data.get("name", ""),
            content=data.get("content", ""),
            operation_id=data.get("operationId", ""),
            test_case_id=data.get("testCaseId", ""),
            source_artifact=data.get("sourceArtifact", ""),
            headers=[Header(name=h["name"], values=h.get("values", [])) for h in data.get("headers", [])],
            id=data.get("id", ""),
            media_type=data.get("mediaType", ""),
            dispatch_criteria=data.get("dispatchCriteria", ""),
        )


@dataclass
class RequestResponsePair:
    """A request/response pair from a test execution."""

    request: Request
    response: Response

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RequestResponsePair:
        """Create from a JSON dict."""
        return cls(
            request=Request.from_dict(data.get("request", {})),
            response=Response.from_dict(data.get("response", {})),
        )


@dataclass
class UnidirectionalEvent:
    """A unidirectional event from an async test execution."""

    event_message: EventMessage

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> UnidirectionalEvent:
        """Create from a JSON dict."""
        return cls(event_message=EventMessage.from_dict(data.get("eventMessage", {})))


@dataclass
class TestStepResult:
    """Result of an individual test step within a test case."""

    success: bool = False
    elapsed_time: int = 0
    request_name: str = ""
    event_message_name: str = ""
    message: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TestStepResult:
        """Create from a JSON dict with camelCase keys."""
        return cls(
            success=data.get("success", False),
            elapsed_time=data.get("elapsedTime", 0),
            request_name=data.get("requestName", ""),
            event_message_name=data.get("eventMessageName", ""),
            message=data.get("message", ""),
        )


@dataclass
class TestCaseResult:
    """Result of a test case (one operation) within a test."""

    success: bool = False
    elapsed_time: int = 0
    operation_name: str = ""
    test_step_results: list[TestStepResult] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TestCaseResult:
        """Create from a JSON dict with camelCase keys."""
        return cls(
            success=data.get("success", False),
            elapsed_time=data.get("elapsedTime", 0),
            operation_name=data.get("operationName", ""),
            test_step_results=[TestStepResult.from_dict(s) for s in data.get("testStepResults", [])],
        )


@dataclass
class SecretRef:
    """Reference to a secret used in a test."""

    secret_id: str = ""
    name: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SecretRef:
        """Create from a JSON dict with camelCase keys."""
        return cls(secret_id=data.get("secretId", ""), name=data.get("name", ""))


@dataclass
class OAuth2AuthorizedClient:
    """OAuth2 authorized client info from a test result."""

    grant_type: OAuth2GrantType = OAuth2GrantType.CLIENT_CREDENTIALS
    principal_name: str = ""
    token_uri: str = ""
    scopes: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> OAuth2AuthorizedClient:
        """Create from a JSON dict with camelCase keys."""
        return cls(
            grant_type=OAuth2GrantType(data.get("grantType", "CLIENT_CREDENTIALS")),
            principal_name=data.get("principalName", ""),
            token_uri=data.get("tokenUri", ""),
            scopes=data.get("scopes"),
        )


@dataclass
class TestResult:
    """Complete result of a conformance test execution."""

    id: str = ""
    version: int = 0
    test_number: int = 0
    test_date: int = 0
    tested_endpoint: str = ""
    service_id: str = ""
    timeout: int = 0
    elapsed_time: int = 0
    success: bool = False
    in_progress: bool = False
    runner_type: TestRunnerType = TestRunnerType.HTTP
    test_case_results: list[TestCaseResult] = field(default_factory=list)
    operation_headers: Optional[dict[str, Any]] = None
    secret_ref: Optional[SecretRef] = None
    authorized_client: Optional[OAuth2AuthorizedClient] = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TestResult:
        """Create from a JSON dict with camelCase keys."""
        secret_ref = None
        if data.get("secretRef"):
            secret_ref = SecretRef.from_dict(data["secretRef"])
        authorized_client = None
        if data.get("authorizedClient"):
            authorized_client = OAuth2AuthorizedClient.from_dict(data["authorizedClient"])
        return cls(
            id=data.get("id", ""),
            version=data.get("version", 0),
            test_number=data.get("testNumber", 0),
            test_date=data.get("testDate", 0),
            tested_endpoint=data.get("testedEndpoint", ""),
            service_id=data.get("serviceId", ""),
            timeout=data.get("timeout", 0),
            elapsed_time=data.get("elapsedTime", 0),
            success=data.get("success", False),
            in_progress=data.get("inProgress", False),
            runner_type=TestRunnerType(data.get("runnerType", "HTTP")),
            test_case_results=[TestCaseResult.from_dict(tc) for tc in data.get("testCaseResults", [])],
            operation_headers=data.get("operationHeaders"),
            secret_ref=secret_ref,
            authorized_client=authorized_client,
        )


@dataclass
class DailyInvocationStatistic:
    """Daily invocation statistics for a service."""

    id: str = ""
    day: str = ""
    service_name: str = ""
    service_version: str = ""
    daily_count: int = 0
    hourly_count: Optional[dict[str, int]] = None
    minute_count: Optional[dict[str, int]] = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DailyInvocationStatistic:
        """Create from a JSON dict with camelCase keys."""
        return cls(
            id=data.get("id", ""),
            day=data.get("day", ""),
            service_name=data.get("serviceName", ""),
            service_version=data.get("serviceVersion", ""),
            daily_count=data.get("dailyCount", 0),
            hourly_count=data.get("hourlyCount"),
            minute_count=data.get("minuteCount"),
        )


@dataclass
class RemoteArtifactRef:
    """A reference to a remote artifact with optional secret for authentication."""

    url: str
    secret_name: Optional[str] = None


# Union type: a remote artifact is either a plain URL string or a RemoteArtifactRef
RemoteArtifact = str | RemoteArtifactRef
