# Stocra Python SDK

## Sync
### Install
```bash
pip install stocra[sync]
```
### Usage
#### Instantiate client
```python
from stocra.synchronous.client import Stocra
# from concurrent.futures import ThreadPoolExecutor

stocra_client = Stocra(
    version: str = "v1.0",
    token: str = "" ,
    connect_timeout: Optional[float] = None,
    read_timeout: Optional[float] = None,
    # ThreadPoolExecutor(N) if you want transactions obtained in N threads at the same time
    executor: Optional[Executor] = None, 
    # Retry stragegy, useful for retrying on 503 or 429
    retry_strategy: Retry = None,
)
```
#### Stream new transactions:
```python
for block, transaction in stocra_client.stream_new_transactions(
    blockchain="ethereum", # str
    start_block_hash_or_height="latest", # Union[str, int] 
    sleep_interval_seconds=10 # float, interval to sleep if blockchain has no new blocks
): # returns Iterator[Tuple[Block, Transaction]]
    print(block.height, transaction.hash)
```
#### Stream new blocks:
```python
for block, transaction in stocra_client.stream_new_blocks(
    blockchain="ethereum", # str
    start_block_hash_or_height="latest", # Union[str, int] 
    sleep_interval_seconds=10 # float, interval to sleep if blockchain has no new blocks
): # returns Iterator[Block]
    print(block.height, transaction.hash)
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
## Async
### Install
```bash
pip install stocra[async]
```
### Usage
## TODO fix this one
#### Instantiate client
```python
from stocra.asynchronous.client import Stocra
# from concurrent.futures import ThreadPoolExecutor

stocra_client = Stocra(
    version: str = "v1.0",
    token: str = "" ,
    connect_timeout: Optional[float] = None,
    read_timeout: Optional[float] = None,
    # ThreadPoolExecutor(N) if you want transactions obtained in N threads at the same time
    executor: Optional[Executor] = None, 
    # Retry stragegy, useful for retrying on 503 or 429
    retry_strategy: Retry = None,
)
```
#### Stream new transactions:
```python
async for block, transaction in stocra_client.stream_new_transactions(
    blockchain="ethereum", # str
    start_block_hash_or_height="latest", # Union[str, int] 
    sleep_interval_seconds=10 # float, interval to sleep if blockchain has no new blocks
): # returns AsyncIterator[Tuple[Block, Transaction]]
    print(block.height, transaction.hash)
```
#### Stream new blocks:
```python
async for block, transaction in stocra_client.stream_new_blocks(
    blockchain="ethereum", # str
    start_block_hash_or_height="latest", # Union[str, int] 
    sleep_interval_seconds=10 # float, interval to sleep if blockchain has no new blocks
): # returns AsyncIterator[Block]
    print(block.height, transaction.hash)
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
## TODO
- [ ] describe usage of retry strategy
- [ ] describe usage of semaphores
