from datetime import datetime, UTC

import jwt
from graphql import GraphQLError
from jwt import InvalidTokenError

from messenger.models import User
from messenger.resolvers.user_resolver import refresh_access_token
from myproject.settings import SECRET_KEY


def get_user_from_token(token):
    try:
        # Раскодируем токен
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("id")
        if not user_id:
            raise InvalidTokenError("Token does not contain a user ID")

        # Получаем пользователя из базы данных
        try:
            user = User.objects.get(id=user_id)
            exp = payload.get("exp")
            if exp < datetime.now(UTC).timestamp():
                raise InvalidTokenError("Token expired")
            return user
        except User.DoesNotExist:
            raise InvalidTokenError("User not found")
    except jwt.InvalidTokenError:
        raise InvalidTokenError("Invalid token")


class GrapheneAuthMiddleware:
    def __init__(self, excluded_resolvers=None):
        self.excluded_resolvers = excluded_resolvers or [
            "userLogin",
            "userRegister",
            "__typename",
            "message"
        ]

    def resolve(self, next, root, info, **kwargs):
        if info.field_name in self.excluded_resolvers:
            return next(root, info, **kwargs)

        request = info.context
        cookies = request.headers.get("cookie", "")
        access_token = None
        refresh_token = None

        for cookie in cookies.split('; '):
            if cookie.startswith("access-token="):
                access_token = cookie.split("=")[1]
            if cookie.startswith("refresh-token="):
                refresh_token = cookie.split("=")[1]
        if access_token:
            try:
                user = get_user_from_token(access_token)
                request.user = user
            except InvalidTokenError as e:
                # Если access_token истек, пытаемся обновить его с помощью refresh_token
                if refresh_token:
                    try:
                        new_access_token = refresh_access_token(refresh_token)
                        request.user = get_user_from_token(new_access_token)
                        request._access_token = new_access_token
                        request._refresh_token = refresh_token
                    except InvalidTokenError:
                        request.user = None
                        raise GraphQLError("Unauthorized: Both access token and refresh token are invalid.")
                else:
                    request.user = None
                    raise GraphQLError("Unauthorized: Access token expired and no refresh token provided.")
        else:
            if refresh_token:
                try:
                    new_access_token = refresh_access_token(refresh_token)
                    print(new_access_token)
                    request.user = get_user_from_token(new_access_token)
                    print(request.user)
                    request._access_token = new_access_token
                    print(request._access_token)
                    request._refresh_token = refresh_token
                    print(request._refresh_token)

                except ValueError:
                    request.user = None
            else:
                request.user = None
                raise GraphQLError("Unauthorized")
        return next(root, info, **kwargs)