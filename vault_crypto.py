"""Crypto layer: scrypt key derivation + AES-256-GCM. No UI, no file I/O."""
import hashlib, os
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

KDF_DEFAULT = {"n": 2**17, "r": 8, "p": 1}   # ~128 MB RAM, ~0.5 s: slows brute force
AAD = b"securevault-v1"                       # binds ciphertext to this format


class WrongPassword(Exception):
    """Wrong master password (or tampered file: GCM cannot tell them apart)."""


def new_salt() -> bytes:
    return os.urandom(16)


def derive_key(password: str, salt: bytes, kdf: dict) -> bytes:
    return hashlib.scrypt(password.encode("utf-8"), salt=salt, n=kdf["n"], r=kdf["r"],
                          p=kdf["p"], maxmem=2**29, dklen=32)


def encrypt(key: bytes, plaintext: bytes) -> tuple[bytes, bytes]:
    nonce = os.urandom(12)                    # fresh nonce on every save
    return nonce, AESGCM(key).encrypt(nonce, plaintext, AAD)


def decrypt(key: bytes, nonce: bytes, ciphertext: bytes) -> bytes:
    try:
        return AESGCM(key).decrypt(nonce, ciphertext, AAD)
    except InvalidTag as exc:
        raise WrongPassword from exc
