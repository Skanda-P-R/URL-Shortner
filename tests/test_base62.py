import pytest
from app.core.base62 import (
    BASE62_ALPHABET,
    decode_base62,
    encode_base62,
    generate_non_sequential_id,
    MIN_ID,
    MAX_ID,
)


def test_encode_decode_zero():
    encoded = encode_base62(0)
    assert encoded == "0"
    assert decode_base62("0") == 0


def test_encode_decode_positive_integers():
    numbers = [1, 61, 62, 100, 1234567, 9876543210, 2**48, 2**60]
    for num in numbers:
        encoded = encode_base62(num)
        # All characters must be in the base62 alphabet
        assert all(c in BASE62_ALPHABET for c in encoded)
        # Bijective property: decoding must produce the exact original number
        assert decode_base62(encoded) == num


def test_encode_negative_raises():
    with pytest.raises(ValueError):
        encode_base62(-1)


def test_decode_invalid_character_raises():
    with pytest.raises(ValueError):
        decode_base62("abc#123")


def test_decode_empty_string_raises():
    with pytest.raises(ValueError):
        decode_base62("")


def test_generate_non_sequential_id():
    id1 = generate_non_sequential_id()
    id2 = generate_non_sequential_id()

    # Must be within bounds
    assert MIN_ID <= id1 <= MAX_ID
    assert MIN_ID <= id2 <= MAX_ID

    # Must not be sequential
    assert id1 != id2
    assert abs(id1 - id2) != 1

    # Base62 representation should be non-trivial length (>= 7 chars)
    slug1 = encode_base62(id1)
    slug2 = encode_base62(id2)
    assert len(slug1) >= 7
    assert len(slug2) >= 7
