from datetime import datetime, timedelta, UTC
from venv import logger
import jwt
from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from graphql import GraphQLError
from starlette.responses import JSONResponse

from messenger.models import User

from myproject.settings import SECRET_KEY


def create_access_token(user):
    payload = {
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'avatar': user.avatar.url if user.avatar else None,
        'exp': datetime.now(UTC) + timedelta(minutes=60),
        'iat': datetime.now(UTC)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    return token


def create_refresh_token(user):
    payload = {
        'id': user.id,
        'exp': datetime.now(UTC) + timedelta(days=7),
        'iat': datetime.now(UTC)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    return token


def refresh_access_token(refresh_token):
    try:
        decode_refresh_token = jwt.decode(refresh_token, SECRET_KEY, algorithms=['HS256'])
        user_id = decode_refresh_token.get('id')
        if user_id is None:
            raise GraphQLError("Invalid refresh token")

        user = User.objects.get(id=user_id)
        if user is None:
            raise GraphQLError("Invalid refresh token")

        token = create_access_token(user)

        return token

    except jwt.ExpiredSignatureError:
        raise GraphQLError("Refresh token expired")


def resolve_users(self, info):
    return User.objects.all()


def resolve_user_by_id(self, info, id):
    return User.objects.get(id=id)


def resolve_user_register(self, info, user):
    name = user['name']
    email = user['email']
    password = user['password']
    avatar = user.get('avatar', '')

    request = info.context

    try:
        validate_email(email)
    except ValidationError:
        raise GraphQLError("Email is not valid")

    if password is None:
        raise GraphQLError("Password cannot be empty")

    if len(password) < 8:
        raise GraphQLError("Password must be more than 8 characters")

    if len(name) < 4:
        raise GraphQLError("Name must be more than 4 characters")

    if User.objects.filter(email=email).exists():
        raise GraphQLError("User with this email already exists")

    if User.objects.filter(name=name).exists():
        raise GraphQLError("User with this name already exists")

    hashed_password = make_password(password)

    user = User.objects.create(
        name=name,
        email=email,
        password=hashed_password,
        avatar=avatar
    )

    access_token = create_access_token(user)

    refresh_token = create_refresh_token(user)

    request._access_token = access_token
    request._refresh_token = refresh_token

    from messenger.graphene import ResponseType
    return ResponseType("User successfully registered")


def resolve_user_login(self, info, email, password):
    try:
        request = info.context

        user = User.objects.filter(email=email).first()

        if user is None:
            raise GraphQLError("User with this email does not exist")

        if not check_password(password, user.password):
            raise GraphQLError("Incorrect password")

        access_token = create_access_token(user)

        refresh_token = create_refresh_token(user)

        request._access_token = access_token
        request._refresh_token = refresh_token

        from messenger.graphene import ResponseType
        return ResponseType("User logged in successfully")

    except GraphQLError as gql_err:
        raise gql_err


def resolve_access_token(self, info, refresh_token):
    try:
        response = refresh_access_token(refresh_token)
        return response
    except ValueError as e:
        raise GraphQLError(str(e))


def resolve_update_user(self, info, new_user):
    user = info.context.user
    if user is None:
        raise GraphQLError("Invalid access token")

    request = info.context

    if new_user.get('name'):
        if len(new_user.get('name')) > 4:
            if User.objects.filter(name=new_user['name']).exclude(id=user.id):
                raise GraphQLError("User with this name already exists")
            user.name = new_user['name']
        else:
            raise GraphQLError("Name must be more than 4 characters")

    if new_user.get('email'):
        try:
            validate_email(new_user.get('email'))
        except ValidationError:
            raise GraphQLError("Invalid email")
        if User.objects.filter(email=new_user['email']).exclude(id=user.id):
            raise GraphQLError("User with this email already exists")
        user.email = new_user['email']

    if new_user.get('password'):
        if len(new_user.get('password')) > 7:
            user.set_password(new_user['password'])
        else:
            raise GraphQLError("Password must be more than 7 characters")

    if new_user.get('avatar'):
        user.avatar = new_user['avatar']

    user.save()

    # Получаем обновленного пользователя
    updated_user = User.objects.get(id=user.id)

    access_token = create_access_token(updated_user)

    refresh_token = create_refresh_token(updated_user)

    request._access_token = access_token
    request._refresh_token = refresh_token

    from messenger.graphene import ResponseType
    return ResponseType("User successfully updated")


def resolve_re_login(self, info):
    from messenger.graphene import ReLoginResponseType
    user = info.context.user
    if user:
        temp_token = create_access_token(user)
        return ReLoginResponseType(message="User logged in successfully", temp_token=temp_token, user=user)

    return ReLoginResponseType(message="User not logged in", temp_token=None, user=None)


def resolve_get_users_per_query(self, info, search_query, excludes=None):
    this_user = info.context.user
    if not this_user:
        raise GraphQLError("Invalid access token")
    users = User.objects.filter(name__icontains=search_query).exclude(id=this_user.id)

    if excludes:
        users = users.exclude(id__in=excludes)

    return users