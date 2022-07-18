import abc
from typing import List, Optional

from stocra.models import ErrorHandler


class StocraBase(abc.ABC):
    _token: Optional[str] = None
    _error_handlers: Optional[List[ErrorHandler]] = None

    def __init__(
        self,
        token: Optional[str] = None,
        error_handlers: Optional[List[ErrorHandler]] = None,
    ) -> None:
        self._token = token
        self._error_handlers = error_handlers

    @property
    def headers(self) -> dict:
        if self._token:
            return dict(Authorization=f"Bearer {self._token}")

        return dict()
