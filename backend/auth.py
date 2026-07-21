import secrets

from fastapi import Request, HTTPException

from backend.config import BASIC_AUTH_USER, BASIC_AUTH_PASS


async def basic_auth_middleware(request: Request, call_next):
    # Skip auth for OPTIONS (CORS preflight)
    if request.method == "OPTIONS":
        return await call_next(request)

    authorization = request.headers.get("Authorization")
    if not authorization:
        return _unauthorized()

    try:
        scheme, _, credentials = authorization.partition(" ")
        if scheme.lower() != "basic":
            return _unauthorized()

        import base64
        decoded = base64.b64decode(credentials).decode("utf-8")
        username, _, password = decoded.partition(":")

        correct_user = secrets.compare_digest(username, BASIC_AUTH_USER)
        correct_pass = secrets.compare_digest(password, BASIC_AUTH_PASS)

        if not (correct_user and correct_pass):
            return _unauthorized()
    except Exception:
        return _unauthorized()

    return await call_next(request)


def _unauthorized():
    raise HTTPException(
        status_code=401,
        headers={"WWW-Authenticate": 'Basic realm="Quiz App"'},
        detail="Unauthorized",
    )
