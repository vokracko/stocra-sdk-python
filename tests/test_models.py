from decimal import Decimal

import pytest

from stocra.models import Amount, Transaction


def test_amount_add() -> None:
    first = Amount(value=Decimal("1"), currency_symbol="BTC")
    second = Amount(value=Decimal("2"), currency_symbol="BTC")
    assert first + second == Amount(value=Decimal("3"), currency_symbol="BTC")


def test_amount_add_wrong_currency() -> None:
    first = Amount(value=Decimal("1"), currency_symbol="BTC")
    second = Amount(value=Decimal("2"), currency_symbol="ETH")
    with pytest.raises(ValueError):
        first + second  # pylint:disable=pointless-statement


def test_amount_add_wrong_type() -> None:
    first = Amount(value=Decimal("1"), currency_symbol="BTC")
    with pytest.raises(TypeError):
        first + Decimal("2")  # pylint:disable=expression-not-assigned


@pytest.mark.parametrize(
    "first, second, expected_result",
    [
        (
            Amount(value=Decimal("1"), currency_symbol="BTC"),
            Amount(value=Decimal("1"), currency_symbol="BTC"),
            True,
        ),
        (
            Amount(value=Decimal("1"), currency_symbol="BTC"),
            Amount(value=Decimal("2"), currency_symbol="BTC"),
            False,
        ),
        (
            Amount(value=Decimal("1"), currency_symbol="BTC"),
            Amount(value=Decimal("1"), currency_symbol="ETH"),
            False,
        ),
    ],
)
def test_amount_equal(first: Amount, second: Amount, expected_result: bool) -> None:
    result = first == second
    assert result is expected_result


def test_amount_equal_wrong_type() -> None:
    with pytest.raises(TypeError):
        Amount(value=Decimal("1"), currency_symbol="BTC") == Decimal("1")  # pylint:disable=expression-not-assigned


def test_negative_fee() -> None:
    with pytest.raises(ValueError):
        Transaction(fee=Amount(value=Decimal("-1"), currency_symbol="BTC"))


def test_extra_fields() -> None:
    with_extra_field = Amount(value=Decimal("1"), currency_symbol="BTC", new_field="test")
    without_extra_field = Amount(value=Decimal("1"), currency_symbol="BTC")
    assert with_extra_field == without_extra_field
