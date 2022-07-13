from dataclasses import dataclass
from typing import Awaitable, Callable

from aiohttp import ClientError


@dataclass(frozen=True)
class StocraRequestError:
    # TODO improve this bit
    endpoint: str
    iteration: int
    exception: ClientError


ErrorHandler = Callable[[StocraRequestError], Awaitable[bool]]
