"""
AES-256-GCM authenticated encryption for sensitive credentials.

Storage format: base64( nonce[12] + ciphertext + tag[16] )
The GCM tag is appended automatically by the AESGCM primitive.
"""

import os
import json
import base64
from typing import Any, Dict

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def _get_key(raw_hex: str) -> bytes:
    """Decode hex key and validate it is exactly 32 bytes (256-bit)."""
    key = bytes.fromhex(raw_hex)
    if len(key) != 32:
        raise ValueError("ENCRYPTION_KEY must be a 64-character hex string (32 bytes / 256-bit)")
    return key


def encrypt_credentials(data: Dict[str, Any], key_hex: str) -> str:
    """
    Encrypt a credentials dict with AES-256-GCM.
    Returns a base64-encoded string safe for database storage.
    """
    key = _get_key(key_hex)
    nonce = os.urandom(12)          # 96-bit random nonce — unique per encryption
    aesgcm = AESGCM(key)
    plaintext = json.dumps(data, separators=(",", ":")).encode()
    ciphertext = aesgcm.encrypt(nonce, plaintext, None)   # includes 16-byte GCM tag
    return base64.b64encode(nonce + ciphertext).decode()


def decrypt_credentials(encrypted: str, key_hex: str) -> Dict[str, Any]:
    """
    Decrypt a credentials blob produced by encrypt_credentials.
    Raises ValueError / InvalidTag if tampered or wrong key.
    """
    key = _get_key(key_hex)
    raw = base64.b64decode(encrypted)
    if len(raw) < 28:               # 12-byte nonce + at least 16-byte tag
        raise ValueError("Invalid encrypted credentials: payload too short")
    nonce, ciphertext = raw[:12], raw[12:]
    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    return json.loads(plaintext)


def generate_key() -> str:
    """Generate a fresh 256-bit key as a hex string (use once, store safely)."""
    return os.urandom(32).hex()
