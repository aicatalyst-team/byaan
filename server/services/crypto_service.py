from __future__ import annotations

import base64
import hashlib
import json
import os
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlalchemy.ext.asyncio import AsyncSession

from server.db.session import AsyncSessionFactory
from server.services.settings import SettingsService

# Global cached encryption key
_cached_encryption_key: bytes | None = None


async def get_app_encryption_key(session: AsyncSession | None = None) -> bytes:
    """
    Get the application encryption key, using cached value if available.

    In hosted mode:
    - Uses legacy ENCRYPTION_KEY env var if set (backward compatibility)
    - Otherwise derives 32-byte key from APP_SECRET using SHA-256
    In local mode: Uses encryption key from database settings table (per-tenant, auto-generated)
    """
    global _cached_encryption_key

    if _cached_encryption_key is not None:
        return _cached_encryption_key

    from server.utils.config_loader import get_app_secret, is_self_hosted

    if is_self_hosted():
        # Check for legacy ENCRYPTION_KEY first (backward compatibility)
        env_key = os.getenv("ENCRYPTION_KEY")
        if env_key:
            _cached_encryption_key = bytes.fromhex(env_key)
            return _cached_encryption_key

        # Derive from APP_SECRET using SHA-256 (produces exactly 32 bytes for AES-256)
        app_secret = get_app_secret()
        if app_secret == "change-me-in-production-use-strong-secret":
            raise ValueError("APP_SECRET environment variable must be set in hosted mode")
        _cached_encryption_key = hashlib.sha256(app_secret.encode()).digest()
        return _cached_encryption_key

    # Local mode: use database (per-tenant key, but only one tenant exists)
    if session:
        key = await SettingsService.get_or_create_encryption_key(session)
        _cached_encryption_key = key
        return key
    else:
        async with AsyncSessionFactory() as new_session:
            key = await SettingsService.get_or_create_encryption_key(new_session)
            _cached_encryption_key = key
            return key


def set_encryption_key(key: bytes) -> None:
    """Set the cached encryption key."""
    global _cached_encryption_key
    _cached_encryption_key = key


def clear_encryption_key_cache() -> None:
    """Clear the cached encryption key."""
    global _cached_encryption_key
    _cached_encryption_key = None


class CryptoService:
    """Unified encryption service for all configuration data across the application."""

    @staticmethod
    async def encrypt_config(config_dict: dict[str, Any], session=None) -> str:
        """
        Encrypt a configuration dictionary using AES-GCM.

        Args:
            config_dict: Dictionary to encrypt
            session: Optional database session for key retrieval

        Returns:
            Base64-encoded encrypted data with embedded nonce
        """
        key = await get_app_encryption_key(session)
        aesgcm = AESGCM(key)
        nonce = os.urandom(12)
        plaintext = json.dumps(config_dict).encode("utf-8")
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)
        return base64.b64encode(nonce + ciphertext).decode("utf-8")

    @staticmethod
    async def decrypt_config(b64_blob: str, session=None) -> dict[str, Any]:
        """
        Decrypt a base64-encoded configuration blob using AES-GCM.

        Args:
            b64_blob: Base64-encoded encrypted data with embedded nonce
            session: Optional database session for key retrieval

        Returns:
            Decrypted configuration dictionary
        """
        key = await get_app_encryption_key(session)
        data = base64.b64decode(b64_blob)
        nonce, ciphertext = data[:12], data[12:]
        aesgcm = AESGCM(key)
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        return json.loads(plaintext.decode("utf-8"))
