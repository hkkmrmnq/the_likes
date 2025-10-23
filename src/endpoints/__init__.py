from .contacts import router as contacts_router
from .core import router as core_router
from .messages import router as messages_router
from .personal_values import router as values_router
from .profiles import router as profiles_router
from .updates import router as updates_router

__all__ = [
    'core_router',
    'contacts_router',
    'messages_router',
    'profiles_router',
    'values_router',
    'updates_router',
]
