import secrets

from fastapi import Request
from starlette.responses import JSONResponse

from backend.config import BASIC_AUTH_USER, BASIC_AUTH_PASS
from backend.logger import get_logger

logger = get_logger(__name__)


async def basic_auth_middleware(request: Request, call_next):
    if request.method == "OPTIONS":
        return await call_next(request)
    if not request.url.path.startswith("/api"):
        return await call_next(request)
    if request.url.path == "/api/health":
        return await call_next(request)

    authorization = request.headers.get("Authorization")
    if not authorization:
        logger.warning("Auth failed: missing Authorization header | path=%s", request.url.path)
        return _unauthorized()

    try:
        scheme, _, credentials = authorization.partition(" ")
        if scheme.lower() != "basic":
            logger.warning("Auth failed: non-Basic scheme '%s' | path=%s", scheme, request.url.path)
            return _unauthorized()

        import base64
        decoded = base64.b64decode(credentials).decode("utf-8")
        username, _, password = decoded.partition(":")

        correct_user = secrets.compare_digest(username, BASIC_AUTH_USER)
        correct_pass = secrets.compare_digest(password, BASIC_AUTH_PASS)

        if not (correct_user and correct_pass):
            logger.warning("Auth failed: invalid credentials for user '%s' | path=%s", username, request.url.path)
            return _unauthorized()
    except Exception as e:
        logger.error("Auth error: %s | path=%s", e, request.url.path)
        return _unauthorized()

    return await call_next(request)


def _unauthorized():
    return JSONResponse(
        status_code=401,
        headers={"WWW-Authenticate": 'Basic realm="Quiz App"'},
        content={"detail": "Unauthorized"},
    )
