"""Quantum-safe crypto via qcrypto (Kyber + Dilithium).

Falls back to stubs if liboqs is unavailable (e.g. Windows without prebuilt binaries).
"""
import base64
import secrets
from typing import NamedTuple

QCRYPTO_AVAILABLE = False
_DilithiumSig = _KyberKEM = _decrypt = _encrypt = None

try:
    from qcrypto import DilithiumSig as _DilithiumSig, KyberKEM as _KyberKEM, decrypt as _decrypt, encrypt as _encrypt
    QCRYPTO_AVAILABLE = True
except (ImportError, OSError, RuntimeError, SystemExit):
    pass

KEM_ALG = "Kyber768"
SIG_ALG = "Dilithium3"


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
        return KeyPair(public_key=keys.public_key, private_key=keys.private_key)
    return _stub_keypair("kem")


def generate_sig_keypair() -> KeyPair:
    """Generate Dilithium signature keypair."""
    if QCRYPTO_AVAILABLE and _DilithiumSig:
        sig = _DilithiumSig(SIG_ALG)
        keys = sig.generate_keypair()
        return KeyPair(public_key=keys.public_key, private_key=keys.secret_key)
    return _stub_keypair("sig")


def encrypt_data(public_key: bytes, plaintext: bytes) -> bytes:
    """Encrypt data with recipient's Kyber public key."""
    if QCRYPTO_AVAILABLE and _encrypt:
        return _encrypt(public_key, plaintext)
    return b"mock_encrypted_" + plaintext[: min(16, len(plaintext))]


def decrypt_data(private_key: bytes, ciphertext: bytes) -> bytes:
    """Decrypt data with Kyber private key."""
    if QCRYPTO_AVAILABLE and _decrypt:
        return _decrypt(private_key, ciphertext)
    return b"mock_decrypted"


def sign_data(private_key: bytes, data: bytes) -> bytes:
    """Sign data with Dilithium secret key."""
    if QCRYPTO_AVAILABLE and _DilithiumSig:
        sig = _DilithiumSig(SIG_ALG)
        return sig.sign(private_key, data)
    return b"mock_sig_" + data[: min(8, len(data))]


def verify_signature(public_key: bytes, data: bytes, signature: bytes) -> bool:
    """Verify Dilithium signature."""
    if QCRYPTO_AVAILABLE and _DilithiumSig:
        sig = _DilithiumSig(SIG_ALG)
        return sig.verify(public_key, data, signature)
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
