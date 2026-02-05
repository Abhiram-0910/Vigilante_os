from fastapi import Security
from fastapi.security import APIKeyHeader
from app.core.config import SETTINGS

api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)


class InvalidAPIKeyError(Exception):
    """Raised when API key is missing or wrong. Never log the key."""
    pass


async def get_api_key(api_key: str = Security(api_key_header)):
    print(f"DEBUG: Received API Key: '{api_key}'")
    print(f"DEBUG: Expected API Key: '{SETTINGS.VIBHISHAN_API_KEY}'")
    if not api_key or api_key != SETTINGS.VIBHISHAN_API_KEY:
        raise InvalidAPIKeyError()
    return api_key