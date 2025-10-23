from fastapi import Request, status
from fastapi.responses import JSONResponse


async def handle_unverified_user(request: Request, exc):
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={'message': getattr(exc, 'message', 'User not verified.')},
    )


async def handle_inactive_user(request: Request, exc):
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={'message': getattr(exc, 'message', 'Account inactive.')},
    )


async def handle_forbidden(request: Request, exc):
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={'message': getattr(exc, 'message', 'Access forbidden.')},
    )


async def handle_not_found(request: Request, exc):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            'message': getattr(exc, 'message', 'Requested item not found.')
        },
    )


async def handle_already_exists(request: Request, exc):
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            'message': getattr(exc, 'message', 'Item(s) already exist(s).')
        },
    )


async def handle_bad_request(request: Request, exc):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={'message': getattr(exc, 'message', 'Bad request.')},
    )


async def handle_server_error(request: Request, exc):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            'message': getattr(
                exc, 'message', 'Something went wrong. Contact us.'
            )
        },
    )
