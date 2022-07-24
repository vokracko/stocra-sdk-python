import requests_mock
from requests import Timeout

from stocra.synchronous.client import Stocra
from stocra.synchronous.error_handlers import (
    retry_on_bad_gateway,
    retry_on_service_unavailable,
    retry_on_timeout_error,
    retry_on_too_many_requests,
)
from tests.fixtures import BASE_URL, BLOCK_100


def test_retry_on_service_unavailable() -> None:
    client = Stocra(error_handlers=[retry_on_service_unavailable])
    with requests_mock.Mocker(real_http=False) as mocked:
        mocked.get(f"{BASE_URL}/blocks/{BLOCK_100.height}", [dict(status_code=503), dict(text=BLOCK_100.json())])
        block = client.get_block("bitcoin", hash_or_height=BLOCK_100.height)
        assert block == BLOCK_100


def test_retry_on_too_many_requests() -> None:
    client = Stocra(error_handlers=[retry_on_too_many_requests])
    with requests_mock.Mocker(real_http=False) as mocked:
        mocked.get(
            f"{BASE_URL}/blocks/{BLOCK_100.height}",
            [dict(status_code=429, headers={"Retry-After": "1"}), dict(text=BLOCK_100.json())],
        )
        block = client.get_block("bitcoin", hash_or_height=BLOCK_100.height)
        assert block == BLOCK_100


def test_retry_on_bad_gateway() -> None:
    client = Stocra(error_handlers=[retry_on_bad_gateway])
    with requests_mock.Mocker(real_http=False) as mocked:
        mocked.get(
            f"{BASE_URL}/blocks/{BLOCK_100.height}",
            [dict(status_code=502), dict(text=BLOCK_100.json())],
        )
        block = client.get_block("bitcoin", hash_or_height=BLOCK_100.height)
        assert block == BLOCK_100


def test_retry_on_timeout_error() -> None:
    client = Stocra(error_handlers=[retry_on_timeout_error])
    with requests_mock.Mocker(real_http=False) as mocked:
        mocked.get(
            f"{BASE_URL}/blocks/{BLOCK_100.height}",
            [dict(exc=Timeout("Connection timeout")), dict(text=BLOCK_100.json())],
        )
        block = client.get_block("bitcoin", hash_or_height=BLOCK_100.height)
        assert block == BLOCK_100
