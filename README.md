# Stocra Python SDK
- [Api documentation](https://stocra.github.io/sdk-python/)
  - [Models](https://stocra.github.io/sdk-python/stocra/models.html)
- [Using synchronous client](#synchronous-client)
- [Using asynchronous client](#asynchronous-client)
- [Error handlers](#error-handlers)

## Synchronous client
### Install
```bash
pip install stocra[synchronous]
```
### Usage
#### Instantiate client
```python
from stocra.synchronous.client import Stocra

stocra_client = Stocra(
    token: str = "" ,
    connect_timeout: Optional[float] = None,
    read_timeout: Optional[float] = None,
    # ThreadPoolExecutor(N) if you want transactions obtained in N threads at the same time
    executor: Optional[Executor] = None, 
    # Errors handlers are executed when request fails
    error_handlers: Optional[List[ErrorHandler]] = DEFAULT_ERROR_HANDLERS,
)
```
#### Stream new transactions:
```python
for block, transaction in stocra_client.stream_new_transactions(
    blockchain="ethereum", # str
    start_block_hash_or_height="latest", # Union[str, int] 
    sleep_interval_seconds=10 # float, interval to sleep if blockchain has no new blocks
): # returns Iterable[Tuple[Block, Transaction]]
    print(block.height, transaction.hash)
```
#### Stream new blocks:
```python
for block in stocra_client.stream_new_blocks(
    blockchain="ethereum", # str
    start_block_hash_or_height="latest", # Union[str, int] 
    sleep_interval_seconds=10 # float, interval to sleep if blockchain has no new blocks
): # returns Iterable[Block]
    print(block)
```
#### Get block
```python
block = stocra_client.get_block(
    blockchain="bitcoin", # str
    hash_or_height="latest", # Union[str, int] = "latest"
) # returns Block
```
#### Get transaction
```python
transaction = stocra_client.get_transaction(
    blockchain="bitcoin", # str
    transaction_hash="latest", # str
) # returns Transaction
```
#### Get all transactions in block
```python
transactions = stocra_client.get_all_transactions_of_block(
    blockchain="bitcoin", # str 
    block=block, # Block
) # returns Iterable[Transaction]
for transaction in transactions:
    print(transaction)
```
## Asynchronous client
### Install
```bash
pip install stocra[asynchronous]
```
### Usage
#### Instantiate client
```python
from stocra.asynchronous.client import Stocra

stocra_client = Stocra(
    token: str = "" ,
    connect_timeout: Optional[float] = None,
    read_timeout: Optional[float] = None,
    # Limit number of requests made at the same time
    semaphore: Optional[Semaphore] = None,
    error_handlers: Optional[List[ErrorHandler]] = DEFAULT_ERROR_HANDLERS,
)
```
#### Stream new transactions:
```python
async for block, transaction in stocra_client.stream_new_transactions(
    blockchain="ethereum", # str
    start_block_hash_or_height="latest", # Union[str, int] 
    sleep_interval_seconds=10 # float, interval to sleep if blockchain has no new blocks
): # returns AsyncIterable[Tuple[Block, Transaction]]
    print(block.height, transaction.hash)
```
#### Stream new blocks:
```python
async for block in stocra_client.stream_new_blocks(
    blockchain="ethereum", # str
    start_block_hash_or_height="latest", # Union[str, int] 
    sleep_interval_seconds=10 # float, interval to sleep if blockchain has no new blocks
): # returns AsyncIterable[Block]
    print(block)
```
#### Get block
```python
block = await stocra_client.get_block(
    blockchain="bitcoin", # str
    hash_or_height="latest", # Union[str, int] = "latest"
) # returns Block
```
#### Get transaction
```python
transaction = await stocra_client.get_transaction(
    blockchain="bitcoin", # str
    transaction_hash="latest", # str
) # returns Transaction
```
#### Get all transactions in block
```python
transactions = stocra_client.get_all_transactions_of_block(
    blockchain="bitcoin", # str 
    block=block, # Block
) # returns AsyncIterable[Transaction]
async for transaction in transactions:
    print(transaction)
```
## Error handlers
- error handlers are functions that are called after a request fails
- signature: `ErrorHandler = Callable[[StocraHTTPError], Union[bool, Awaitable[bool]]]`
- [StocraHTTPError](https://github.com/stocra/sdk-python/blob/master/stocra/models.py#L96) model
- returned value indicates whether request should be repeated or exception raised
- examples of synchronous error handlers: [stocra.synchronous.error_handlers](https://github.com/stocra/sdk-python/blob/master/stocra/synchronous/error_handlers.py)
- examples of asynchronous error handlers: [stocra.asynchronous.error_handlers](https://github.com/stocra/sdk-python/blob/master/stocra/asynchronous/error_handlers.py)
