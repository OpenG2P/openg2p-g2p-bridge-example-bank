from typing import Any

from jose import jwt


def create_jwt_token(
    payload: dict[str, Any], private_key: str, detatched_jwt: bool = True
) -> str:
    headers = {"alg": "RS256", "typ": "JWT"}
    token = jwt.encode(payload, private_key, algorithm="RS256", headers=headers)

    if detatched_jwt:
        return detach_payload_from_jwt(token)

    return token


def detach_payload_from_jwt(token: str) -> str:
    jwt_header_b64, _, jwt_signature_b64 = token.split(".")
    detached_jwt = f"{jwt_header_b64}..{jwt_signature_b64}"

    return detached_jwt
