import abc
from typing import Dict, List, Optional

from stocra.models import ErrorHandler, Token


class StocraBase(abc.ABC):
    _api_key: Optional[str] = None
    _error_handlers: Optional[List[ErrorHandler]] = None
    _tokens: Dict[str, Dict[str, Token]] = dict()

    def __init__(
        self,
        api_key: Optional[str] = None,
        error_handlers: Optional[List[ErrorHandler]] = None,
    ) -> None:
        self._api_key = api_key
        self._error_handlers = error_handlers

    @property
    def headers(self) -> dict:
        if self._api_key:
            return dict(Authorization=f"Bearer {self._api_key}")

        return dict()
