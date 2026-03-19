from dataclasses import dataclass
from typing import Tuple
import oqs
import ctypes as ct
import base64
from pathlib import Path


@dataclass
class KyberKeypair:
    public_key: bytes
    private_key: bytes


class KyberKEM:
    def __init__(self, alg: str = "Kyber768"):
        self.alg = alg
        self._private_key = None
        self._public_key = None

    def generate_keypair(self) -> KyberKeypair:
        with oqs.KeyEncapsulation(self.alg) as kem:
            public_key = kem.generate_keypair()
            private_key = kem.export_secret_key()
            self._public_key = public_key
            self._private_key = private_key
            return KyberKeypair(public_key, private_key)

    def encapsulate(self, public_key: bytes) -> Tuple[bytes, bytes]:
        with oqs.KeyEncapsulation(self.alg) as kem:
            ct, ss = kem.encap_secret(public_key)
            return ct, ss

    def decapsulate(self, ciphertext: bytes, private_key: bytes = None) -> bytes:
        # Choose which key to use
        if private_key is None:
            if self._private_key is None:
                raise ValueError(
                    "No private key provided. Pass one in or call generate_keypair() first."
                )
            private_key = self._private_key

        with oqs.KeyEncapsulation(self.alg) as kem:
            kem.generate_keypair()

            sk_len = kem._kem.contents.length_secret_key
            sk_buf = (ct.c_ubyte * sk_len)(*private_key)

            kem.secret_key = sk_buf

            return kem.decap_secret(ciphertext)

    # ---- Key Serialization

    @staticmethod
    def _encode(data: bytes, encoding: str) -> bytes:
        if encoding == "raw":
            return data
        elif encoding == "base64":
            return base64.b64encode(data)
        else:
            raise ValueError("encoding must be 'raw' or 'base64'")

    @staticmethod
    def _decode(data: bytes, encoding: str) -> bytes:
        if encoding == "raw":
            return data
        elif encoding == "base64":
            return base64.b64decode(data)
        else:
            raise ValueError("encoding must be 'raw' or 'base64'")

    def save_public_key(self, path="public.key", encoding="raw"):
        if self._public_key is None:
            raise ValueError("Generate a keypair first.")
        Path(path).write_bytes(self._encode(self._public_key, encoding))

    def save_private_key(self, path="private.key", encoding="raw"):
        if self._private_key is None:
            raise ValueError("Generate a keypair first.")
        Path(path).write_bytes(self._encode(self._private_key, encoding))

    @staticmethod
    def load_public_key(path="public.key", encoding="raw"):
        data = Path(path).read_bytes()
        return KyberKEM._decode(data, encoding)

    @staticmethod
    def load_private_key(path="private.key", encoding="raw"):
        data = Path(path).read_bytes()
        return KyberKEM._decode(data, encoding)

class ClassicMcElieceKEM(KyberKEM):
    """
    Classic McEliece KEM wrapper.

    Classic McEliece is provided by liboqs as a KEM, with algorithm
    names such as:

        "Classic-McEliece-348864"
        "Classic-McEliece-348864f"
        "Classic-McEliece-460896"
        "Classic-McEliece-460896f"
        "Classic-McEliece-6688128"
        "Classic-McEliece-6688128f"
        "Classic-McEliece-6960119"
        "Classic-McEliece-6960119f"
        "Classic-McEliece-8192128"
        "Classic-McEliece-8192128f"

    Default here is the 128 bit security level parameter set
    "Classic-McEliece-348864". You can override it by passing any
    other Classic McEliece algorithm string supported by your liboqs build.
    """

    def __init__(self, alg: str = "Classic-McEliece-348864"):
        super().__init__(alg=alg)
