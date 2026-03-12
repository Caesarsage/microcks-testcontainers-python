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

from dataclasses import dataclass
from typing import Optional

@dataclass
class KafkaConnection:
    """Connection details to a Kafka broker."""

    bootstrap_servers: str


@dataclass
class GenericConnection:
    """Connection details to a MQTT or AMQP broker."""

    server: str
    username: str
    password: str


@dataclass
class AmazonServiceConnection:
    """Connection details to an Amazon SQS or SNS service."""

    region: str
    access_key: str
    secret_key: str
    endpoint_override: Optional[str] = None


@dataclass
class GooglePubSubConnection:
    """Connection details to a Google Pub/Sub service."""

    project_id: str
    emulator_host: Optional[str] = None
