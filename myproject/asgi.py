import os
from django.core.asgi import get_asgi_application
from django.urls import path
from channels.routing import ProtocolTypeRouter, URLRouter
from strawberry.asgi import GraphQL
from strawberry.channels import GraphQLWSConsumer
from strawberry.django.views import AsyncGraphQLView

from messenger.strawberry import schema

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings")

graphql_ws_consumer = GraphQLWSConsumer(schema)

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": (URLRouter([
        path("graphql/subscription/", graphql_ws_consumer.as_asgi(schema=schema)),
    ])),
})
