from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from src.config.config import CFG
from src.context import set_current_language


class LanguageMiddleware(BaseHTTPMiddleware):
    """Parses request header and sets current language ContextVar."""

    async def dispatch(self, request: Request, call_next):
        accept_language_header = request.headers.get('accept-language')
        if not accept_language_header:
            set_current_language(CFG.DEFAULT_LANGUAGE)
        else:
            lan_code = accept_language_header.split(',')[0][:2].lower()
            if lan_code in CFG.SUPPORTED_LANGUAGES:
                set_current_language(lan_code)
            else:
                set_current_language(CFG.DEFAULT_LANGUAGE)
        response = await call_next(request)
        return response
