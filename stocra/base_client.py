import abc
from typing import List, Optional

from stocra.models import ErrorHandler


class StocraBase(abc.ABC):
    _token: Optional[str] = None
    _connect_timeout: Optional[float] = None
    _read_timeout: Optional[float] = None
    _error_handlers: Optional[List[ErrorHandler]] = None

    def __init__(
        self,
        connect_timeout: Optional[float] = None,
        read_timeout: Optional[float] = None,
        token: Optional[str] = None,
        error_handlers: Optional[List[ErrorHandler]] = None,
    ) -> None:
        self._version = version
        self._token = token
        self._connect_timeout = connect_timeout
        self._read_timeout = read_timeout
        self._error_handlers = error_handlers

    @property
    def headers(self) -> dict:
        if self._token:
            return dict(Authorization=f"Bearer {self._token}")

        return dict()
