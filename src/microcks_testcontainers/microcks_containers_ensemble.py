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

"""MicrocksContainersEnsemble - Multi-container orchestration for Microcks."""

from __future__ import annotations

import sys

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

from testcontainers.core.container import DockerContainer
from testcontainers.core.network import Network
from testcontainers.core.wait_strategies import LogMessageWaitStrategy

from .async_minion_container import MicrocksAsyncMinionContainer
from .connections import (
    AmazonServiceConnection,
    GenericConnection,
    GooglePubSubConnection,
    KafkaConnection,
)
from .microcks_container import MicrocksContainer
from .models import RemoteArtifact, Secret


class MicrocksContainersEnsemble:
    """Orchestrates Microcks, Postman runtime, and Async Minion containers.

    Manages a coordinated setup of multiple containers on a shared Docker network.

    Usage::

        with Network() as network:
            ensemble = MicrocksContainersEnsemble(network)
            ensemble.with_main_artifacts(["my-api.yaml"])
            ensemble.with_postman()
            with ensemble:
                mc = ensemble.get_microcks_container()
                result = mc.test_endpoint(test_request)
    """

    MICROCKS_CONTAINER_ALIAS = "microcks"
    POSTMAN_CONTAINER_ALIAS = "postman"
    ASYNC_MINION_CONTAINER_ALIAS = "microcks-async-minion"

    def __init__(self, network: Network, image: str = MicrocksContainer.DEFAULT_IMAGE) -> None:
        self._network = network
        self._image = image

        self._microcks = MicrocksContainer(image)
        self._microcks.with_network(network)
        self._microcks.with_network_aliases(self.MICROCKS_CONTAINER_ALIAS)
        self._microcks.with_env(
            "POSTMAN_RUNNER_URL", f"http://{self.POSTMAN_CONTAINER_ALIAS}:3000"
        )
        self._microcks.with_env(
            "TEST_CALLBACK_URL",
            f"http://{self.MICROCKS_CONTAINER_ALIAS}:{MicrocksContainer.MICROCKS_HTTP_PORT}",
        )
        self._microcks.with_env(
            "ASYNC_MINION_URL",
            f"http://{self.ASYNC_MINION_CONTAINER_ALIAS}:{MicrocksAsyncMinionContainer.MICROCKS_ASYNC_MINION_HTTP_PORT}",
        )

        self._postman: DockerContainer | None = None
        self._async_minion: MicrocksAsyncMinionContainer | None = None
        self._async_minion_env: dict[str, str] = {}

    # --- Context manager ---

    def __enter__(self) -> MicrocksContainersEnsemble:
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore[no-untyped-def]
        self.stop()

    # --- Configuration (all return self for chaining) ---

    def with_debug_log_level(self) -> Self:
        """Enable debug log level on all containers in the ensemble."""
        self._microcks.with_debug_log_level()
        self._async_minion_env["QUARKUS_LOG_CONSOLE_LEVEL"] = "DEBUG"
        self._async_minion_env["QUARKUS_LOG_CATEGORY__IO_GITHUB_MICROCKS__LEVEL"] = "DEBUG"
        return self

    def with_postman(self, image: str = "quay.io/microcks/microcks-postman-runtime:latest") -> Self:
        """Enable the Postman runtime container for test execution."""
        self._postman = DockerContainer(image)
        self._postman.with_network(self._network)
        self._postman.with_network_aliases(self.POSTMAN_CONTAINER_ALIAS)
        return self

    def with_async_feature(self, image: str | None = None) -> Self:
        """Enable the Async Minion container for async protocol support."""
        if image is None:
            image = self._image.replace("microcks-uber", "microcks-uber-async-minion")
        if image.endswith("-native"):
            image = image[: -len("-native")]
        self._async_minion = MicrocksAsyncMinionContainer(self._network, image)
        return self

    # --- Artifact/secret delegation to MicrocksContainer ---

    def with_main_artifacts(self, artifacts: list[str]) -> Self:
        """Provide paths to artifacts that will be imported as primary ones."""
        self._microcks.with_main_artifacts(artifacts)
        return self

    def with_secondary_artifacts(self, artifacts: list[str]) -> Self:
        """Provide paths to artifacts that will be imported as secondary ones."""
        self._microcks.with_secondary_artifacts(artifacts)
        return self

    def with_main_remote_artifacts(self, remote_artifacts: list[RemoteArtifact]) -> Self:
        """Provide URLs of remote artifacts to import as primary ones."""
        self._microcks.with_main_remote_artifacts(remote_artifacts)
        return self

    def with_secondary_remote_artifacts(self, remote_artifacts: list[RemoteArtifact]) -> Self:
        """Provide URLs of remote artifacts to import as secondary ones."""
        self._microcks.with_secondary_remote_artifacts(remote_artifacts)
        return self

    def with_snapshots(self, snapshots: list[str]) -> Self:
        """_summary_

        Args:
            snapshots (list[str]): _description_

        Returns:
            Self: _description_
        """        """Provide paths to repository snapshots that will be imported."""
        self._microcks.with_snapshots(snapshots)
        return self

    def with_secret(self, secret: Secret) -> Self:
        """Provide a secret to be imported after startup."""
        self._microcks.with_secret(secret)
        return self

    # --- Protocol connections (delegated to async minion) ---

    def with_kafka_connection(self, connection: KafkaConnection) -> Self:
        """Connect the async minion to a Kafka broker."""
        if self._async_minion is None:
            raise RuntimeError("Async feature must be enabled first")
        self._async_minion.with_kafka_connection(connection)
        return self

    def with_mqtt_connection(self, connection: GenericConnection) -> Self:
        """Connect the async minion to a MQTT broker."""
        if self._async_minion is None:
            raise RuntimeError("Async feature must be enabled first")
        self._async_minion.with_mqtt_connection(connection)
        return self

    def with_amqp_connection(self, connection: GenericConnection) -> Self:
        """Connect the async minion to an AMQP broker."""
        if self._async_minion is None:
            raise RuntimeError("Async feature must be enabled first")
        self._async_minion.with_amqp_connection(connection)
        return self

    def with_amazon_sqs_connection(self, connection: AmazonServiceConnection) -> Self:
        """Connect the async minion to an Amazon SQS service."""
        if self._async_minion is None:
            raise RuntimeError("Async feature must be enabled first")
        self._async_minion.with_amazon_sqs_connection(connection)
        return self

    def with_amazon_sns_connection(self, connection: AmazonServiceConnection) -> Self:
        """Connect the async minion to an Amazon SNS service."""
        if self._async_minion is None:
            raise RuntimeError("Async feature must be enabled first")
        self._async_minion.with_amazon_sns_connection(connection)
        return self

    def with_google_pubsub_connection(self, connection: GooglePubSubConnection) -> Self:
        """Connect the async minion to a Google Pub/Sub service."""
        if self._async_minion is None:
            raise RuntimeError("Async feature must be enabled first")
        self._async_minion.with_google_pubsub_connection(connection)
        return self

    # --- Lifecycle ---

    def start(self) -> Self:
        """Start all containers sequentially (avoids resource contention on CI)."""
        self._microcks.start()

        if self._postman is not None:
            self._postman.waiting_for(LogMessageWaitStrategy("postman-runtime wrapper listening on port"))
            self._postman.start()

        if self._async_minion is not None:
            for k, v in self._async_minion_env.items():
                self._async_minion.with_env(k, v)
            self._async_minion.start()

        return self

    def stop(self) -> None:
        """Stop all containers in the ensemble."""
        self._microcks.stop()
        if self._postman is not None:
            self._postman.stop()
        if self._async_minion is not None:
            self._async_minion.stop()

    # --- Accessors ---

    def get_microcks_container(self) -> MicrocksContainer:
        """Get the main Microcks container."""
        return self._microcks

    def get_postman_container(self) -> DockerContainer | None:
        """Get the Postman runtime container (None if not enabled)."""
        return self._postman

    def get_async_minion_container(self) -> MicrocksAsyncMinionContainer | None:
        """Get the Async Minion container (None if not enabled)."""
        return self._async_minion
