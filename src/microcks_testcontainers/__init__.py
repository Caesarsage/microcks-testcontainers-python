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

"""Microcks Testcontainers for Python.

Provides testcontainer support for embedding Microcks into your unit tests
with lightweight, throwaway container instances.
"""

from .models import (
    DailyInvocationStatistic,
    EventMessage,
    Header,
    OAuth2AuthorizedClient,
    OAuth2ClientContext,
    OAuth2GrantType,
    Parameter,
    RemoteArtifact,
    RemoteArtifactRef,
    Request,
    RequestResponsePair,
    Response,
    Secret,
    SecretRef,
    TestCaseResult,
    TestRequest,
    TestResult,
    TestRunnerType,
    TestStepResult,
    UnidirectionalEvent,
)
from .microcks_container import MicrocksContainer
from .assertions import assert_failure, assert_success
from .exceptions import MicrocksException, MicrocksTestFailure

__all__ = [
    # Containers
    "MicrocksContainer",
    # Models
    "DailyInvocationStatistic",
    "EventMessage",
    "Header",
    "OAuth2AuthorizedClient",
    "OAuth2ClientContext",
    "OAuth2GrantType",
    "Parameter",
    "RemoteArtifact",
    "RemoteArtifactRef",
    "Request",
    "RequestResponsePair",
    "Response",
    "Secret",
    "SecretRef",
    "TestCaseResult",
    "TestRequest",
    "TestResult",
    "TestRunnerType",
    "TestStepResult",
    "UnidirectionalEvent",
    # Assertions
    "MicrocksTestFailure",
    "assert_failure",
    "assert_success",
    # Exceptions
    "MicrocksException",
    "MicrocksTestFailure",
]
