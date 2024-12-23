import os
from django.core.asgi import get_asgi_application
from django.urls import path  # Корректный импорт для маршрутов
from channels.routing import ProtocolTypeRouter, URLRouter
from strawberry.asgi import GraphQL
from messenger.subscription import schema as strawberry_schema

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings")

application = ProtocolTypeRouter({
    # HTTP запросы будут обрабатываться стандартным ASGI-приложением Django
    "http": get_asgi_application(),
    # WebSocket запросы перенаправляются на обработку GraphQL
    "websocket": URLRouter([
        path("subscription/", GraphQL(schema=strawberry_schema)),
    ]),
})