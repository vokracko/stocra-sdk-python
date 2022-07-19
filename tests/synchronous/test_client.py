from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from unittest.mock import patch

import pytest
import requests_mock

from stocra.synchronous.client import Stocra
from tests.fixtures import (
    BASE_URL,
    BLOCK_100,
    BLOCK_101,
    TOKEN_CONTRACT_ADDRESS,
    TOKEN_RESPONSE,
    TRANSACTION_BLOCK_100,
    TRANSACTION_BLOCK_101,
)


@pytest.fixture
def default_responses():
    with requests_mock.Mocker(real_http=False) as mocked:
        mocked.get(f"{BASE_URL}/blocks/latest", text=BLOCK_100.json())
        mocked.get(f"{BASE_URL}/blocks/{BLOCK_100.hash}", text=BLOCK_100.json())
        mocked.get(f"{BASE_URL}/blocks/{BLOCK_100.height}", text=BLOCK_100.json())
        mocked.get(f"{BASE_URL}/blocks/{BLOCK_101.hash}", text=BLOCK_101.json())
        mocked.get(f"{BASE_URL}/blocks/{BLOCK_101.height}", text=BLOCK_101.json())
        mocked.get(f"{BASE_URL}/transactions/{TRANSACTION_BLOCK_100.hash}", text=TRANSACTION_BLOCK_100.json())
        mocked.get(f"{BASE_URL}/transactions/{TRANSACTION_BLOCK_101.hash}", text=TRANSACTION_BLOCK_101.json())
        yield


@pytest.fixture(params=[dict(executor=None), dict(executor=ThreadPoolExecutor())])
def client(request) -> Stocra:
    yield Stocra(**request.param)


def test_get_block_latest(client: Stocra, default_responses) -> None:
    block = client.get_block("bitcoin", "latest")
    assert block == BLOCK_100


def test_get_block_by_height(client: Stocra, default_responses) -> None:
    block = client.get_block("bitcoin", 100)
    assert block == BLOCK_100


def test_get_block_by_hash(client: Stocra, default_responses) -> None:
    block = client.get_block("bitcoin", BLOCK_100.hash)
    assert block == BLOCK_100


def test_get_transaction(client: Stocra, default_responses) -> None:
    transaction = client.get_transaction("bitcoin", TRANSACTION_BLOCK_100.hash)
    assert transaction == TRANSACTION_BLOCK_100


def test_get_all_transactions_of_block(client: Stocra, default_responses) -> None:
    transactions = client.get_all_transactions_of_block("bitcoin", BLOCK_100)
    assert list(transactions) == [TRANSACTION_BLOCK_100]


def test_stream_new_blocks(client: Stocra, default_responses) -> None:
    blocks = client.stream_new_blocks("bitcoin", BLOCK_100.hash)
    assert next(blocks) == BLOCK_100
    assert next(blocks) == BLOCK_101


@patch("stocra.synchronous.client.sleep")
def test_stream_new_blocks_not_found(patch_sleep, client: Stocra) -> None:
    with requests_mock.Mocker(real_http=False) as mocked:
        mocked.get(f"{BASE_URL}/blocks/{BLOCK_100.hash}", text=BLOCK_100.json())
        mocked.get(f"{BASE_URL}/blocks/{BLOCK_101.height}", [dict(status_code=404), dict(text=BLOCK_101.json())])
        blocks = client.stream_new_blocks(
            "bitcoin", start_block_hash_or_height=BLOCK_100.hash, sleep_interval_seconds=0.5
        )
        assert next(blocks) == BLOCK_100
        assert next(blocks) == BLOCK_101
        patch_sleep.assert_called_with(0.5)


def test_stream_new_transactions(client: Stocra, default_responses) -> None:
    transactions = client.stream_new_transactions("bitcoin", start_block_hash_or_height=BLOCK_100.hash)
    assert next(transactions) == (BLOCK_100, TRANSACTION_BLOCK_100)
    assert next(transactions) == (BLOCK_101, TRANSACTION_BLOCK_101)


def test_scale_token_value(client: Stocra):
    with requests_mock.Mocker(real_http=False) as mocked:
        mocked.get("https://ethereum.stocra.com/v1.0/tokens", json=TOKEN_RESPONSE)
        value = client.scale_token_value("ethereum", TOKEN_CONTRACT_ADDRESS, Decimal("325000000"))
        assert value == Decimal("325")
