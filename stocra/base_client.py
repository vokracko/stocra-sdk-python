import abc
from typing import Optional


class StocraBase(abc.ABC):
    _version: str
    _token: Optional[str] = None
    _connect_timeout: Optional[float] = None
    _read_timeout: Optional[float] = None

    def __init__(
        self,
        version: str = "v1.0",
        connect_timeout: Optional[float] = None,
        read_timeout: Optional[float] = None,
        token: Optional[str] = None,
    ) -> None:
        self._version = version
        self._token = token
        self._connect_timeout = connect_timeout
        self._read_timeout = read_timeout

    @property
    def headers(self) -> dict:
        if self._token:
            return dict(Authorization=f"Bearer {self._token}")

        return dict()
