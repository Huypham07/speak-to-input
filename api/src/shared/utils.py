from __future__ import annotations

import base64
import random
import time
from functools import lru_cache
from functools import wraps

import numpy as np
from shared.logging import get_logger
from shared.settings import Settings


@lru_cache
def get_settings():
    return Settings()  # type: ignore


def profile(func):
    """Decorator to profile execution time. Using default logger with info level\n
    Output: [module.function] executed in: 0.0s
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        logger = get_logger('profiler')
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        logger.info(
            f'[{func.__module__}.{func.__name__}] executed in: {end_time - start_time}s',
        )

        if hasattr(result, 'processing_time'):
            setattr(result, 'processing_time', end_time - start_time)

        return result

    return wrapper


def encode_basic_auth(username, password):
    credentials = f'{username}:{password}'
    encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
    return encoded_credentials


def generate_account_number(user_id: int, sequence: int = 1) -> str:
    """
    Generate a unique account number

    Format: FF{user_id:08d}{sequence:02d}
    - FF: Bank code (FinFlow)
    - user_id: 8 digits padded with zeros
    - sequence: 2 digits (01, 02, 03... for multiple accounts)

    Examples:
    - User ID 1, Account 1: FF0000000101
    - User ID 1, Account 2: FF0000000102
    - User ID 123, Account 1: FF0000012301
    - User ID 99999, Account 1: FF0009999901

    Args:
        user_id: The user's ID
        sequence: The account sequence number (default: 1)

    Returns:
        str: Generated account number
    """
    return f'FF{user_id:08d}{sequence:02d}'


def parse_account_number(account_number: str) -> dict:
    """
    Parse an account number to extract components

    Args:
        account_number: The account number to parse

    Returns:
        dict: Dictionary with bank_code, user_id, and sequence

    Raises:
        ValueError: If account number format is invalid
    """
    if not account_number or len(account_number) != 12:
        raise ValueError('Invalid account number format')

    if not account_number.startswith('FF'):
        raise ValueError('Invalid bank code')

    try:
        bank_code = account_number[:2]
        user_id = int(account_number[2:10])
        sequence = int(account_number[10:12])

        return {
            'bank_code': bank_code,
            'user_id': user_id,
            'sequence': sequence,
        }
    except ValueError:
        raise ValueError('Invalid account number format')
