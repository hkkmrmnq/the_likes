import threading

from .constants import LANGUAGE_DEFAULT

_request_context = threading.local()


def set_current_language(language_code: str):
    _request_context.language_code = language_code


def get_current_language() -> str:
    return getattr(_request_context, 'language_code', LANGUAGE_DEFAULT)
