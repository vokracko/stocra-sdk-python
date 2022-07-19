import logging
from concurrent.futures import Executor, as_completed
from decimal import Decimal
from itertools import count
from time import sleep
from typing import Dict, Iterable, List, Optional, Tuple, Union, cast

from requests import HTTPError, RequestException, Session

from stocra.base_client import StocraBase
from stocra.models import Block, ErrorHandler, StocraHTTPError, Token, Transaction

logger = logging.getLogger("stocra")


class Stocra(StocraBase):
    _session: Session
    _executor: Optional[Executor]

    def __init__(
        self,
        api_key: Optional[str] = None,
        session: Optional[Session] = None,
        executor: Optional[Executor] = None,
        error_handlers: Optional[List[ErrorHandler]] = None,
    ):
        super().__init__(
            api_key=api_key,
            error_handlers=error_handlers,
        )
        self._session = session or Session()
        self._executor = executor

    def get_block(self, blockchain: str, hash_or_height: Union[str, int] = "latest") -> Block:
        logger.debug("%s: get_block %s", blockchain, hash_or_height)
        block_json = self._get(blockchain=blockchain, endpoint=f"blocks/{hash_or_height}")
        return Block(**block_json)

    def get_transaction(self, blockchain: str, transaction_hash: str) -> Transaction:
        logger.debug("%s: get_transaction %s", blockchain, transaction_hash)
        transaction_json = self._get(blockchain=blockchain, endpoint=f"transactions/{transaction_hash}")
        return Transaction(**transaction_json)

    def get_all_transactions_of_block(self, blockchain: str, block: Block) -> Iterable[Transaction]:
        logger.debug("%s: get_all_transactions %s", blockchain, block.height)
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
        next_block_height = block.height + 1
        yield block

        while True:
            try:
                block = self.get_block(blockchain=blockchain, hash_or_height=next_block_height)
            except HTTPError as exception:
                if exception.response.status_code == 404:
                    self._handle_404_during_block_streaming(blockchain, next_block_height, sleep_interval_seconds)
                    continue

                raise

            next_block_height += 1
            yield block

    def stream_new_blocks_ahead(
        self,
        blockchain: str,
        start_block_hash_or_height: Union[int, str] = "latest",
        sleep_interval_seconds: float = 10,
        n_blocks_ahead: int = 10,
    ) -> Iterable[Block]:
        if not self._executor:
            raise Exception("Works only with executor")

        if n_blocks_ahead < 1:
            raise ValueError(f"`n_blocks_ahead` must be greater than 0. Got `{n_blocks_ahead}`")

        block = self.get_block(blockchain=blockchain, hash_or_height=start_block_hash_or_height)
        next_block_height = block.height + 1
        last_block_height = next_block_height + n_blocks_ahead + 1
        yield block

        block_tasks = [
            self._executor.submit(self.get_block, blockchain, height)
            for height in range(next_block_height, last_block_height)
        ]

        while True:
            block_task = block_tasks.pop(0)
            try:
                yield block_task.result()
            except HTTPError as exception:
                if exception.response.status_code == 404:
                    self._handle_404_during_block_streaming(blockchain, next_block_height, sleep_interval_seconds)
                    block_tasks.insert(0, self._executor.submit(self.get_block, blockchain, next_block_height))
                    continue

                raise

            block_tasks.append(self._executor.submit(self.get_block, blockchain, last_block_height))
            next_block_height += 1
            last_block_height += 1

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

    def get_tokens(self, blockchain: str) -> Dict[str, Token]:
        if self._tokens.get(blockchain) is None:
            self._refresh_tokens(blockchain)

        return self._tokens[blockchain]

    def scale_token_value(self, blockchain: str, contract_address: str, value: Decimal) -> Decimal:
        token = self.get_tokens(blockchain)[contract_address]
        return value * token.scaling

    def _get(self, blockchain: str, endpoint: str) -> dict:  # type: ignore[return]
        for iteration in count(start=1):
            try:
                response = self._session.get(
                    f"https://{blockchain}.stocra.com/v1.0/{endpoint}",
                    allow_redirects=False,
                    headers=self.headers,
                )
                response.raise_for_status()
                return cast(dict, response.json())
            except RequestException as exception:
                error = StocraHTTPError(endpoint=endpoint, iteration=iteration, exception=exception)
                if self._should_continue(error):
                    continue

                raise

    def _should_continue(self, error: StocraHTTPError) -> bool:
        if not self._error_handlers:
            return False

        for error_handler in self._error_handlers:
            retry = error_handler(error)
            if retry:
                return True

        return False

    @classmethod
    def _handle_404_during_block_streaming(
        cls, blockchain: str, block_height: int, sleep_interval_seconds: float
    ) -> None:
        logger.debug(
            "%s: stream_new_blocks %s: 404, sleeping for %d seconds",
            blockchain,
            block_height,
            sleep_interval_seconds,
        )
        sleep(sleep_interval_seconds)

    def _refresh_tokens(self, blockchain: str) -> None:
        tokens = self._get(blockchain, "tokens")
        self._tokens[blockchain] = {contract_address: Token(**token) for contract_address, token in tokens.items()}
