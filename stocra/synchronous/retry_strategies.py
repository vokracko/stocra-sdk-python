from urllib3.util.retry import Retry

DEFAULT_RETRY_STRATEGY = Retry(total=10, backoff_factor=1, status_forcelist=[429, 503])
