import pytest
from app.services.payment_service import (
    generate_payhere_hash,
    verify_payhere_ipn_signature,
    CREDIT_PACKAGES,
)

def test_generate_payhere_hash():
    merchant_id = "1211149"
    order_id = "LANGID-TEST123"
    amount = 2500.0
    currency = "LKR"
    secret = "testsecret123"

    h = generate_payhere_hash(
        merchant_id=merchant_id,
        order_id=order_id,
        amount=amount,
        currency=currency,
        merchant_secret=secret,
    )
    assert isinstance(h, str)
    assert len(h) == 32
    assert h == h.upper()

def test_verify_payhere_ipn_signature_valid_and_invalid():
    merchant_id = "1211149"
    order_id = "LANGID-TEST123"
    payhere_amount = "2500.00"
    payhere_currency = "LKR"
    status_code = "2"
    secret = "testsecret123"

    # Compute expected signature
    import hashlib
    secret_hash = hashlib.md5(secret.encode("utf-8")).hexdigest().upper()
    valid_sig = hashlib.md5(
        f"{merchant_id}{order_id}{payhere_amount}{payhere_currency}{status_code}{secret_hash}".encode("utf-8")
    ).hexdigest().upper()

    # Valid check
    assert verify_payhere_ipn_signature(
        merchant_id=merchant_id,
        order_id=order_id,
        payhere_amount=payhere_amount,
        payhere_currency=payhere_currency,
        status_code=status_code,
        md5sig=valid_sig,
        merchant_secret=secret,
    ) is True

    # Tampered amount
    assert verify_payhere_ipn_signature(
        merchant_id=merchant_id,
        order_id=order_id,
        payhere_amount="999.00",
        payhere_currency=payhere_currency,
        status_code=status_code,
        md5sig=valid_sig,
        merchant_secret=secret,
    ) is False

def test_credit_packages_defined():
    assert "starter" in CREDIT_PACKAGES
    assert "standard" in CREDIT_PACKAGES
    assert "institution" in CREDIT_PACKAGES
    assert CREDIT_PACKAGES["standard"]["popular"] is True
    assert CREDIT_PACKAGES["standard"]["credits"] == 10000.0
