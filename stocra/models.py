from dataclasses import dataclass
from decimal import Decimal
from enum import Enum, unique
from typing import Any, Awaitable, Callable, Dict, List, Optional, Union

from pydantic import BaseModel, root_validator, validator

Address = str
TransactionHash = str
OutputIndex = int


class Amount(BaseModel):
    value: Decimal
    currency_symbol: str

    def __add__(self, other: Any) -> "Amount":
        if isinstance(other, Amount):
            if self.currency_symbol != other.currency_symbol:
                raise ValueError(
                    f"Amounts have different currencies: {self.currency_symbol} != {other.currency_symbol}"
                )

            return Amount(value=self.value + other.value, currency_symbol=self.currency_symbol)

        raise TypeError(f"Cannot add Amount and {type(other)}")

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Amount):
            raise TypeError(f"Cannot compare Amount and {type(other)}")

        if self.value != other.value:
            return False

        if self.currency_symbol != other.currency_symbol:
            return False

        return True


class TransactionPointer(BaseModel):
    transaction_hash: TransactionHash
    output_index: OutputIndex


class Input(BaseModel):
    address: Optional[Address] = None
    amount: Optional[Amount] = None
    transaction_pointer: Optional[TransactionPointer] = None

    @classmethod
    @root_validator
    def validate_address_or_pointer(cls, values: Dict) -> Dict:  # pylint: disable=no-self-argument
        if not (values["address"] or values["transaction_pointer"]):
            raise ValueError("Either address or transaction pointer must be specified")

        return values


class Output(BaseModel):
    address: Address
    amount: Amount


class Transaction(BaseModel):
    hash: TransactionHash
    inputs: List[Input]
    outputs: List[Output]
    fee: Amount

    @classmethod
    @validator("fee")
    def validate_fee(cls, value: Amount) -> Amount:
        if value.value < 0:
            raise ValueError(f"Fee cannot be negative! Got {value.value}")

        return value


class Block(BaseModel):
    height: int
    hash: str
    timestamp_ms: int
    transactions: List[str] = []

    @classmethod
    @validator("timestamp_ms")
    def validate_timestamp_ms(cls, value: int) -> int:  # pylint: disable=no-self-argument
        # I don't really care if this runs even after 2286
        if len(str(value)) != 13:
            raise ValueError("Timestamp must be in miliseconds")

        return value


class Currency(BaseModel):
    symbol: str
    name: str

    class Config:
        frozen = True


@unique
class TokenType(Enum):
    ERC20 = "ERC20"


class Token(BaseModel):
    currency: Currency
    scaling: Decimal
    type: TokenType


@dataclass(frozen=True)
class StocraHTTPError:
    endpoint: str
    iteration: int
    exception: Exception


ErrorHandler = Callable[[StocraHTTPError], Union[bool, Awaitable[bool]]]
