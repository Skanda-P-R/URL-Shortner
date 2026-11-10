import secrets

BASE62_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
BASE = len(BASE62_ALPHABET)  # 62

# Limits for 64-bit signed integer (PostgreSQL BIGINT max is 2^63 - 1)
# 62^6 ensures at least 7 characters in Base62
MIN_ID = 62**6  # 56,800,235,584
MAX_ID = (1 << 62) - 1  # 4,611,686,018,427,387,903


def encode_base62(num: int) -> str:
    """
    Encodes a positive integer into a Base62 string.
    """
    if num < 0:
        raise ValueError("Cannot encode negative integers to Base62.")
    if num == 0:
        return BASE62_ALPHABET[0]

    digits = []
    while num > 0:
        rem = num % BASE
        digits.append(BASE62_ALPHABET[rem])
        num //= BASE

    return "".join(reversed(digits))


def decode_base62(code: str) -> int:
    """
    Decodes a Base62 string back into an integer.
    """
    if not code:
        raise ValueError("Cannot decode an empty Base62 string.")

    num = 0
    for char in code:
        idx = BASE62_ALPHABET.find(char)
        if idx == -1:
            raise ValueError(f"Invalid character '{char}' in Base62 string.")
        num = num * BASE + idx

    return num


def generate_non_sequential_id(min_val: int = MIN_ID, max_val: int = MAX_ID) -> int:
    """
    Generates a cryptographically secure non-sequential random integer.
    Fits comfortably inside a PostgreSQL BIGINT column (up to 2^63 - 1).
    Produces Base62 slugs of length 7-11 characters.
    """
    span = max_val - min_val + 1
    return min_val + secrets.randbelow(span)
