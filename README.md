# Unofficial Microcks Testcontainers Python

Python library for [Testcontainers](https://testcontainers.com) that enables embedding [Microcks](https://microcks.io) into your unit tests with lightweight, throwaway instances.

## Installation

```bash
pip install microcks-testcontainers
```

## Usage

```python
from microcks_testcontainers import MicrocksContainer

with MicrocksContainer().with_main_artifacts(["my-api.yaml"]) as mc:
    endpoint = mc.get_rest_mock_endpoint("My API", "1.0")
    # Use the endpoint in your tests
```

## License

[Apache License, Version 2.0](LICENSE)
