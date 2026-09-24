import pytest
from fastapi import HTTPException
from passlib.context import CryptContext

from backend.auth import validate_password


@pytest.mark.parametrize(
    'password',
    ['short', 'lowercase123', 'UPPERCASE123', 'NoNumber', 'nouppercase123']
)
def test_validate_password_rejects_weak_passwords(password):
    with pytest.raises(HTTPException):
        validate_password(password)


def test_validate_password_allows_strong_password():
    assert validate_password('TestPass123') == 'TestPass123'


def test_bcrypt_can_hash_and_verify_strong_password():
    password = 'StrongPass456'
    ctx = CryptContext(schemes=['bcrypt'], deprecated='auto')
    hashed = ctx.hash(password)
    assert ctx.verify(password, hashed)


def test_validate_password_rejects_password_over_72_bytes():
    long_password = 'A' * 73
    with pytest.raises(HTTPException):
        validate_password(long_password)
