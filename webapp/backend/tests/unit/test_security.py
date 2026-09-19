import pytest
from datetime import timedelta, datetime, timezone
from jose import jwt, JWTError
from app.utils.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
)
from app.config import settings

def test_password_hashing_creates_unique_salts():
    """Verify that hashing the same password twice produces distinct salt hashes."""
    pwd = "SecurePassword123!"
    hash1 = get_password_hash(pwd)
    hash2 = get_password_hash(pwd)
    
    assert hash1 != hash2
    assert hash1.startswith("$2b$") or hash1.startswith("$2a$")
    assert hash2.startswith("$2b$") or hash2.startswith("$2a$")

def test_verify_password_success_and_failure():
    """Verify password verification matches valid credentials and rejects incorrect ones."""
    pwd = "CorrectHorseBatteryStaple"
    hashed = get_password_hash(pwd)
    
    assert verify_password(pwd, hashed) is True
    assert verify_password("WrongPassword", hashed) is False
    assert verify_password("", hashed) is False
    assert verify_password(pwd.lower(), hashed) is False

def test_create_access_token_claims_and_default_expiration():
    """Verify access token payload contains required claims and valid default expiration."""
    user_id = "test-user-uuid-12345"
    token = create_access_token(subject=user_id)
    
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert payload["sub"] == user_id
    assert payload["type"] == "access"
    assert "exp" in payload
    
    # Check that expiration is roughly in the future by ACCESS_TOKEN_EXPIRE_MINUTES
    exp_dt = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    now = datetime.now(timezone.utc)
    delta_minutes = (exp_dt - now).total_seconds() / 60
    assert 0 < delta_minutes <= settings.ACCESS_TOKEN_EXPIRE_MINUTES + 1

def test_create_access_token_custom_delta():
    """Verify access token respects custom expiration delta."""
    user_id = "custom-delta-user"
    token = create_access_token(subject=user_id, expires_delta=timedelta(minutes=45))
    
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    exp_dt = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    now = datetime.now(timezone.utc)
    delta_minutes = (exp_dt - now).total_seconds() / 60
    assert 40 < delta_minutes <= 46

def test_create_refresh_token():
    """Verify refresh token payload type claim and multi-day expiration."""
    user_id = "refresh-user-uuid"
    token = create_refresh_token(subject=user_id)
    
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert payload["sub"] == user_id
    assert payload["type"] == "refresh"
    assert "exp" in payload

def test_tampered_token_fails_decoding():
    """Verify that tampering with token signature raises JWTError."""
    token = create_access_token(subject="user-tamper-test")
    tampered = token[:-4] + "abcd"
    
    with pytest.raises(JWTError):
        jwt.decode(tampered, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

def test_token_with_wrong_secret_key_fails():
    """Verify that decoding with an invalid secret key fails."""
    token = create_access_token(subject="user-wrong-key")
    with pytest.raises(JWTError):
        jwt.decode(token, "wrong_secret_key_1234567890", algorithms=[settings.ALGORITHM])
