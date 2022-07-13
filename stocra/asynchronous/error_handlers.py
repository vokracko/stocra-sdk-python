import asyncio

from aiohttp import ClientConnectionError, ClientResponseError

from stocra.asynchronous.retry_models import StocraRequestError
from stocra.utils import calculate_sleep


async def retry_on_service_unavailable(error: StocraRequestError) -> bool:
    if not isinstance(error.exception, ClientResponseError):
        return False

    if error.exception.status != 503:
        return False

    if error.iteration > 10:
        return False

    await asyncio.sleep(calculate_sleep(error.iteration))
    return True


async def retry_on_connection_error(error: StocraRequestError) -> bool:
    if not isinstance(error.exception, ClientConnectionError):
        return False

    if error.iteration > 10:
        return False

    await asyncio.sleep(calculate_sleep(error.iteration))
    return True


async def retry_on_too_many_requests(error: StocraRequestError) -> bool:
    if not isinstance(error.exception, ClientResponseError):
        return False

    if error.exception.status != 429:
        return False

    if error.iteration > 10:
        return False

    await asyncio.sleep(int(error.exception.headers["Retry-After"]))
    return True


DEFAULT_ERROR_HANDLERS = [
    retry_on_too_many_requests,
    retry_on_service_unavailable,
    retry_on_connection_error,
]
