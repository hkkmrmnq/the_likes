import threading

from .config import constants as CNST

_request_context = threading.local()


def set_current_language(language_code: str):
    _request_context.language_code = language_code


def get_current_language() -> str:
    return getattr(_request_context, 'language_code', CNST.LANGUAGE_DEFAULT)
