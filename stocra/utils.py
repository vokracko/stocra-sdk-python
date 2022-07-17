from typing import cast


def calculate_sleep(backoff_factor: int) -> int:
    sleep_length = 1 * (2 ** (backoff_factor - 1))
    return cast(int, sleep_length)
