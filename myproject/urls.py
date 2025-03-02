import logging

from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from strawberry.django.views import AsyncGraphQLView

from messenger.CustomGraphQLView import CustomGraphQLView
from messenger.deleteCookie import delete_http_only_cookie
from messenger.graphene import graphene_schema
from messenger.strawberry import schema as strawberry_schema


urlpatterns = [
    path('admin/', admin.site.urls),
    # Graphene маршруты
    path("graphql/graphene/", CustomGraphQLView.as_view(graphiql=True, schema=graphene_schema)),
    # Strawberry маршруты
    path("graphql/strawberry/", AsyncGraphQLView.as_view(schema=strawberry_schema)),
    path('delete-http-only-cookie/', delete_http_only_cookie, name='delete_http_only_cookie'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)