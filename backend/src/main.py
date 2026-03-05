from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from src import endpoints
from src import middleware as mdw
from src.config import CFG

# from src import exceptions as exc
from src.lifespan import lifespan

app = FastAPI(lifespan=lifespan, root_path='/api')

app.add_middleware(
    CORSMiddleware,
    allow_origins=[CFG.BACKEND_ORIGIN, CFG.FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.add_middleware(mdw.LanguageMiddleware)
app.add_middleware(mdw.ExceptionsMiddleware)
app.add_middleware(mdw.EnsureCORSHeadersMiddleware)

app.include_router(endpoints.auth_router, tags=['auth'])
app.include_router(endpoints.core_router, tags=['definitions'])
app.include_router(endpoints.profiles_router, tags=['profile'])
app.include_router(endpoints.values_router, tags=['values'])
app.include_router(endpoints.contacts_router, tags=['contacts'])
app.include_router(endpoints.messages_router, tags=['messages'])
app.include_router(endpoints.bootstrap_router, tags=['bootstrap'])


app.include_router(endpoints.chat_router)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title='The likes',
        version='1.0.0',
        description='Find people with similar core values.',
        routes=app.routes,
    )
    openapi_schema['paths']['/ws'] = {
        'get': {
            'summary': 'WebSocket Endpoint',
            'description': 'Establishes a WebSocket connection.',
            'responses': {
                101: {'description': 'Switching Protocols'},
                200: {'description': 'WebSocket Connection'},
            },
            'tags': ['chat'],
        }
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi_schema = custom_openapi()
