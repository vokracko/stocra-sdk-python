import pytest
from aioresponses import aioresponses

from stocra.asynchronous.client import Stocra
from stocra.asynchronous.error_handlers import (
    retry_on_service_unavailable,
    retry_on_too_many_requests,
)
from tests.fixtures import BASE_URL, BLOCK_100


@pytest.mark.asyncio
async def test_retry_on_service_unavailable() -> None:
    client = Stocra(error_handlers=[retry_on_service_unavailable])
    with aioresponses() as mocked:
        mocked.get(f"{BASE_URL}/blocks/{BLOCK_100.height}", status=503)
        mocked.get(f"{BASE_URL}/blocks/{BLOCK_100.height}", body=BLOCK_100.json())
        block = await client.get_block("bitcoin", hash_or_height=BLOCK_100.height)
        assert block == BLOCK_100
    await client.close()


@pytest.mark.asyncio
async def test_retry_on_too_many_requests() -> None:
    client = Stocra(error_handlers=[retry_on_too_many_requests])
    with aioresponses() as mocked:
        mocked.get(f"{BASE_URL}/blocks/{BLOCK_100.height}", status=429, headers={"Retry-After": "1"})
        mocked.get(f"{BASE_URL}/blocks/{BLOCK_100.height}", body=BLOCK_100.json())
        block = await client.get_block("bitcoin", hash_or_height=BLOCK_100.height)
        assert block == BLOCK_100
    await client.close()
