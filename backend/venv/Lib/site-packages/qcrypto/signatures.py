from dataclasses import dataclass
import oqs
import ctypes as ct

# Existing Dilithium specific API (kept for backwards compatibility)

@dataclass
class DilithiumKeypair:
    public_key: bytes
    secret_key: bytes


class DilithiumSig:
    """
    Thin wrapper around liboqs Dilithium signatures.

    Example:
        sig = DilithiumSig("Dilithium3")
        kp = sig.generate_keypair()
        signature = sig.sign(kp.secret_key, b"message")
        ok = sig.verify(kp.public_key, b"message", signature)
    """

    def __init__(self, alg: str = "Dilithium3"):
        self.alg = alg

    def generate_keypair(self) -> DilithiumKeypair:
        with oqs.Signature(self.alg) as sig:
            public_key = sig.generate_keypair()
            secret_key = sig.export_secret_key()
            return DilithiumKeypair(public_key, secret_key)

    def sign(self, secret_key: bytes, message: bytes) -> bytes:
        with oqs.Signature(self.alg) as signer:
            # Load the secret key into the underlying liboqs struct
            sk_len = signer._sig.contents.length_secret_key
            sk_buf = (ct.c_ubyte * sk_len)(*secret_key)
            signer.secret_key = sk_buf
            return signer.sign(message)

    def verify(self, public_key: bytes, message: bytes, signature: bytes) -> bool:
        with oqs.Signature(self.alg) as verifier:
            return verifier.verify(message, signature, public_key)


# New unified signature API

@dataclass
class SignatureKeypair:
    """
    Generic keypair for any liboqs signature algorithm:
    Falcon, SPHINCS+, Dilithium, etc.
    """
    public_key: bytes
    secret_key: bytes


class SignatureScheme:
    """
    Generic wrapper for any liboqs signature algorithm.

    You can pass any algorithm name that your liboqs build supports, for example:
      - "Dilithium2", "Dilithium3", "Dilithium5"
      - "Falcon-512", "Falcon-1024"
      - "SPHINCS+-SHA2-128f-simple", etc.

    Example:
        sig = SignatureScheme("Falcon-512")
        kp = sig.generate_keypair()
        sig_bytes = sig.sign(kp.secret_key, b"hello")
        assert sig.verify(kp.public_key, b"hello", sig_bytes)
    """

    def __init__(self, alg: str):
        self.alg = alg

    def generate_keypair(self) -> SignatureKeypair:
        with oqs.Signature(self.alg) as sig:
            public_key = sig.generate_keypair()
            secret_key = sig.export_secret_key()
            return SignatureKeypair(public_key, secret_key)

    def sign(self, secret_key: bytes, message: bytes) -> bytes:
        with oqs.Signature(self.alg) as signer:
            sk_len = signer._sig.contents.length_secret_key
            sk_buf = (ct.c_ubyte * sk_len)(*secret_key)
            signer.secret_key = sk_buf
            return signer.sign(message)

    def verify(self, public_key: bytes, message: bytes, signature: bytes) -> bool:
        with oqs.Signature(self.alg) as verifier:
            return verifier.verify(message, signature, public_key)


class FalconSig(SignatureScheme):
    """
    Convenience wrapper for Falcon signatures.

    Default variant is "Falcon-512". You can pass
    "Falcon-1024" or one of the padded variants if your
    liboqs build enables them.
    """

    def __init__(self, variant: str = "Falcon-512"):
        super().__init__(alg=variant)


class SphincsSig(SignatureScheme):
    """
    Convenience wrapper for SPHINCS+ signatures.

    Default variant is "SPHINCS+-SHA2-128f-simple", which is one
    of the liboqs SPHINCS+ parameter sets. You can override with
    any other SPHINCS+ algorithm string supported by liboqs, such as
    "SPHINCS+-SHA2-256s-simple" or "SPHINCS+-SHAKE-128f-simple".
    """

    def __init__(self, variant: str = "SPHINCS+-SHA2-128f-simple"):
        super().__init__(alg=variant)
