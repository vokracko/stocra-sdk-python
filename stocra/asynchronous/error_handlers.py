import asyncio

from aiohttp import ClientConnectionError, ClientResponseError

from stocra.models import StocraHTTPError
from stocra.utils import calculate_sleep


async def retry_on_service_unavailable(error: StocraHTTPError) -> bool:
    if not isinstance(error.exception, ClientResponseError):
        return False

    if error.exception.status != 503:
        return False

    if error.iteration > 10:
        return False

    await asyncio.sleep(calculate_sleep(error.iteration))
    return True


async def retry_on_connection_error(error: StocraHTTPError) -> bool:
    if not isinstance(error.exception, ClientConnectionError):
        return False

    if error.iteration > 10:
        return False

    await asyncio.sleep(calculate_sleep(error.iteration))
    return True


async def retry_on_too_many_requests(error: StocraHTTPError) -> bool:
    if not isinstance(error.exception, ClientResponseError):
        return False

    if error.exception.status != 429:
        return False

    if error.iteration > 10:
        return False

    headers = error.exception.headers

    if not headers:
        return False

    retry_after = headers.get("Retry-After", 0)
    await asyncio.sleep(int(retry_after))
    return True
