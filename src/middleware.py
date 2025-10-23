from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from src.config import constants as CNST
from src.context import set_current_language


class LanguageMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        accept_language_header = request.headers.get('accept-language')
        if not accept_language_header:
            set_current_language(CNST.LANGUAGE_DEFAULT)
        else:
            lan_code = accept_language_header.split(',')[0][:2].lower()
            if lan_code in CNST.SUPPORTED_LANGUAGES:
                set_current_language(lan_code)
            else:
                set_current_language(CNST.LANGUAGE_DEFAULT)
        response = await call_next(request)
        return response
