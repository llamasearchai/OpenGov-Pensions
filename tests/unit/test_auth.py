import pytest
from opengovpension.security.auth import hash_password, verify_password, create_access_token, decode_token

def test_password_hash_and_verify():
    pw = "secret123"
    hashed = hash_password(pw)
    assert hashed != pw
    assert verify_password(pw, hashed)

def test_jwt_create_and_decode():
    token = create_access_token("user123")
    data = decode_token(token)
    assert data['sub'] == 'user123'
