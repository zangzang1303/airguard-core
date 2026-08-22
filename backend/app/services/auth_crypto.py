from __future__ import annotations

import hashlib
import re
import secrets

import argon2

# Argon2id hasher configured for web security and memory hardness
_hasher = argon2.PasswordHasher(
    time_cost=2,
    memory_cost=65536,
    parallelism=2,
    hash_len=32,
    type=argon2.Type.ID,
)

# Pre-computed dummy hash to prevent timing attacks during user lookup failure
_DUMMY_HASH = _hasher.hash("AirGuard@TimingProtection2026")


def hash_password(password: str) -> str:
    """Hash a plaintext password with Argon2id."""
    if len(password) > 1024:
        raise ValueError("Password exceeds maximum allowed length.")
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str | None) -> bool:
    """Verify a plaintext password against an Argon2id hash."""
    if not password_hash or len(password) > 1024:
        return False
    try:
        return _hasher.verify(password_hash, password)
    except (argon2.exceptions.VerifyMismatchError, argon2.exceptions.InvalidHashError):
        return False
    except Exception:
        return False


def dummy_verify_password() -> bool:
    """Perform a constant-time dummy verification."""
    try:
        _hasher.verify(_DUMMY_HASH, "incorrect_dummy_attempt")
    except Exception:
        pass
    return False


def generate_token() -> str:
    """Generate a high-entropy CSPRNG raw token (URL-safe)."""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """Compute the SHA-256 hash of a raw token for safe database persistence."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest().lower()


def normalize_email(email: str) -> str:
    """Trim whitespace and lowercase email."""
    return email.strip().lower()


def is_valid_email(email: str) -> bool:
    """Basic structural validation for email."""
    normalized = normalize_email(email)
    if len(normalized) < 5 or len(normalized) > 200:
        return False
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return bool(re.match(pattern, normalized))
