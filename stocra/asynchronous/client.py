import asyncio
import logging
from asyncio import Semaphore
from contextlib import asynccontextmanager
from itertools import count
from typing import (
    AsyncGenerator,
    AsyncIterable,
    Awaitable,
    List,
    Optional,
    Tuple,
    Union,
    cast,
)

from aiohttp import ClientError, ClientResponseError, ClientSession, ClientTimeout

from stocra.asynchronous.error_handlers import DEFAULT_ERROR_HANDLERS
from stocra.base_client import StocraBase
from stocra.models import Block, ErrorHandler, StocraHTTPError, Transaction

logger = logging.getLogger("stocra")


class Stocra(StocraBase):
    _session: ClientSession
    _semaphore: Optional[Semaphore]
    _error_handlers: List[ErrorHandler]

    def __init__(
        self,
        token: Optional[str] = None,
        connect_timeout: Optional[float] = None,
        read_timeout: Optional[float] = None,
        semaphore: Optional[Semaphore] = None,
        error_handlers: Optional[List[ErrorHandler]] = DEFAULT_ERROR_HANDLERS,
    ):
        super().__init__(
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

    async def close(self) -> None:
        await self._session.close()

    async def _acquire(self) -> None:
        if self._semaphore:
            await self._semaphore.acquire()

    def _release(self) -> None:
        if self._semaphore:
            self._semaphore.release()

    @asynccontextmanager
    async def _with_semaphore(self) -> AsyncGenerator[None, None]:
        await self._acquire()
        try:
            yield
        finally:
            self._release()

    async def _get(self, blockchain: str, endpoint: str) -> dict:  # type: ignore[return]
        for iteration in count(start=1):
            try:
                response = await self._session.get(
                    f"https://{blockchain}.stocra.com/v1.0/{endpoint}",
                    raise_for_status=True,
                    allow_redirects=False,
                    headers=self.headers,
                )
                return cast(dict, await response.json())
            except ClientError as exception:
                error = StocraHTTPError(endpoint=endpoint, iteration=iteration, exception=exception)
                if await self._should_continue(error):
                    continue

                raise

    async def _should_continue(self, error: StocraHTTPError) -> bool:
        if not self._error_handlers:
            return False

        for error_handler in self._error_handlers:
            retry = await cast(Awaitable[bool], error_handler(error))
            if retry:
                return True

        return False

    async def get_block(self, blockchain: str, hash_or_height: Union[str, int] = "latest") -> Block:
        logger.debug("%s: get_block %s", blockchain, hash_or_height)
        async with self._with_semaphore():
            block_json = await self._get(blockchain=blockchain, endpoint=f"blocks/{hash_or_height}")
            return Block(**block_json)

    async def get_transaction(self, blockchain: str, transaction_hash: str) -> Transaction:
        logger.debug("%s: get_transaction %s", blockchain, transaction_hash)
        async with self._with_semaphore():
            transaction_json = await self._get(blockchain=blockchain, endpoint=f"transactions/{transaction_hash}")
            return Transaction(**transaction_json)

    async def get_all_transactions_of_block(self, blockchain: str, block: Block) -> AsyncIterable[Transaction]:
        logger.debug("%s: get_all_transactions %s", blockchain, block.height)
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
        n_blocks_ahead: int = 1,
    ) -> AsyncIterable[Block]:
        if n_blocks_ahead < 1:
            raise ValueError(f"`n_blocks_ahead` must be greater than 0. Got `{n_blocks_ahead}`")

        block = await self.get_block(blockchain=blockchain, hash_or_height=start_block_hash_or_height)
        first_block_to_load_height = block.height + 1
        last_block_to_load_height = first_block_to_load_height + n_blocks_ahead + 1
        yield block

        block_tasks = [
            asyncio.create_task(self.get_block(blockchain, height))
            for height in range(first_block_to_load_height, last_block_to_load_height)
        ]

        while True:
            block_task = block_tasks.pop(0)
            try:
                await asyncio.wait_for(block_task, timeout=None)
                yield block_task.result()
            except ClientResponseError as exception:
                if exception.status == 404:
                    logger.debug(
                        "%s: stream_new_blocks_ahead %s: 404, sleeping for %d seconds",
                        blockchain,
                        first_block_to_load_height,
                        sleep_interval_seconds,
                    )
                    await asyncio.sleep(sleep_interval_seconds)
                    block_tasks.insert(0, asyncio.create_task(self.get_block(blockchain, first_block_to_load_height)))
                    continue

                raise

            block_tasks.append(asyncio.create_task(self.get_block(blockchain, last_block_to_load_height)))
            first_block_to_load_height += 1
            last_block_to_load_height += 1

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
