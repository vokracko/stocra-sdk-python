from asyncio import Semaphore
from unittest.mock import patch

import pytest
import pytest_asyncio
from aioresponses import aioresponses

from stocra.asynchronous.client import Stocra
from tests.fixtures import (
    BASE_URL,
    BLOCK_100,
    BLOCK_101,
    TRANSACTION_BLOCK_100,
    TRANSACTION_BLOCK_101,
)


@pytest_asyncio.fixture
async def default_responses():
    with aioresponses() as mocked:
        mocked.get(f"{BASE_URL}/blocks/latest", body=BLOCK_100.json())
        mocked.get(f"{BASE_URL}/blocks/{BLOCK_100.hash}", body=BLOCK_100.json())
        mocked.get(f"{BASE_URL}/blocks/{BLOCK_100.height}", body=BLOCK_100.json())
        mocked.get(f"{BASE_URL}/blocks/{BLOCK_101.hash}", body=BLOCK_101.json())
        mocked.get(f"{BASE_URL}/blocks/{BLOCK_101.height}", body=BLOCK_101.json())
        mocked.get(f"{BASE_URL}/transactions/{TRANSACTION_BLOCK_100.hash}", body=TRANSACTION_BLOCK_100.json())
        mocked.get(f"{BASE_URL}/transactions/{TRANSACTION_BLOCK_101.hash}", body=TRANSACTION_BLOCK_101.json())
        yield


@pytest_asyncio.fixture(params=[dict(semaphore=None), dict(semaphore=Semaphore(2))])
async def client(request) -> Stocra:
    client_instance = Stocra(**request.param)
    yield client_instance
    await client_instance.close()


@pytest.mark.asyncio
async def test_get_block_latest(client: Stocra, default_responses) -> None:
    block = await client.get_block("bitcoin", "latest")
    assert block == BLOCK_100


@pytest.mark.asyncio
async def test_get_block_by_height(client: Stocra, default_responses) -> None:
    block = await client.get_block("bitcoin", 100)
    assert block == BLOCK_100


@pytest.mark.asyncio
async def test_get_block_by_hash(client: Stocra, default_responses) -> None:
    block = await client.get_block("bitcoin", BLOCK_100.hash)
    assert block == BLOCK_100


@pytest.mark.asyncio
async def test_get_transaction(client: Stocra, default_responses) -> None:
    transaction = await client.get_transaction("bitcoin", TRANSACTION_BLOCK_100.hash)
    assert transaction == TRANSACTION_BLOCK_100


@pytest.mark.asyncio
async def test_get_all_transactions_of_block(client: Stocra, default_responses) -> None:
    transactions = client.get_all_transactions_of_block("bitcoin", BLOCK_100)
    transactions = [transaction async for transaction in transactions]
    assert transactions == [TRANSACTION_BLOCK_100]


@pytest.mark.asyncio
async def test_stream_new_blocks(client: Stocra, default_responses) -> None:
    blocks = client.stream_new_blocks("bitcoin", BLOCK_100.hash)
    assert await anext(blocks) == BLOCK_100
    assert await anext(blocks) == BLOCK_101


@pytest.mark.asyncio
@patch("stocra.asynchronous.client.asyncio.sleep")
async def test_stream_new_blocks_not_found(patch_sleep, client: Stocra) -> None:
    with aioresponses() as mocked:
        mocked.get(f"{BASE_URL}/blocks/{BLOCK_100.hash}", body=BLOCK_100.json())
        mocked.get(f"{BASE_URL}/blocks/{BLOCK_101.height}", status=404, body="empty")
        mocked.get(f"{BASE_URL}/blocks/{BLOCK_101.height}", body=BLOCK_101.json())
        blocks = client.stream_new_blocks(
            "bitcoin", start_block_hash_or_height=BLOCK_100.hash, sleep_interval_seconds=0.5
        )
        assert await anext(blocks) == BLOCK_100
        assert await anext(blocks) == BLOCK_101
        patch_sleep.assert_called_with(0.5)


@pytest.mark.asyncio
async def test_stream_new_transactions(client: Stocra, default_responses) -> None:
    transactions = client.stream_new_transactions("bitcoin", start_block_hash_or_height=BLOCK_100.hash)
    assert await anext(transactions) == (BLOCK_100, TRANSACTION_BLOCK_100)
    assert await anext(transactions) == (BLOCK_101, TRANSACTION_BLOCK_101)
