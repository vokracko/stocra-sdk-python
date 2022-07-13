def calculate_sleep(backoff_factor: int) -> int:
    return 1 * (2 ** (backoff_factor - 1))
