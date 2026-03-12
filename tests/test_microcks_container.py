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

from pathlib import Path

import pytest
import requests

from microcks_testcontainers import (
    MicrocksContainer,
    TestRequest,
    TestRunnerType,
)

RESOURCES = Path(__file__).parent.parent / "test-resources"


@pytest.mark.integration
class TestMicrocksContainerStartAndMock:
    """Test starting container, loading artifacts, and exposing mocks."""

    def test_start_load_artifacts_and_mock(self):
        with (
            MicrocksContainer()
            .with_debug_log_level()
            .with_snapshots([str(RESOURCES / "microcks-repository.json")])
            .with_main_artifacts([str(RESOURCES / "apipastries-openapi.yaml")])
            .with_main_remote_artifacts(
                ["https://raw.githubusercontent.com/microcks/microcks/master/samples/APIPastry-openapi.yaml"]
            )
            .with_secondary_artifacts([str(RESOURCES / "apipastries-postman-collection.json")])
        ) as mc:
            # Verify endpoint URL construction
            assert mc.get_soap_mock_endpoint("Pastries Service", "1.0") == (
                f"{mc.http_endpoint}/soap/Pastries Service/1.0"
            )
            assert mc.get_rest_mock_endpoint("API Pastries", "0.0.1") == (
                f"{mc.http_endpoint}/rest/API Pastries/0.0.1"
            )
            assert mc.get_graphql_mock_endpoint("Pastries Graph", "1") == (
                f"{mc.http_endpoint}/graphql/Pastries Graph/1"
            )
            assert mc.grpc_mock_endpoint.startswith("grpc://")

            # Verify path-only variants
            assert mc.get_soap_mock_endpoint_path("Pastries Service", "1.0") == "/soap/Pastries Service/1.0"
            assert mc.get_rest_mock_endpoint_path("API Pastries", "0.0.1") == "/rest/API Pastries/0.0.1"
            assert mc.get_graphql_mock_endpoint_path("Pastries Graph", "1") == "/graphql/Pastries Graph/1"

            # Verify validating endpoints
            assert mc.get_validating_rest_mock_endpoint("API Pastries", "0.0.1") == (
                f"{mc.http_endpoint}/rest-valid/API Pastries/0.0.1"
            )
            assert mc.get_validating_soap_mock_endpoint("Pastries Service", "1.0") == (
                f"{mc.http_endpoint}/soap/Pastries Service/1.0?validate=true"
            )
            assert mc.get_validating_rest_mock_endpoint_path("API Pastries", "0.0.1") == (
                "/rest-valid/API Pastries/0.0.1"
            )
            assert mc.get_validating_soap_mock_endpoint_path("Pastries Service", "1.0") == (
                "/soap/Pastries Service/1.0?validate=true"
            )

            # Check available services loaded including snapshot
            resp = requests.get(f"{mc.http_endpoint}/api/services")
            assert resp.status_code == 200
            services = resp.json()
            assert len(services) == 6
            names = [s["name"] for s in services]
            assert "API Pastries" in names
            assert "API Pastry - 2.0" in names
            assert "HelloService Mock" in names
            assert "Movie Graph API" in names
            assert "Petstore API" in names
            assert "io.github.microcks.grpc.hello.v1.HelloService" in names

            # Verify mock from main artifact
            pastries_url = mc.get_rest_mock_endpoint("API Pastries", "0.0.1")
            resp = requests.get(f"{pastries_url}/pastries/Millefeuille")
            assert resp.status_code == 200
            assert resp.json()["name"] == "Millefeuille"

            # Verify invocation counting
            assert mc.verify("API Pastries", "0.0.1") is True
            assert mc.get_service_invocations_count("API Pastries", "0.0.1") == 1

            # Verify mock from secondary artifact
            resp = requests.get(f"{pastries_url}/pastries/Eclair Chocolat")
            assert resp.status_code == 200
            assert resp.json()["name"] == "Eclair Chocolat"
            assert mc.get_service_invocations_count("API Pastries", "0.0.1") == 2

            # Verify remote artifact mock
            pastries_v2_url = mc.get_rest_mock_endpoint("API Pastry - 2.0", "2.0.0")
            resp = requests.get(f"{pastries_v2_url}/pastry/Millefeuille")
            assert resp.status_code == 200
            assert resp.json()["name"] == "Millefeuille"
            assert mc.verify("API Pastry - 2.0", "2.0.0") is True
            assert mc.get_service_invocations_count("API Pastry - 2.0", "2.0.0") == 1


@pytest.mark.integration
class TestMicrocksContainerContractTest:
    """Test contract testing against good/bad implementations."""

    def test_contract_testing(self):
        from testcontainers.core.container import DockerContainer
        from testcontainers.core.network import Network
        from testcontainers.core.waiting_utils import wait_for_logs

        with Network() as network:
            with (
                MicrocksContainer()
                .with_network(network)
            ) as mc:
                mc.import_as_main_artifact(str(RESOURCES / "apipastries-openapi.yaml"))

                bad = DockerContainer("quay.io/microcks/contract-testing-demo:01")
                bad.with_network(network)
                bad.with_network_aliases("bad-impl")
                bad.start()
                wait_for_logs(bad, "Example app listening on port 3001")

                good = DockerContainer("quay.io/microcks/contract-testing-demo:02")
                good.with_network(network)
                good.with_network_aliases("good-impl")
                good.start()
                wait_for_logs(good, "Example app listening on port 3002")

                try:
                    # Test bad implementation - should fail
                    result = mc.test_endpoint(
                        TestRequest(
                            service_id="API Pastries:0.0.1",
                            runner_type=TestRunnerType.OPEN_API_SCHEMA,
                            test_endpoint="http://bad-impl:3001",
                            timeout=2000,
                        )
                    )
                    assert result.success is False
                    assert result.tested_endpoint == "http://bad-impl:3001"
                    assert len(result.test_case_results) == 3
                    assert "string found, number expected" in result.test_case_results[0].test_step_results[0].message
                    assert "required property 'status' not found" in result.test_case_results[0].test_step_results[0].message

                    # Verify messages retrieval
                    messages = mc.get_messages_for_test_case(result, "GET /pastries")
                    assert len(messages) == 3
                    for msg in messages:
                        assert msg.request is not None
                        assert msg.response is not None
                        assert msg.request.content is not None
                        assert len(msg.request.query_parameters) == 1
                        assert msg.request.query_parameters[0].name == "size"

                    # Test good implementation - should pass
                    result = mc.test_endpoint(
                        TestRequest(
                            service_id="API Pastries:0.0.1",
                            runner_type=TestRunnerType.OPEN_API_SCHEMA,
                            test_endpoint="http://good-impl:3002",
                            timeout=3000,
                        )
                    )
                    assert result.success is True
                    assert result.tested_endpoint == "http://good-impl:3002"
                    assert len(result.test_case_results) == 3
                    assert result.test_case_results[0].test_step_results[0].message == ""
                finally:
                    bad.stop()
                    good.stop()
