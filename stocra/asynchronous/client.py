import asyncio
from asyncio import Semaphore
from contextlib import asynccontextmanager
from itertools import count
from typing import AsyncIterable, List, Optional, Tuple, Union

from aiohttp import ClientError, ClientResponseError, ClientSession, ClientTimeout

from stocra.asynchronous.error_handlers import DEFAULT_ERROR_HANDLERS
from stocra.base_client import StocraBase
from stocra.models import Block, ErrorHandler, StocraHTTPError, Transaction


class Stocra(StocraBase):
    _session: ClientSession
    _semaphore: Optional[Semaphore]
    _error_handlers: List[ErrorHandler]

    def __init__(
        self,
        version: str = "v1.0",
        token: Optional[str] = None,
        connect_timeout: Optional[float] = None,
        read_timeout: Optional[float] = None,
        semaphore: Optional[Semaphore] = None,
        error_handlers: Optional[List[ErrorHandler]] = DEFAULT_ERROR_HANDLERS,
    ):
        super().__init__(
            version=version,
            connect_timeout=connect_timeout,
            read_timeout=read_timeout,
            token=token,
            error_handlers=error_handlers,
        )
        self._session = ClientSession(
            timeout=ClientTimeout(
                sock_connect=self._connect_timeout,
                sock_read=self._read_timeout,
            ),
        )
        self._semaphore = semaphore

    async def close(self):
        await self._session.close()

    async def _acquire(self) -> None:
        if self._semaphore:
            await self._semaphore.acquire()

    def _release(self) -> None:
        if self._semaphore:
            self._semaphore.release()

    @asynccontextmanager
    async def with_semaphore(self):
        await self._acquire()
        try:
            yield
        finally:
            self._release()

    async def _get(self, blockchain: str, endpoint: str) -> dict:
        for iteration in count(start=1):
            try:
                response = await self._session.get(
                    f"https://{blockchain}.stocra.com/{self._version}/{endpoint}",
                    raise_for_status=True,
                    allow_redirects=False,
                    headers=self.headers,
                )
                return await response.json()
            except ClientError as exception:
                if self._error_handlers:
                    error = StocraHTTPError(endpoint=endpoint, iteration=iteration, exception=exception)
                    if await self._should_continue(error):
                        continue

                raise

    async def _should_continue(self, error):
        for error_handler in self._error_handlers:
            retry = await error_handler(error)
            if retry:
                return True

        return False

    async def get_block(self, blockchain: str, hash_or_height: Union[str, int] = "latest") -> Block:
        async with self.with_semaphore():
            block_json = await self._get(blockchain=blockchain, endpoint=f"blocks/{hash_or_height}")
            return Block(**block_json)

    async def get_transaction(self, blockchain: str, transaction_hash: str) -> Transaction:
        async with self.with_semaphore():
            transaction_json = await self._get(blockchain=blockchain, endpoint=f"transactions/{transaction_hash}")
            return Transaction(**transaction_json)

    async def get_all_transactions_of_block(self, blockchain: str, block: Block) -> AsyncIterable[Transaction]:
        transaction_tasks = []

        for transaction_hash in block.transactions:
            task = asyncio.create_task(self.get_transaction(blockchain=blockchain, transaction_hash=transaction_hash))
            transaction_tasks.append(task)

        for completed_task in asyncio.as_completed(transaction_tasks):
            task = await completed_task
            yield task

    async def stream_new_blocks(
        self,
        blockchain: str,
        start_block_hash_or_height: Union[int, str] = "latest",
        sleep_interval_seconds: float = 10,
    ) -> AsyncIterable[Block]:
        block = await self.get_block(blockchain=blockchain, hash_or_height=start_block_hash_or_height)
        latest_block_height = block.height

        yield block

        while True:
            try:
                block = await self.get_block(blockchain=blockchain, hash_or_height=latest_block_height + 1)
            except ClientResponseError as exception:
                if exception.status == 404:
                    await asyncio.sleep(sleep_interval_seconds)
                    continue

                raise

            latest_block_height = block.height
            yield block

    async def stream_new_transactions(
        self,
        blockchain: str,
        start_block_hash_or_height: Union[int, str] = "latest",
        sleep_interval_seconds: float = 10,
    ) -> AsyncIterable[Tuple[Block, Transaction]]:
        new_blocks = self.stream_new_blocks(
            blockchain=blockchain,
            start_block_hash_or_height=start_block_hash_or_height,
            sleep_interval_seconds=sleep_interval_seconds,
        )
        async for block in new_blocks:
            block_transactions = self.get_all_transactions_of_block(blockchain=blockchain, block=block)
            async for transaction in block_transactions:
                yield block, transaction
