from typing import Any

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    detail: str
    extra: dict[str, Any] | None = None


COMMON_RESPONSES = {
    400: {
        'model': ErrorResponse,
        # 'description': 'Incorrect body structure.',
        'content': {
            'application/json': {
                'example': {'detail': 'Incorrect body structure.'}
            }
        },
    },
    401: {
        'model': ErrorResponse,
        # 'description': 'Unauthorized / inactive account.',
        'content': {
            'application/json': {
                'example': {'detail': 'Unauthorized / inactive account.'}
            }
        },
    },
    403: {
        'model': ErrorResponse,
        # 'description': 'Unverified',
        'content': {'application/json': {'example': {'detail': 'Unverified'}}},
    },
    404: {
        # 'description': 'Requested item not found'
        'model': ErrorResponse,
        'content': {
            'application/json': {
                'example': {'detail': 'Requested item not found'}
            }
        },
    },
    409: {
        # 'description': 'Item(s) already exist(s).'
        'model': ErrorResponse,
        'content': {
            'application/json': {
                'example': {'detail': 'Item(s) already exist(s).'}
            }
        },
    },
    500: {
        # 'description': 'Something went wrong.'
        'model': ErrorResponse,
        'content': {
            'application/json': {
                'example': {'detail': 'Something went wrong.'}
            }
        },
    },
}
