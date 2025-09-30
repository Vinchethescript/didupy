import os
import base64
import hashlib

from typing import Tuple, Union
from aiohttp import ClientResponse

DidUPyResponse = Tuple[Union[dict, str], ClientResponse]


def generate_22byte_b64_string() -> str:
    """Generate a URL-safe base64-encoded string of 22 bytes."""
    return base64.urlsafe_b64encode(os.urandom(22)).rstrip(b"=").decode("utf-8")


def get_pkce_pair() -> tuple[str, str]:
    """Generate a PKCE code verifier and its corresponding code challenge."""

    # 44 bytes
    code_verifier = generate_22byte_b64_string() + generate_22byte_b64_string()
    code_challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode("utf-8")).digest())
        .rstrip(b"=")
        .decode("utf-8")
    )
    return code_verifier, code_challenge
