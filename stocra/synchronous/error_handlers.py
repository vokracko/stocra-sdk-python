from time import sleep

from requests import HTTPError

from stocra.models import StocraHTTPError
from stocra.utils import calculate_sleep


def retry_on_service_unavailable(error: StocraHTTPError) -> bool:
    if not isinstance(error.exception, HTTPError):
        return False

    if error.exception.response.status_code != 503:
        return False

    if error.iteration > 10:
        return False

    sleep(calculate_sleep(error.iteration))
    return True


def retry_on_too_many_requests(error: StocraHTTPError) -> bool:
    if not isinstance(error.exception, HTTPError):
        return False

    if error.exception.response.status_code != 429:
        return False

    if error.iteration > 10:
        return False

    sleep(int(error.exception.response.headers["Retry-After"]))
    return True
