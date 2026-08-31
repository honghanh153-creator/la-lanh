import base64
import hmac
import os
from typing import Protocol

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class EnvelopeCipher(Protocol):
    """Encryption boundary; a KMS-backed implementation can replace the local key adapter."""

    def encrypt(self, plaintext: bytes, *, context: bytes) -> str: ...

    def decrypt(self, envelope: str, *, context: bytes) -> bytes: ...


class DataKeyProvider(Protocol):
    """Production KMS boundary for obtaining versioned data-encryption keys."""

    def active_key(self) -> tuple[str, bytes]: ...

    def key_for_version(self, version: str) -> bytes: ...


class StaticDataKeyProvider:
    """Single-key provider for local development and secret-managed deployments."""

    def __init__(self, key: bytes, *, version: str = "local-v1") -> None:
        if len(key) != 32:
            raise ValueError("AES-256 data key must contain exactly 32 bytes")
        self._key = key
        self._version = version

    def active_key(self) -> tuple[str, bytes]:
        return self._version, self._key

    def key_for_version(self, version: str) -> bytes:
        if version != self._version:
            raise ValueError("unknown encryption key version")
        return self._key


class AesGcmEnvelopeCipher:
    def __init__(self, provider: DataKeyProvider) -> None:
        self._provider = provider

    def encrypt(self, plaintext: bytes, *, context: bytes) -> str:
        version, key = self._provider.active_key()
        nonce = os.urandom(12)
        ciphertext = AESGCM(key).encrypt(nonce, plaintext, context)
        payload = base64.urlsafe_b64encode(nonce + ciphertext).decode().rstrip("=")
        return f"aesgcm:{version}:{payload}"

    def decrypt(self, envelope: str, *, context: bytes) -> bytes:
        algorithm, version, payload = envelope.split(":", 2)
        if algorithm != "aesgcm":
            raise ValueError("unsupported encryption envelope")
        padded = payload + "=" * (-len(payload) % 4)
        packed = base64.urlsafe_b64decode(padded)
        if len(packed) < 29:
            raise ValueError("invalid encryption envelope")
        return AESGCM(self._provider.key_for_version(version)).decrypt(
            packed[:12], packed[12:], context
        )


class SecretHasher:
    """Domain-separated keyed hashes for database lookups and proof verification."""

    def __init__(self, key: bytes) -> None:
        if len(key) < 32:
            raise ValueError("hash key must contain at least 32 bytes")
        self._key = key

    def digest(self, domain: str, value: str) -> bytes:
        return hmac.digest(self._key, domain.encode() + b"\x00" + value.encode(), "sha256")

    def verify(self, domain: str, value: str, expected: bytes) -> bool:
        return hmac.compare_digest(self.digest(domain, value), expected)


def decode_key(encoded: str, *, expected_bytes: int | None = None) -> bytes:
    padded = encoded + "=" * (-len(encoded) % 4)
    try:
        key = base64.urlsafe_b64decode(padded.encode())
    except (ValueError, TypeError) as exc:
        raise ValueError("key must be URL-safe base64") from exc
    if expected_bytes is not None and len(key) != expected_bytes:
        raise ValueError(f"key must decode to exactly {expected_bytes} bytes")
    return key
