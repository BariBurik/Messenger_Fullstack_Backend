from datetime import datetime, UTC

import jwt
from asgiref.sync import sync_to_async
from graphql import GraphQLResolveInfo
from jwt import decode, ExpiredSignatureError, InvalidTokenError
from strawberry import Info

from messenger.models import User
from myproject.settings import SECRET_KEY


@sync_to_async
def get_user_from_token(token):
    try:
        # Раскодируем токен
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("user_id")
        if not user_id:
            raise InvalidTokenError("Token does not contain a user ID")

        # Получаем пользователя из базы данных
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise InvalidTokenError("User not found")

        # Проверяем срок действия токена (если не используется валидация на уровне JWT)
        exp = payload.get("exp")
        if exp and datetime.fromtimestamp(exp) < datetime.now(UTC):
            raise InvalidTokenError("Token has expired")

        return user
    except jwt.ExpiredSignatureError:
        raise InvalidTokenError("Token has expired")
    except jwt.InvalidTokenError:
        raise InvalidTokenError("Invalid token")


def get_user_from_token_sync(token):
    try:
        # Раскодируем токен
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("user_id")
        if not user_id:
            raise InvalidTokenError("Token does not contain a user ID")

        # Получаем пользователя из базы данных
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise InvalidTokenError("User not found")

        # Проверяем срок действия токена (если не используется валидация на уровне JWT)
        exp = payload.get("exp")
        if exp and datetime.fromtimestamp(exp) < datetime.now(UTC):
            raise InvalidTokenError("Token has expired")

        return user
    except jwt.ExpiredSignatureError:
        raise InvalidTokenError("Token has expired")
    except jwt.InvalidTokenError:
        raise InvalidTokenError("Invalid token")


class StrawberryAuthMiddleware:
    def __init__(self, app, excluded_resolvers=None):
        self.excluded_resolvers = excluded_resolvers or [
            "resolve_user_login",
            "resolve_user_register",
            "refresh_access_token",
        ]
        self.app = app

    async def __call__(self, scope, receive, send):
        headers = dict(scope['headers'])
        if b'cookie' in headers:
            cookies = headers[b'cookie'].decode().split('; ')
            for cookie in cookies:
                if cookie.startswith('access_token='):
                    token = cookie.split('=')[1]
                    scope['user'] = await get_user_from_token(token)
                    break
            else:
                scope['user'] = None

        return await self.app(scope, receive, send)

    async def resolve_strawberry(self, next_, root, info, **kwargs):
        if info.field_name in self.excluded_resolvers:
            return await next_(root, info, **kwargs)

        request = info.context["request"]
        cookies = request.headers.get("cookie", "")
        access_token = None

        for cookie in cookies.split('; '):
            if cookie.startswith("access_token="):
                access_token = cookie.split("=")[1]

        if access_token:
            try:
                user = await get_user_from_token(access_token)
                info.context["user"] = user
            except Exception:
                info.context["user"] = None
        else:
            info.context["user"] = None

        return await next_(root, info, **kwargs)


class GrapheneAuthMiddleware:
    def __init__(self, app, excluded_resolvers=None):
        self.excluded_resolvers = excluded_resolvers or [
            "resolve_user_login",
            "resolve_user_register",
            "refresh_access_token",
        ]
        self.app = app

    def resolve(self, next, root, info, **kwargs):
        if info.field_name in self.excluded_resolvers:
            return next(root, info, **kwargs)

        request = info.context
        cookies = request.headers.get("cookie", "")
        access_token = None

        for cookie in cookies.split('; '):
            if cookie.startswith("access_token="):
                access_token = cookie.split("=")[1]

        if access_token:
            try:
                user = get_user_from_token_sync(access_token)
                info.context["user"] = user
            except Exception:
                info.context["user"] = None
        else:
            info.context["user"] = None

        return next(root, info, **kwargs)