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

"""Assertion helpers for checking Microcks TestResult instances.

These functions raise AssertionError subclasses, integrating natively with pytest.
"""

from __future__ import annotations

from .models import TestResult
from .exceptions import MicrocksTestFailure

def assert_success(
    test_result: TestResult,
    operation_name: str | None = None,
    message_name: str | None = None,
) -> None:
    """Assert that a Microcks test result is successful.

    Args:
        test_result: The test result to check.
        operation_name: If provided, only check this operation's test case.
        message_name: If provided (with operation_name), only check this specific test step.

    Raises:
        MicrocksTestFailure: If the assertion fails.
    """
    if operation_name is None:
        # Check overall success
        if not test_result.success:
            failures: list[str] = []
            for tc in test_result.test_case_results:
                if not tc.success:
                    for ts in tc.test_step_results:
                        if not ts.success:
                            msg = ts.message.replace("\n", " && ")
                            failures.append(
                                f"Message '{ts.request_name}' of operation "
                                f"'{tc.operation_name}' failed: {msg}"
                            )
            if failures:
                raise MicrocksTestFailure(
                    f"Test '{test_result.id}' has failed:\n" + "\n".join(failures)
                )
            raise MicrocksTestFailure(
                f"Test '{test_result.id}' is not a success, but has no failure details"
            )
        return

    # Find matching test case(s)
    matching_cases = [
        tc
        for tc in test_result.test_case_results
        if tc.operation_name.lower() == operation_name.lower()
    ]
    if not matching_cases:
        raise MicrocksTestFailure(
            f"Test '{test_result.id}' has no test case for operation '{operation_name}'"
        )

    if message_name is None:
        # Check operation-level success
        for tc in matching_cases:
            if not tc.success:
                failures = []
                for ts in tc.test_step_results:
                    if not ts.success:
                        msg = ts.message.replace("\n", " && ")
                        failures.append(
                            f"Message '{ts.request_name}' of operation "
                            f"'{tc.operation_name}' failed: {msg}"
                        )
                if failures:
                    raise MicrocksTestFailure(
                        f"Test '{test_result.id}' for operation '{operation_name}' has failed:\n"
                        + "\n".join(failures)
                    )
        return

    # Check specific message/step
    for tc in matching_cases:
        matching_steps = [
            ts
            for ts in tc.test_step_results
            if ts.request_name.lower() == message_name.lower()
        ]
        if not matching_steps:
            raise MicrocksTestFailure(
                f"Test '{test_result.id}' has no test step for operation "
                f"'{operation_name}' and message '{message_name}'"
            )
        for ts in matching_steps:
            if not ts.success:
                raise MicrocksTestFailure(
                    f"Test '{test_result.id}' for operation '{operation_name}' "
                    f"and message '{message_name}' has failed: {ts.message}"
                )


def assert_failure(
    test_result: TestResult,
    operation_name: str,
    message_name: str | None = None,
) -> None:
    """Assert that a Microcks test result has failed for the given operation.

    Args:
        test_result: The test result to check.
        operation_name: The operation name to check.
        message_name: If provided, only check this specific test step.

    Raises:
        MicrocksTestFailure: If the assertion fails.
    """
    matching_cases = [
        tc
        for tc in test_result.test_case_results
        if tc.operation_name.lower() == operation_name.lower()
    ]
    if not matching_cases:
        raise MicrocksTestFailure(
            f"Test '{test_result.id}' has no test case for operation '{operation_name}'"
        )

    if message_name is None:
        for tc in matching_cases:
            if tc.success:
                raise MicrocksTestFailure(
                    f"Test '{test_result.id}' for operation '{operation_name}' should have failed"
                )
        return

    for tc in matching_cases:
        matching_steps = [
            ts
            for ts in tc.test_step_results
            if ts.request_name.lower() == message_name.lower()
        ]
        if not matching_steps:
            raise MicrocksTestFailure(
                f"Test '{test_result.id}' has no test step for operation "
                f"'{operation_name}' and message '{message_name}'"
            )
        for ts in matching_steps:
            if ts.success:
                raise MicrocksTestFailure(
                    f"Test '{test_result.id}' for operation '{operation_name}' "
                    f"and message '{message_name}' should have failed"
                )
