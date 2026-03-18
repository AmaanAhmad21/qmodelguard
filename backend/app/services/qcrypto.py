"""Quantum-safe crypto via qcrypto (Kyber + Dilithium).

Falls back to stubs if liboqs is unavailable (e.g. Windows without prebuilt binaries).
On Windows we skip importing qcrypto/oqs so liboqs is never auto-installed (branch 0.14.1 is gone).
"""
import base64
import secrets
import sys
from typing import NamedTuple

QCRYPTO_AVAILABLE = False
_DilithiumSig = _KyberKEM = _decrypt = _encrypt = None

if sys.platform != "win32":
    try:
        from qcrypto import (  # type: ignore[import]
            DilithiumSig as _DilithiumSig,
            KyberKEM as _KyberKEM,
            decrypt as _decrypt,
            encrypt as _encrypt,
        )
        QCRYPTO_AVAILABLE = True
    except (ImportError, OSError, RuntimeError, SystemExit):
        pass

# Follow qcrypto 1.0.0 API/docs: Kyber + Dilithium names, but prefer
# the ML-DSA alias when available (your liboqs build supports ML-DSA-65
# and not Dilithium3).
KEM_ALG = "Kyber768"
SIG_ALG_PRIMARY = "ML-DSA-65"
SIG_ALG_FALLBACK = "Dilithium3"

# Backwards-compatible alias used by /health and tests. Expose the
# *effective* signature algorithm the wrapper prefers on this build.
SIG_ALG = SIG_ALG_PRIMARY


class KeyPair(NamedTuple):
    """Keypair with base64-encoded keys."""
    public_key: bytes
    private_key: bytes


def _stub_keypair(prefix: str) -> KeyPair:
    """Generate stub keypair for when qcrypto is unavailable."""
    raw = secrets.token_bytes(32)
    return KeyPair(
        public_key=f"{prefix}_pub_{raw.hex()}".encode(),
        private_key=f"{prefix}_priv_{raw.hex()}".encode(),
    )


def generate_kem_keypair() -> KeyPair:
    """Generate Kyber KEM keypair."""
    if QCRYPTO_AVAILABLE and _KyberKEM:
        kem = _KyberKEM(KEM_ALG)
        keys = kem.generate_keypair()
        # qcrypto's KyberKeypair exposes `public_key` / `private_key` attributes.
        return KeyPair(public_key=keys.public_key, private_key=keys.private_key)
    return _stub_keypair("kem")


def generate_sig_keypair() -> KeyPair:
    """Generate Dilithium/ML-DSA signature keypair.

    Tries ML-DSA-65 first (modern alias), then falls back to Dilithium3 if
    that mechanism is not supported by the current liboqs build.
    """
    if QCRYPTO_AVAILABLE and _DilithiumSig:
        last_exc: Exception | None = None
        for alg in (SIG_ALG_PRIMARY, SIG_ALG_FALLBACK):
            try:
                sig = _DilithiumSig(alg)
                keys = sig.generate_keypair()
                return KeyPair(public_key=keys.public_key, private_key=keys.secret_key)
            except Exception as exc:  # pragma: no cover - depends on liboqs build
                last_exc = exc
                continue
        if last_exc is not None:
            raise last_exc
    return _stub_keypair("sig")


def encrypt_data(public_key: bytes, plaintext: bytes) -> bytes:
    """Encrypt data with recipient's Kyber public key using qcrypto's hybrid API."""
    if QCRYPTO_AVAILABLE and _encrypt:
        return _encrypt(public_key, plaintext)
    return b"mock_encrypted_" + plaintext[: min(16, len(plaintext))]


def decrypt_data(private_key: bytes, ciphertext: bytes) -> bytes:
    """Decrypt data with Kyber private key using qcrypto's hybrid API."""
    if QCRYPTO_AVAILABLE and _decrypt:
        return _decrypt(private_key, ciphertext)
    return b"mock_decrypted"


def sign_data(private_key: bytes, data: bytes) -> bytes:
    """Sign data with ML-DSA/Dilithium secret key."""
    if QCRYPTO_AVAILABLE and _DilithiumSig:
        last_exc: Exception | None = None
        for alg in (SIG_ALG_PRIMARY, SIG_ALG_FALLBACK):
            try:
                sig = _DilithiumSig(alg)
                return sig.sign(private_key, data)
            except Exception as exc:  # pragma: no cover - depends on liboqs build
                last_exc = exc
                continue
        if last_exc is not None:
            raise last_exc
    return b"mock_sig_" + data[: min(8, len(data))]


def verify_signature(public_key: bytes, data: bytes, signature: bytes) -> bool:
    """Verify Dilithium signature."""
    if QCRYPTO_AVAILABLE and _DilithiumSig:
        for alg in (SIG_ALG_PRIMARY, SIG_ALG_FALLBACK):
            try:
                sig = _DilithiumSig(alg)
                return sig.verify(public_key, data, signature)
            except Exception:  # pragma: no cover - depends on liboqs build
                continue
        return False
    return True


def keys_to_base64(kp: KeyPair) -> tuple[str, str]:
    """Serialize keypair to base64 strings."""
    pub_b64 = base64.b64encode(kp.public_key).decode("ascii")
    priv_b64 = base64.b64encode(kp.private_key).decode("ascii")
    return pub_b64, priv_b64


def base64_to_keys(pub_b64: str, priv_b64: str) -> KeyPair:
    """Deserialize keypair from base64 strings."""
    return KeyPair(
        public_key=base64.b64decode(pub_b64),
        private_key=base64.b64decode(priv_b64),
    )
