# Stocra Python SDK
- [SDK API documentation](https://stocra.github.io/sdk-python/)
  - [Models](https://stocra.github.io/sdk-python/stocra/models.html)
  - [Synchronous client](https://stocra.github.io/sdk-python/stocra/synchronous/client.html)
  - [Asynchronous client](https://stocra.github.io/sdk-python/stocra/asynchronous/client.html)
- [Using synchronous client](#synchronous-client)
- [Using asynchronous client](#asynchronous-client)
- [Error handlers](#error-handlers)

## Synchronous client
### Install
```bash
pip install stocra[synchronous]
```
### Usage
```python
# stream new blocks
for block in stocra_client.stream_new_blocks(blockchain="ethereum"):
    print(block)

# stream new blocks, load new blocks in the background for faster processing. Work only with executor
for block in stocra_client.stream_new_blocks_ahead(blockchain="ethereum"):
    print(block)
    
# stream new transactions
for block, transaction in stocra_client.stream_new_transactions(blockchain="ethereum"):
    print(block.height, transaction.hash)
    
# get one block
block = stocra_client.get_block(blockchain="bitcoin", hash_or_height=57043)

# get one transaction
transaction = stocra_client.get_transaction(
    blockchain="bitcoin", 
    transaction_hash="a1075db55d416d3ca199f55b6084e2115b9345e16c5cf302fc80e9d5fbf5d48d"
)

# get all transactions in block
transactions = stocra_client.get_all_transactions_of_block(blockchain="bitcoin", block=block) 
for transaction in transactions:
    print(transaction)

```
## Asynchronous client
### Install
```bash
pip install stocra[asynchronous]
```
### Usage
```python
# stream new transactions
async for block, transaction in stocra_client.stream_new_transactions(blockchain="ethereum"):
    print(block.height, transaction.hash)

# stream new blocks, load 5 blocks in the background
async for block in stocra_client.stream_new_blocks(blockchain="ethereum", n_blocks_ahead=5):
    print(block)

# get one block
block = await stocra_client.get_block(
    blockchain="bitcoin",
    hash_or_height="00000000152340ca42227603908689183edc47355204e7aca59383b0aaac1fd8"
)

# get one transaction
transaction = await stocra_client.get_transaction(
    blockchain="bitcoin",
    transaction_hash="a1075db55d416d3ca199f55b6084e2115b9345e16c5cf302fc80e9d5fbf5d48d", 
)

# get all transactions in block
transactions = stocra_client.get_all_transactions_of_block(blockchain="bitcoin", block=block)
async for transaction in transactions:
    print(transaction)
```
## Error handlers
- error handlers are functions that are called after a request fails
- signature: `ErrorHandler = Callable[[StocraHTTPError], Union[bool, Awaitable[bool]]]`
- [StocraHTTPError](https://stocra.github.io/sdk-python/stocra/models.html#StocraHTTPError) model
- returned value indicates whether request should be repeated (`True`) or exception raised (`False)
- examples of synchronous error handlers: [stocra.synchronous.error_handlers](https://stocra.github.io/sdk-python/stocra/synchronous/error_handlers.html)
- examples of asynchronous error handlers: [stocra.asynchronous.error_handlers](https://stocra.github.io/sdk-python/stocra/asynchronous/error_handlers.html)
