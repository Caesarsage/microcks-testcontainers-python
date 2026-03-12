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

"""Unit tests for assertion helpers (no Docker required)."""

import pytest

from microcks_testcontainers import (
    TestCaseResult,
    TestResult,
    TestRunnerType,
    TestStepResult,
)
from microcks_testcontainers.assertions import (
    MicrocksTestFailure,
    assert_failure,
    assert_success,
)


def _make_test_result(success: bool, cases: list[TestCaseResult] | None = None) -> TestResult:
    return TestResult(
        id="test-123",
        version=1,
        test_number=1,
        test_date=0,
        tested_endpoint="http://example.com",
        service_id="API:1.0",
        timeout=5000,
        elapsed_time=1000,
        success=success,
        in_progress=False,
        runner_type=TestRunnerType.OPEN_API_SCHEMA,
        test_case_results=cases or [],
    )


class TestAssertSuccess:
    def test_overall_success(self):
        result = _make_test_result(True)
        assert_success(result)  # Should not raise

    def test_overall_failure_raises(self):
        result = _make_test_result(
            False,
            [
                TestCaseResult(
                    success=False,
                    elapsed_time=100,
                    operation_name="GET /items",
                    test_step_results=[
                        TestStepResult(
                            success=False,
                            elapsed_time=50,
                            request_name="Get items",
                            message="Expected 200 but got 500",
                        )
                    ],
                )
            ],
        )
        with pytest.raises(MicrocksTestFailure, match="has failed"):
            assert_success(result)

    def test_operation_success(self):
        result = _make_test_result(
            True,
            [
                TestCaseResult(
                    success=True,
                    elapsed_time=100,
                    operation_name="GET /items",
                    test_step_results=[
                        TestStepResult(success=True, elapsed_time=50, request_name="Get items")
                    ],
                )
            ],
        )
        assert_success(result, "GET /items")

    def test_operation_not_found_raises(self):
        result = _make_test_result(True, [])
        with pytest.raises(MicrocksTestFailure, match="no test case"):
            assert_success(result, "GET /nonexistent")

    def test_message_success(self):
        result = _make_test_result(
            True,
            [
                TestCaseResult(
                    success=True,
                    elapsed_time=100,
                    operation_name="GET /items",
                    test_step_results=[
                        TestStepResult(success=True, elapsed_time=50, request_name="Get items")
                    ],
                )
            ],
        )
        assert_success(result, "GET /items", "Get items")

    def test_message_not_found_raises(self):
        result = _make_test_result(
            True,
            [
                TestCaseResult(
                    success=True,
                    elapsed_time=100,
                    operation_name="GET /items",
                    test_step_results=[],
                )
            ],
        )
        with pytest.raises(MicrocksTestFailure, match="no test step"):
            assert_success(result, "GET /items", "Nonexistent message")


class TestAssertFailure:
    def test_operation_failure(self):
        result = _make_test_result(
            False,
            [
                TestCaseResult(
                    success=False,
                    elapsed_time=100,
                    operation_name="GET /items",
                    test_step_results=[
                        TestStepResult(success=False, elapsed_time=50, request_name="Get items", message="Error")
                    ],
                )
            ],
        )
        assert_failure(result, "GET /items")  # Should not raise

    def test_operation_success_raises(self):
        result = _make_test_result(
            True,
            [
                TestCaseResult(
                    success=True,
                    elapsed_time=100,
                    operation_name="GET /items",
                    test_step_results=[],
                )
            ],
        )
        with pytest.raises(MicrocksTestFailure, match="should have failed"):
            assert_failure(result, "GET /items")

    def test_message_failure(self):
        result = _make_test_result(
            False,
            [
                TestCaseResult(
                    success=False,
                    elapsed_time=100,
                    operation_name="GET /items",
                    test_step_results=[
                        TestStepResult(success=False, elapsed_time=50, request_name="Get items", message="Error")
                    ],
                )
            ],
        )
        assert_failure(result, "GET /items", "Get items")  # Should not raise

    def test_message_success_raises(self):
        result = _make_test_result(
            True,
            [
                TestCaseResult(
                    success=True,
                    elapsed_time=100,
                    operation_name="GET /items",
                    test_step_results=[
                        TestStepResult(success=True, elapsed_time=50, request_name="Get items")
                    ],
                )
            ],
        )
        with pytest.raises(MicrocksTestFailure, match="should have failed"):
            assert_failure(result, "GET /items", "Get items")
