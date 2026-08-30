from typing import Any

from pydantic import BaseModel


class ErrorResponseSchema(BaseModel):
    detail: str
    extra: dict[str, Any] | None = None


COMMON_RESPONSES = {
    400: {
        'model': ErrorResponseSchema,
        'content': {
            'application/json': {
                'example': {'detail': 'Incorrect body structure.'}
            }
        },
    },
    401: {
        'model': ErrorResponseSchema,
        'content': {
            'application/json': {
                'example': {'detail': 'Unauthorized / inactive account.'}
            }
        },
    },
    403: {
        'model': ErrorResponseSchema,
        'content': {'application/json': {'example': {'detail': 'Unverified'}}},
    },
    404: {
        'model': ErrorResponseSchema,
        'content': {
            'application/json': {
                'example': {'detail': 'Requested item not found'}
            }
        },
    },
    409: {
        'model': ErrorResponseSchema,
        'content': {
            'application/json': {
                'example': {'detail': 'Item(s) already exist(s).'}
            }
        },
    },
    500: {
        'model': ErrorResponseSchema,
        'content': {
            'application/json': {
                'example': {'detail': 'Something went wrong.'}
            }
        },
    },
}
