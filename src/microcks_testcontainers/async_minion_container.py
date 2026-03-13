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

"""MicrocksAsyncMinionContainer - Async protocol support for Microcks."""

from __future__ import annotations

import re
import sys

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

from testcontainers.core.container import DockerContainer
from testcontainers.core.network import Network
from testcontainers.core.wait_strategies import LogMessageWaitStrategy

from .connections import (
    AmazonServiceConnection,
    GenericConnection,
    GooglePubSubConnection,
    KafkaConnection,
)
from .microcks_container import MicrocksContainer


class MicrocksAsyncMinionContainer(DockerContainer):  # type: ignore[misc]
    """Testcontainer for the Microcks Async Minion, providing async protocol mocking.

    Supports Kafka, MQTT, AMQP, Amazon SQS/SNS, and Google Pub/Sub.
    """

    MICROCKS_ASYNC_MINION_HTTP_PORT = 8081

    def __init__(self, network: Network, image: str) -> None:
        super().__init__(image)
        self._extra_protocols = ""
        self.with_network(network)
        self.with_network_aliases("microcks-async-minion")
        self.with_env("MICROCKS_HOST_PORT", f"microcks:{MicrocksContainer.MICROCKS_HTTP_PORT}")
        self.with_exposed_ports(self.MICROCKS_ASYNC_MINION_HTTP_PORT)

    def start(self) -> Self:
        """Start the async minion container."""
        self.waiting_for(LogMessageWaitStrategy("Profile prod activated."))
        super().start()
        return self

    # --- Protocol connections ---

    def with_kafka_connection(self, connection: KafkaConnection) -> Self:
        """Connect to a Kafka broker for message mocking."""
        self._add_protocol("KAFKA")
        self.with_env("ASYNC_PROTOCOLS", self._extra_protocols)
        self.with_env("KAFKA_BOOTSTRAP_SERVER", connection.bootstrap_servers)
        return self

    def with_mqtt_connection(self, connection: GenericConnection) -> Self:
        """Connect to a MQTT broker for message mocking."""
        self._add_protocol("MQTT")
        self.with_env("ASYNC_PROTOCOLS", self._extra_protocols)
        self.with_env("MQTT_SERVER", connection.server)
        self.with_env("MQTT_USERNAME", connection.username)
        self.with_env("MQTT_PASSWORD", connection.password)
        return self

    def with_amqp_connection(self, connection: GenericConnection) -> Self:
        """Connect to an AMQP broker for message mocking."""
        self._add_protocol("AMQP")
        self.with_env("ASYNC_PROTOCOLS", self._extra_protocols)
        self.with_env("AMQP_SERVER", connection.server)
        self.with_env("AMQP_USERNAME", connection.username)
        self.with_env("AMQP_PASSWORD", connection.password)
        return self

    def with_amazon_sqs_connection(self, connection: AmazonServiceConnection) -> Self:
        """Connect to an Amazon SQS service for message mocking."""
        self._add_protocol("SQS")
        self.with_env("ASYNC_PROTOCOLS", self._extra_protocols)
        self.with_env("AWS_SQS_REGION", connection.region)
        self.with_env("AWS_ACCESS_KEY_ID", connection.access_key)
        self.with_env("AWS_SECRET_ACCESS_KEY", connection.secret_key)
        if connection.endpoint_override:
            self.with_env("AWS_SQS_ENDPOINT", connection.endpoint_override)
        return self

    def with_amazon_sns_connection(self, connection: AmazonServiceConnection) -> Self:
        """Connect to an Amazon SNS service for message mocking."""
        self._add_protocol("SNS")
        self.with_env("ASYNC_PROTOCOLS", self._extra_protocols)
        self.with_env("AWS_SNS_REGION", connection.region)
        self.with_env("AWS_ACCESS_KEY_ID", connection.access_key)
        self.with_env("AWS_SECRET_ACCESS_KEY", connection.secret_key)
        if connection.endpoint_override:
            self.with_env("AWS_SNS_ENDPOINT", connection.endpoint_override)
        return self

    def with_google_pubsub_connection(self, connection: GooglePubSubConnection) -> Self:
        """Connect to a Google Pub/Sub service for message mocking."""
        self._add_protocol("GOOGLEPUBSUB")
        self.with_env("ASYNC_PROTOCOLS", self._extra_protocols)
        self.with_env("GOOGLEPUBSUB_PROJECT", connection.project_id)
        if connection.emulator_host:
            self.with_env("PUBSUB_EMULATOR_HOST", connection.emulator_host)
        return self

    # --- Mock topic/queue name getters ---

    def get_ws_mock_endpoint(self, service: str, version: str, operation_name: str) -> str:
        """Get the WebSocket mock endpoint for a service operation."""
        operation_name = self._strip_verb(operation_name)
        host = self.get_container_host_ip()
        port = self.get_exposed_port(self.MICROCKS_ASYNC_MINION_HTTP_PORT)
        svc = service.replace(" ", "+")
        ver = version.replace(" ", "+")
        return f"ws://{host}:{port}/api/ws/{svc}/{ver}/{operation_name}"

    def get_kafka_mock_topic(self, service: str, version: str, operation_name: str) -> str:
        """Get the Kafka mock topic name for a service operation."""
        operation_name = self._strip_verb(operation_name)
        svc = re.sub(r"[\s-]", "", service)
        return f"{svc}-{version}-{operation_name.replace('/', '-')}"

    def get_mqtt_mock_topic(self, service: str, version: str, operation_name: str) -> str:
        """Get the MQTT mock topic name for a service operation."""
        operation_name = self._strip_verb(operation_name)
        svc = re.sub(r"[\s-]", "", service)
        ver = version.replace(" ", "")
        return f"{svc}-{ver}-{operation_name}"

    def get_amqp_mock_destination(self, service: str, version: str, operation_name: str) -> str:
        """Get the AMQP mock destination name for a service operation."""
        operation_name = self._strip_verb(operation_name)
        svc = re.sub(r"[\s-]", "", service)
        ver = version.replace(" ", "")
        return f"{svc}-{ver}-{operation_name}"

    def get_amazon_sqs_mock_queue(self, service: str, version: str, operation_name: str) -> str:
        """Get the Amazon SQS mock queue name for a service operation."""
        return self._amazon_mock_destination(service, version, operation_name)

    def get_amazon_sns_mock_topic(self, service: str, version: str, operation_name: str) -> str:
        """Get the Amazon SNS mock topic name for a service operation."""
        return self._amazon_mock_destination(service, version, operation_name)

    def get_google_pubsub_mock_topic(self, service: str, version: str, operation_name: str) -> str:
        """Get the Google Pub/Sub mock topic name for a service operation."""
        operation_name = self._strip_verb(operation_name)
        svc = re.sub(r"[\s-]", "", service)
        ver = version.replace(" ", "")
        return f"{svc}-{ver}-{operation_name.replace('/', '-')}"

    # --- Private helpers ---

    def _add_protocol(self, protocol: str) -> None:
        """Add a protocol to the extra protocols string if not already present."""
        if f",{protocol}" not in self._extra_protocols:
            self._extra_protocols += f",{protocol}"

    @staticmethod
    def _strip_verb(operation_name: str) -> str:
        """Remove SUBSCRIBE/PUBLISH verb prefix if present."""
        if " " in operation_name:
            return operation_name.split(" ", 1)[1]
        return operation_name

    def _amazon_mock_destination(self, service: str, version: str, operation_name: str) -> str:
        """Build Amazon service mock destination name."""
        operation_name = self._strip_verb(operation_name)
        svc = re.sub(r"[\s-]", "", service)
        ver = re.sub(r"[\s.]", "", version)
        return f"{svc}-{ver}-{operation_name.replace('/', '-')}"
