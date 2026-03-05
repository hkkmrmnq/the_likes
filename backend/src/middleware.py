from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src import exceptions as exc
from src.config import CFG
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


class ExceptionsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        try:
            return await call_next(request)
        except exc.NotFound as e:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={'detail': exc.get_error_msg(e)},
            )
        except exc.Forbidden as e:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={'detail': exc.get_error_msg(e)},
            )
        except exc.Unauthorized as e:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={'detail': exc.get_error_msg(e)},
            )
        except exc.AlreadyExists as e:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={'detail': exc.get_error_msg(e)},
            )
        except exc.BadRequest as e:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={'detail': exc.get_error_msg(e)},
            )
        # except (exc.ServerError, Exception):
        #     return JSONResponse(
        #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        #         content={'detail': 'Something went wrong.'},
        #     )


class EnsureCORSHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)

        response.headers['Access-Control-Allow-Origin'] = CFG.FRONTEND_ORIGIN
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Methods'] = '*'
        response.headers['Access-Control-Allow-Headers'] = '*'

        return response
