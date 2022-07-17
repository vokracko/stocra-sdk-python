from concurrent.futures import Executor, as_completed
from itertools import count
from time import sleep
from typing import Iterable, List, Optional, Tuple, Union

from requests import HTTPError, RequestException, Session

from stocra.base_client import StocraBase
from stocra.models import Block, ErrorHandler, StocraHTTPError, Transaction
from stocra.synchronous.error_handlers import DEFAULT_ERROR_HANDLERS


class Stocra(StocraBase):
    _session: Session
    _executor: Optional[Executor]

    def __init__(
        self,
        version: str = "v1.0",
        token: Optional[str] = None,
        connect_timeout: Optional[float] = None,
        read_timeout: Optional[float] = None,
        executor: Optional[Executor] = None,
        error_handlers: Optional[List[ErrorHandler]] = DEFAULT_ERROR_HANDLERS,
    ):
        super().__init__(
            version=version,
            connect_timeout=connect_timeout,
            read_timeout=read_timeout,
            token=token,
            error_handlers=error_handlers,
        )
        self._session = Session()
        self._executor = executor

    def _get(self, blockchain: str, endpoint: str) -> dict:
        for iteration in count(start=1):
            try:
                response = self._session.get(
                    f"https://{blockchain}.stocra.com/{self._version}/{endpoint}",
                    allow_redirects=False,
                    headers=self.headers,
                    timeout=(self._connect_timeout, self._read_timeout),
                )
                response.raise_for_status()
                return response.json()
            except RequestException as exception:
                if self._error_handlers:
                    error = StocraHTTPError(endpoint=endpoint, iteration=iteration, exception=exception)
                    if self._should_continue(error):
                        continue

                raise

    def _should_continue(self, error) -> bool:
        for error_handler in self._error_handlers:
            retry = error_handler(error)
            if retry:
                return True

        return False

    def get_block(self, blockchain: str, hash_or_height: Union[str, int] = "latest") -> Block:
        block_json = self._get(blockchain=blockchain, endpoint=f"blocks/{hash_or_height}")
        return Block(**block_json)

    def get_transaction(self, blockchain: str, transaction_hash: str) -> Transaction:
        transaction_json = self._get(blockchain=blockchain, endpoint=f"transactions/{transaction_hash}")
        return Transaction(**transaction_json)

    def get_all_transactions_of_block(self, blockchain: str, block: Block) -> Iterable[Transaction]:
        if self._executor:
            futures = [
                self._executor.submit(self.get_transaction, blockchain, transaction_hash)
                for transaction_hash in block.transactions
            ]
            for transaction_task in as_completed(futures):
                yield transaction_task.result()
        else:
            for transaction_hash in block.transactions:
                yield self.get_transaction(blockchain, transaction_hash)

    def stream_new_blocks(
        self,
        blockchain: str,
        start_block_hash_or_height: Union[int, str] = "latest",
        sleep_interval_seconds: float = 10,
    ) -> Iterable[Block]:
        block = self.get_block(blockchain=blockchain, hash_or_height=start_block_hash_or_height)
        latest_block_height = block.height
        yield block

        while True:
            try:
                block = self.get_block(blockchain=blockchain, hash_or_height=latest_block_height + 1)
            except HTTPError as exception:
                if exception.response.status_code == 404:
                    sleep(sleep_interval_seconds)
                    continue

                raise

            latest_block_height = block.height
            yield block

    def stream_new_transactions(
        self,
        blockchain: str,
        start_block_hash_or_height: Union[int, str] = "latest",
        sleep_interval_seconds: float = 10,
    ) -> Iterable[Tuple[Block, Transaction]]:
        new_blocks = self.stream_new_blocks(
            blockchain=blockchain,
            start_block_hash_or_height=start_block_hash_or_height,
            sleep_interval_seconds=sleep_interval_seconds,
        )
        for block in new_blocks:
            block_transactions = self.get_all_transactions_of_block(blockchain=blockchain, block=block)
            for transaction in block_transactions:
                yield block, transaction
