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

from testcontainers.core.container import DockerContainer
from testcontainers.core.network import Network
from testcontainers.core.waiting_utils import wait_for_logs

from microcks_testcontainers import (
    MicrocksContainersEnsemble,
    TestRequest,
    TestRunnerType,
)

RESOURCES = Path(__file__).parent.parent / "test-resources"


@pytest.mark.integration
class TestEnsembleMock:
    """Test ensemble container mock functionality."""

    def test_ensemble_mock(self):
        with Network() as network:
            ensemble = MicrocksContainersEnsemble(network)
            ensemble.with_main_artifacts([str(RESOURCES / "apipastries-openapi.yaml")])
            ensemble.with_secondary_artifacts([str(RESOURCES / "apipastries-postman-collection.json")])

            with ensemble:
                mc = ensemble.get_microcks_container()
                url = mc.get_rest_mock_endpoint("API Pastries", "0.0.1")

                # Check main artifact mock
                resp = requests.get(f"{url}/pastries/Millefeuille")
                assert resp.status_code == 200
                assert resp.json()["name"] == "Millefeuille"

                # Check secondary artifact mock
                resp = requests.get(f"{url}/pastries/Eclair Chocolat")
                assert resp.status_code == 200
                assert resp.json()["name"] == "Eclair Chocolat"


@pytest.mark.integration
class TestEnsemblePostmanContract:
    """Test ensemble with Postman runner for contract testing."""

    def test_ensemble_postman_contract(self):
        with Network() as network:
            ensemble = MicrocksContainersEnsemble(network)
            ensemble.with_main_artifacts([str(RESOURCES / "apipastries-openapi.yaml")])
            ensemble.with_secondary_artifacts([str(RESOURCES / "apipastries-postman-collection.json")])
            ensemble.with_postman()

            with ensemble:
                bad = DockerContainer("quay.io/microcks/contract-testing-demo:02")
                bad.with_network(network)
                bad.with_network_aliases("bad-impl")
                bad.start()
                wait_for_logs(bad, "Example app listening on port 3002")

                good = DockerContainer("quay.io/microcks/contract-testing-demo:03")
                good.with_network(network)
                good.with_network_aliases("good-impl")
                good.start()
                wait_for_logs(good, "Example app listening on port 3003")

                mc = ensemble.get_microcks_container()

                try:
                    # Test bad implementation with Postman runner
                    result = mc.test_endpoint(
                        TestRequest(
                            service_id="API Pastries:0.0.1",
                            runner_type=TestRunnerType.POSTMAN,
                            test_endpoint="http://bad-impl:3002",
                            timeout=3000,
                        )
                    )
                    assert result.success is False
                    assert result.tested_endpoint == "http://bad-impl:3002"
                    assert len(result.test_case_results) == 3
                    # Postman runner stops at first failure, so 1 step result per case
                    assert len(result.test_case_results[0].test_step_results) == 1

                    # Test good implementation
                    result = mc.test_endpoint(
                        TestRequest(
                            service_id="API Pastries:0.0.1",
                            runner_type=TestRunnerType.POSTMAN,
                            test_endpoint="http://good-impl:3003",
                            timeout=3000,
                        )
                    )
                    assert result.success is True
                    assert result.tested_endpoint == "http://good-impl:3003"
                    assert len(result.test_case_results) == 3
                finally:
                    bad.stop()
                    good.stop()
