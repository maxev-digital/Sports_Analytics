"""
Encrypted storage for per-user Kalshi API credentials.

Scheme: AES-256-GCM with a per-user key-encryption-key (KEK) derived from a
single master key via PBKDF2-HMAC-SHA256. The master key lives only in this
server's environment (KALSHI_MASTER_KEY) - never committed, never logged,
never shipped to a client.

Each user's row stores: a random nonce, the encrypted API key ID, and the
encrypted private key PEM. GCM's authentication tag is appended to the
ciphertext by the library itself - it is not stored separately.
"""

from __future__ import annotations

import base64
import os
from dataclasses import dataclass

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

_PBKDF2_ITERATIONS = 100_000
_KEY_LEN = 32  # AES-256
_NONCE_LEN = 12  # 96-bit nonce, standard for GCM


@dataclass
class EncryptedCredential:
    nonce_b64: str
    encrypted_api_key_id_b64: str
    encrypted_private_key_b64: str


def _load_master_key() -> bytes:
    """
    Load the 32-byte master key from KALSHI_MASTER_KEY (base64-encoded).

    Raises if unset - unlike the old build, this never silently generates a
    throwaway key, since that key would only ever exist in a log line and
    any credentials encrypted under it become unrecoverable on restart.
    """
    raw = os.environ.get("KALSHI_MASTER_KEY")
    if not raw:
        raise RuntimeError(
            "KALSHI_MASTER_KEY is not set. Generate one with "
            "`python3 -c \"import os,base64; print(base64.b64encode(os.urandom(32)).decode())\"` "
            "and add it to the backend's .env - do not commit it, do not log it."
        )
    key = base64.b64decode(raw)
    if len(key) != _KEY_LEN:
        raise RuntimeError(
            f"KALSHI_MASTER_KEY must decode to {_KEY_LEN} bytes, got {len(key)}."
        )
    return key


def _derive_user_kek(master_key: bytes, username: str) -> bytes:
    """Derive a per-user 32-byte key-encryption-key from the master key."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=_KEY_LEN,
        salt=f"kalshi_user_{username}".encode("utf-8"),
        iterations=_PBKDF2_ITERATIONS,
    )
    return kdf.derive(master_key)


def encrypt_credentials(username: str, api_key_id: str, private_key_pem: str) -> EncryptedCredential:
    """Encrypt a user's Kalshi API key ID + private key PEM for storage."""
    master_key = _load_master_key()
    kek = _derive_user_kek(master_key, username)
    aesgcm = AESGCM(kek)
    nonce = os.urandom(_NONCE_LEN)

    enc_key_id = aesgcm.encrypt(nonce, api_key_id.encode("utf-8"), None)
    enc_private_key = aesgcm.encrypt(nonce, private_key_pem.encode("utf-8"), None)

    return EncryptedCredential(
        nonce_b64=base64.b64encode(nonce).decode("utf-8"),
        encrypted_api_key_id_b64=base64.b64encode(enc_key_id).decode("utf-8"),
        encrypted_private_key_b64=base64.b64encode(enc_private_key).decode("utf-8"),
    )


def decrypt_credentials(username: str, cred: EncryptedCredential) -> tuple[str, str]:
    """Decrypt a user's stored credential row back into (api_key_id, private_key_pem)."""
    master_key = _load_master_key()
    kek = _derive_user_kek(master_key, username)
    aesgcm = AESGCM(kek)
    nonce = base64.b64decode(cred.nonce_b64)

    api_key_id = aesgcm.decrypt(
        nonce, base64.b64decode(cred.encrypted_api_key_id_b64), None
    ).decode("utf-8")
    private_key_pem = aesgcm.decrypt(
        nonce, base64.b64decode(cred.encrypted_private_key_b64), None
    ).decode("utf-8")

    return api_key_id, private_key_pem
