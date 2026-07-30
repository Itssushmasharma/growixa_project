import json
import logging
from typing import Any

import pytest

from growixa_worker.consumer import make_healthcheck_handler, parse_job_message


class FakeMessage:
    def __init__(self, body: bytes) -> None:
        self.body = body

    def process(self) -> "FakeMessage":
        return self

    async def __aenter__(self) -> "FakeMessage":
        return self

    async def __aexit__(self, *exc: object) -> None:
        return None


async def test_parse_job_message_decodes_the_json_body() -> None:
    message: Any = FakeMessage(json.dumps({"job_id": "abc-123", "job_type": "grx.x"}).encode())

    body = await parse_job_message(message)

    assert body == {"job_id": "abc-123", "job_type": "grx.x"}


async def test_healthcheck_handler_logs_the_job_id(caplog: pytest.LogCaptureFixture) -> None:
    message: Any = FakeMessage(json.dumps({"job_id": "abc-123"}).encode())
    handler = make_healthcheck_handler()

    with caplog.at_level(logging.INFO, logger="growixa_worker"):
        await handler(message)

    assert "abc-123" in caplog.text
