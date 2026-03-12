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

"""Unit tests for model serialization/deserialization (no Docker required)."""

from microcks_testcontainers import (
    OAuth2ClientContext,
    OAuth2GrantType,
    Secret,
    TestRequest,
    TestResult,
    TestRunnerType,
)


class TestSecretSerialization:
    def test_minimal_secret(self):
        secret = Secret(name="my-secret")
        d = secret.to_dict()
        assert d == {"name": "my-secret"}

    def test_full_secret(self):
        secret = Secret(
            name="my-secret",
            description="A test secret",
            username="user",
            password="pass",
            token="tok",
            token_header="X-Token",
            ca_cert_pem="-----BEGIN CERT-----",
        )
        d = secret.to_dict()
        assert d["name"] == "my-secret"
        assert d["description"] == "A test secret"
        assert d["username"] == "user"
        assert d["password"] == "pass"
        assert d["token"] == "tok"
        assert d["tokenHeader"] == "X-Token"
        assert d["caCertPem"] == "-----BEGIN CERT-----"


class TestTestRequestSerialization:
    def test_minimal_request(self):
        req = TestRequest(
            service_id="API:1.0",
            test_endpoint="http://example.com",
            runner_type=TestRunnerType.OPEN_API_SCHEMA,
            timeout=5000,
        )
        d = req.to_dict()
        assert d == {
            "serviceId": "API:1.0",
            "testEndpoint": "http://example.com",
            "runnerType": "OPEN_API_SCHEMA",
            "timeout": 5000,
        }

    def test_request_with_oauth2(self):
        req = TestRequest(
            service_id="API:1.0",
            test_endpoint="http://example.com",
            runner_type=TestRunnerType.OPEN_API_SCHEMA,
            timeout=5000,
            oauth2_context=OAuth2ClientContext(
                client_id="my-client",
                token_uri="http://keycloak/token",
                grant_type=OAuth2GrantType.CLIENT_CREDENTIALS,
                client_secret="secret123",
            ),
        )
        d = req.to_dict()
        assert "oAuth2Context" in d
        assert d["oAuth2Context"]["clientId"] == "my-client"
        assert d["oAuth2Context"]["grantType"] == "CLIENT_CREDENTIALS"
        assert d["oAuth2Context"]["clientSecret"] == "secret123"


class TestTestResultDeserialization:
    def test_from_dict(self):
        data = {
            "id": "abc123",
            "version": 1,
            "testNumber": 42,
            "testDate": 1700000000,
            "testedEndpoint": "http://example.com",
            "serviceId": "API:1.0",
            "timeout": 5000,
            "elapsedTime": 1200,
            "success": True,
            "inProgress": False,
            "runnerType": "OPEN_API_SCHEMA",
            "testCaseResults": [
                {
                    "success": True,
                    "elapsedTime": 500,
                    "operationName": "GET /items",
                    "testStepResults": [
                        {
                            "success": True,
                            "elapsedTime": 100,
                            "requestName": "Get items",
                            "eventMessageName": "",
                            "message": "",
                        }
                    ],
                }
            ],
        }
        result = TestResult.from_dict(data)
        assert result.id == "abc123"
        assert result.test_number == 42
        assert result.success is True
        assert result.in_progress is False
        assert result.runner_type == TestRunnerType.OPEN_API_SCHEMA
        assert len(result.test_case_results) == 1
        assert result.test_case_results[0].operation_name == "GET /items"
        assert result.test_case_results[0].test_step_results[0].request_name == "Get items"

    def test_from_dict_with_authorized_client(self):
        data = {
            "id": "abc123",
            "version": 1,
            "testNumber": 1,
            "testDate": 0,
            "testedEndpoint": "http://example.com",
            "serviceId": "API:1.0",
            "timeout": 5000,
            "elapsedTime": 0,
            "success": True,
            "inProgress": False,
            "runnerType": "OPEN_API_SCHEMA",
            "testCaseResults": [],
            "authorizedClient": {
                "grantType": "CLIENT_CREDENTIALS",
                "principalName": "my-client",
                "tokenUri": "http://keycloak/token",
                "scopes": "openid profile",
            },
        }
        result = TestResult.from_dict(data)
        assert result.authorized_client is not None
        assert result.authorized_client.principal_name == "my-client"
        assert result.authorized_client.scopes == "openid profile"
        assert result.authorized_client.grant_type == OAuth2GrantType.CLIENT_CREDENTIALS


class TestEnumValues:
    def test_runner_types(self):
        assert TestRunnerType.HTTP.value == "HTTP"
        assert TestRunnerType.POSTMAN.value == "POSTMAN"
        assert TestRunnerType.ASYNC_API_SCHEMA.value == "ASYNC_API_SCHEMA"

    def test_grant_types(self):
        assert OAuth2GrantType.PASSWORD.value == "PASSWORD"
        assert OAuth2GrantType.CLIENT_CREDENTIALS.value == "CLIENT_CREDENTIALS"
