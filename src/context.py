from contextvars import ContextVar

from src.config import constants as CNST

_current_language: ContextVar[str] = ContextVar(
    'current_language', default=CNST.LANGUAGE_DEFAULT
)


def set_current_language(language_code: str) -> None:
    _current_language.set(language_code)


def get_current_language() -> str:
    return _current_language.get()
