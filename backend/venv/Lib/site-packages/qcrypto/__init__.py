"""
qcrypto: Post-quantum cryptography for Python.

Provides:
- Kyber KEM key generation, encapsulation, and decapsulation
- Classic McEliece KEM support
- Dilithium, Falcon, and SPHINCS+ digital signatures
- Generic SignatureScheme wrapper for any liboqs signature algorithm
- Hybrid PQC + AES GCM authenticated encryption
- High level encrypt() and decrypt() using Kyber768 + HKDF + AES GCM
"""

from .kem import KyberKEM, KyberKeypair, ClassicMcElieceKEM
from .signatures import (
    DilithiumSig,
    DilithiumKeypair,
    SignatureScheme,
    SignatureKeypair,
    FalconSig,
    SphincsSig,
)
from .hybrid import (
    encrypt,
    decrypt,
    encrypt_for_recipient,
    decrypt_from_sender,
    encrypt_file,
    decrypt_file,
)

__all__ = [
    # KEMs
    "KyberKEM",
    "KyberKeypair",
    "ClassicMcElieceKEM",

    # Signatures
    "DilithiumSig",
    "DilithiumKeypair",
    "SignatureScheme",
    "SignatureKeypair",
    "FalconSig",
    "SphincsSig",

    # High level hybrid encryption
    "encrypt",
    "decrypt",

    # File helpers (v0.4)
    "encrypt_file",
    "decrypt_file",

    # Legacy v0.1 API
    "encrypt_for_recipient",
    "decrypt_from_sender",
]

