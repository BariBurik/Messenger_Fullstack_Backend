import os
from django.core.asgi import get_asgi_application
from django.urls import path  # Корректный импорт для маршрутов
from channels.routing import ProtocolTypeRouter, URLRouter
from strawberry.asgi import GraphQL
from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL

from messenger.middlewares import StrawberryAuthMiddleware
from messenger.strawberry import schema

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings")

application = ProtocolTypeRouter({
    # HTTP запросы будут обрабатываться стандартным ASGI-приложением Django
    "http": get_asgi_application(),
    # WebSocket запросы перенаправляются на обработку GraphQL
    "websocket": StrawberryAuthMiddleware(URLRouter([
        path("graphql/subscription/", StrawberryAuthMiddleware(GraphQL(schema=schema))),
    ])),
})