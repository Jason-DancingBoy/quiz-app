async def basic_auth_middleware(request, call_next):
    return await call_next(request)
