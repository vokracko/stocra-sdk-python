import json
from datetime import datetime
from decimal import Decimal

from stocra.models import (
    Amount,
    Block,
    Currency,
    Input,
    Output,
    Token,
    TokenType,
    Transaction,
)

BASE_URL = "https://bitcoin.stocra.com/v1.0"
TRANSACTION_BLOCK_100 = Transaction(
    hash="test_transaction_hash_block_100",
    inputs=[Input(address="test_address_input", amount=Amount(value=Decimal("1"), currency_symbol="BTC"))],
    outputs=[Output(address="test_address_output", amount=Amount(value=Decimal("0.8"), currency_symbol="BTC"))],
    fee=Amount(value=Decimal("0.2"), currency_symbol="BTC"),
)
TRANSACTION_BLOCK_101 = Transaction(
    hash="test_transaction_hash_block_101",
    inputs=[Input(address="test_address_input", amount=Amount(value=Decimal("1"), currency_symbol="BTC"))],
    outputs=[Output(address="test_address_output", amount=Amount(value=Decimal("0.8"), currency_symbol="BTC"))],
    fee=Amount(value=Decimal("0.2"), currency_symbol="BTC"),
)
BLOCK_100 = Block(
    height=100,
    hash="test_block_hash_100",
    timestamp_ms=int(datetime.now().timestamp() * 1_000),
    transactions=[TRANSACTION_BLOCK_100.hash],
)
BLOCK_101 = Block(
    height=101,
    hash="test_block_hash_101",
    timestamp_ms=int(datetime.now().timestamp() * 1_000),
    transactions=[TRANSACTION_BLOCK_101.hash],
)

TOKEN_CONTRACT_ADDRESS = "0xdAC17F958D2ee523a2206206994597C13D831ec7"
TOKEN = Token(currency=Currency(symbol="USDT", name="Tether"), scaling="0.000001", type=TokenType.ERC20)
TOKEN_RESPONSE = {TOKEN_CONTRACT_ADDRESS: json.loads(TOKEN.json())}
