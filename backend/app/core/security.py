from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from typing import Any


PASSWORD_ALGORITHM = "pbkdf2_sha256"
PASSWORD_ITERATIONS = 390000


def hash_password(password: str) -> str:
    """
    Genera hash seguro de contraseña usando librerías estándar de Python.

    Formato:
    pbkdf2_sha256$iteraciones$salt$hash
    """
    if not password:
        raise ValueError("La contraseña no puede estar vacía.")

    salt = secrets.token_bytes(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PASSWORD_ITERATIONS,
    )

    salt_b64 = base64.b64encode(salt).decode("utf-8")
    hash_b64 = base64.b64encode(password_hash).decode("utf-8")

    return f"{PASSWORD_ALGORITHM}${PASSWORD_ITERATIONS}${salt_b64}${hash_b64}"


def verify_password(password: str, stored_hash: str | None) -> bool:
    """
    Verifica contraseña contra hash almacenado.
    """
    if not password or not stored_hash:
        return False

    try:
        algorithm, iterations_text, salt_b64, hash_b64 = stored_hash.split("$", 3)

        if algorithm != PASSWORD_ALGORITHM:
            return False

        iterations = int(iterations_text)
        salt = base64.b64decode(salt_b64.encode("utf-8"))
        expected_hash = base64.b64decode(hash_b64.encode("utf-8"))

        candidate_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            iterations,
        )

        return hmac.compare_digest(candidate_hash, expected_hash)

    except Exception:
        return False


def generate_random_password(length: int = 16) -> str:
    """
    Genera contraseña temporal segura.
    """
    if length < 12:
        length = 12

    return secrets.token_urlsafe(length)[:length]


def _get_auth_secret_key() -> str:
    secret_key = os.getenv("AUTH_SECRET_KEY")

    if secret_key:
        return secret_key

    return "dev-secret-key-change-me"


def _get_token_minutes() -> int:
    value = os.getenv("AUTH_ACCESS_TOKEN_MINUTES", "480")

    try:
        return int(value)
    except ValueError:
        return 480


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)

    return base64.urlsafe_b64decode((data + padding).encode("utf-8"))


def create_access_token(payload: dict[str, Any], expires_minutes: int | None = None) -> str:
    """
    Crea token tipo JWT HS256 usando librerías estándar.
    """
    if expires_minutes is None:
        expires_minutes = _get_token_minutes()

    header = {
        "alg": "HS256",
        "typ": "JWT",
    }

    now = int(time.time())

    token_payload = {
        **payload,
        "iat": now,
        "exp": now + expires_minutes * 60,
    }

    encoded_header = _b64url_encode(
        json.dumps(header, separators=(",", ":")).encode("utf-8")
    )
    encoded_payload = _b64url_encode(
        json.dumps(token_payload, separators=(",", ":"), default=str).encode("utf-8")
    )

    signing_input = f"{encoded_header}.{encoded_payload}"

    signature = hmac.new(
        _get_auth_secret_key().encode("utf-8"),
        signing_input.encode("utf-8"),
        hashlib.sha256,
    ).digest()

    encoded_signature = _b64url_encode(signature)

    return f"{signing_input}.{encoded_signature}"


def decode_access_token(token: str) -> dict[str, Any]:
    """
    Valida y decodifica token tipo JWT HS256.
    """
    try:
        encoded_header, encoded_payload, encoded_signature = token.split(".", 2)

        signing_input = f"{encoded_header}.{encoded_payload}"

        expected_signature = hmac.new(
            _get_auth_secret_key().encode("utf-8"),
            signing_input.encode("utf-8"),
            hashlib.sha256,
        ).digest()

        received_signature = _b64url_decode(encoded_signature)

        if not hmac.compare_digest(expected_signature, received_signature):
            raise ValueError("Firma inválida.")

        header = json.loads(_b64url_decode(encoded_header).decode("utf-8"))

        if header.get("alg") != "HS256":
            raise ValueError("Algoritmo de token inválido.")

        payload = json.loads(_b64url_decode(encoded_payload).decode("utf-8"))

        exp = int(payload.get("exp", 0))

        if exp < int(time.time()):
            raise ValueError("Token expirado.")

        return payload

    except Exception as exc:
        raise ValueError("Token inválido.") from exc