from graphene_django.views import GraphQLView
import json

from graphene_file_upload.django import FileUploadGraphQLView
from strawberry.django.views import AsyncGraphQLView


class CustomGraphQLView(FileUploadGraphQLView):
    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if hasattr(request, "_access_token") and hasattr(request, "_refresh_token"):
            try:
                response.set_cookie(
                    "access-token",
                    request._access_token,
                    domain="localhost",
                    path="/",
                    httponly=True,
                    samesite="Lax",
                    secure=False
                )
                response.set_cookie(
                    "refresh-token",
                    request._refresh_token,
                    domain="localhost",
                    path="/",
                    httponly=True,
                    samesite="Lax",
                    secure=False
                )
            except json.JSONDecodeError:
                pass
        return response


class CustomAsyncGraphQLView(AsyncGraphQLView):
    async def dispatch(self, request, *args, **kwargs):
        response = await super().dispatch(request, *args, **kwargs)
        if hasattr(request, "_access_token") and hasattr(request, "_refresh_token"):
            try:
                response.set_cookie(
                    "access-token",
                    request._access_token,
                    domain="localhost",
                    path="/",
                    httponly=True,
                    samesite="Lax",
                    secure=False
                )
                response.set_cookie(
                    "refresh-token",
                    request._refresh_token,
                    domain="localhost",
                    path="/",
                    httponly=True,
                    samesite="Lax",
                    secure=False
                )
            except json.JSONDecodeError:
                pass
        return response