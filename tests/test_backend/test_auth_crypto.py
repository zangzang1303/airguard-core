from __future__ import annotations

import sys
from pathlib import Path

BACKEND_PATH = Path(__file__).resolve().parents[2] / "backend"
sys.path.insert(0, str(BACKEND_PATH))

from app.services.auth_crypto import (  # noqa: E402
    dummy_verify_password,
    generate_token,
    hash_password,
    hash_token,
    is_valid_email,
    normalize_email,
    verify_password,
)


def test_password_hashing_and_verification() -> None:
    password = "AirGuard@SuperSecure2026!"
    hashed = hash_password(password)

    assert hashed.startswith("$argon2id$")
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword123!", hashed) is False
    assert verify_password("", hashed) is False
    assert verify_password(password, None) is False
    assert verify_password(password, "invalid_hash_string") is False


def test_dummy_verification_returns_false() -> None:
    assert dummy_verify_password() is False


def test_token_generation_and_hashing() -> None:
    token1 = generate_token()
    token2 = generate_token()

    assert len(token1) >= 32
    assert token1 != token2

    hash1 = hash_token(token1)
    hash2 = hash_token(token1)
    hash_other = hash_token(token2)

    assert len(hash1) == 64
    assert hash1 == hash2
    assert hash1 != hash_other
    assert hash1 == hash1.lower()


def test_email_normalization_and_validation() -> None:
    raw = "  Resident.AirGuard+Test@VinUni.Edu.VN  "
    assert normalize_email(raw) == "resident.airguard+test@vinuni.edu.vn"

    assert is_valid_email("user@vinuni.edu.vn") is True
    assert is_valid_email("admin.ops@airguard.local") is True
    assert is_valid_email("invalid_email") is False
    assert is_valid_email("@no-user.com") is False
    assert is_valid_email("user@") is False
    assert is_valid_email("") is False
