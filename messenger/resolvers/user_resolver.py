from datetime import datetime, timedelta, UTC
from venv import logger

import jwt
from asgiref.sync import sync_to_async
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from graphql import GraphQLError
from graphql_jwt.decorators import login_required
from starlette.responses import JSONResponse

from messenger.models import User
from cryptography.fernet import Fernet

from myproject.settings import SECRET_KEY

key = b'wZIuD0dSRXfDRYkr0MUSxr2j7e8JZphNv1CZkJDNHyA='
fernet = Fernet(key)


def encrypt_password(password: str) -> str:
    encrypted_password = fernet.encrypt(password.encode())
    return encrypted_password.decode()  # Для хранения в базе данных в текстовом формате


def decrypt_password(encrypted_password: str) -> str:
    decrypted_password = fernet.decrypt(encrypted_password.encode()).decode()
    return decrypted_password


def resolve_get_self(self, info):
    user = info.context.get('user')
    return user


def refresh_access_token(refresh_token):
    try:
        decode_refresh_token = jwt.decode(refresh_token, SECRET_KEY, algorithms=['HS256'])
        user_id = decode_refresh_token.get('id')
        if user_id is None:
            raise GraphQLError("Invalid refresh token")

        user = User.objects.get(id=user_id)
        if user is None:
            raise GraphQLError("Invalid refresh token")

        payload = {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'avatar': user.avatar.url if user.avatar else None,
            'exp': datetime.now(UTC) + timedelta(minutes=60),
            'iat': datetime.now(UTC)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        response = JSONResponse({"message": "User registered successfully"})

        response.set_cookie(
            "access-token", token, httponly=True, samesite="none", secure=True
        )

        return response

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

    encrypted_password = encrypt_password(password)

    user = User.objects.create(
        name=name,
        email=email,
        password=encrypted_password,
        avatar=avatar
    )

    payload = {
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'avatar': user.avatar.url if user.avatar else '',
        'exp': datetime.now(UTC) + timedelta(minutes=60),
        'iat': datetime.now(UTC)
    }
    access_token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

    refresh_payload = {
        'id': user.id,
        'exp': datetime.now(UTC) + timedelta(days=7),
        'iat': datetime.now(UTC)
    }
    refresh_token = jwt.encode(refresh_payload, SECRET_KEY, algorithm='HS256')

    response = JSONResponse({"message": "User registered successfully"})

    response.set_cookie(
        "access-token", access_token, httponly=True, samesite="none", secure=True
    )
    response.set_cookie(
        "refresh-token", refresh_token, httponly=True, samesite="none", secure=True
    )

    return response


def resolve_user_login(self, info, email, password):
    try:
        user = User.objects.filter(email=email).first()

        if user is None:
            raise GraphQLError("User with this email does not exist")

        try:
            # Дешифруем сохранённый пароль
            decrypted_password = decrypt_password(user.password)
        except Exception as e:
            logger.error(f"Password decryption failed: {str(e)}")
            raise GraphQLError(f"Password decryption failed: {str(e)}")

        # Сравниваем расшифрованный пароль с введённым
        if decrypted_password != password:
            raise GraphQLError("Incorrect password")

        payload = {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'avatar': user.avatar.url if user.avatar else '',
            'exp': datetime.now(UTC) + timedelta(minutes=60),
            'iat': datetime.now(UTC)
        }
        access_token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

        refresh_payload = {
            'id': user.id,
            'exp': datetime.now(UTC) + timedelta(days=7),
            'iat': datetime.now(UTC)
        }
        refresh_token = jwt.encode(refresh_payload, SECRET_KEY, algorithm='HS256')

        response = JSONResponse({"message": "User login successfully"})

        response.set_cookie(
            "access-token", access_token, httponly=True, samesite="none", secure=True
        )
        response.set_cookie(
            "refresh-token", refresh_token, httponly=True, samesite="none", secure=True
        )

        return response

    except GraphQLError as gql_err:
        raise gql_err
    except Exception as e:
        logger.exception("Unexpected error during user login")
        raise GraphQLError("An unexpected error occurred.")


def resolve_access_token(self, info, refresh_token):
    try:
        new_access_token = refresh_access_token(refresh_token)
        return {
            'access_token': new_access_token
        }
    except ValueError as e:
        raise GraphQLError(str(e))


def resolve_update_user(self, info, new_user):
    user = info.context.get('user')
    if user is None:
        raise GraphQLError("Invalid access token")

    updated_data = {}
    if new_user.get('name'):  # Если имя не пустое, обновляем его
        if len(new_user.get('name')) > 4:
            if User.objects.filter(name=new_user['name']).exclude(id=user.id):
                raise GraphQLError("User with this name already exists")
            updated_data['name'] = new_user['name']
        else:
            raise GraphQLError("Name must be more than 4 characters")
    if new_user.get('email'):  # Если email не пустой, обновляем его
        try:
            validate_email(new_user.get('email'))
        except ValidationError:
            raise GraphQLError("Invalid email")
        if User.objects.filter(email=new_user['email']).exclude(id=user.id):
            raise GraphQLError("User with this email already exists")
        updated_data['email'] = new_user['email']
    if new_user.get('password'):  # Если пароль не пустой, обновляем его
        if len(new_user.get('password')) > 7:
            updated_data['password'] = new_user['password']
        else:
            raise GraphQLError("Name must be more than 4 characters")

    User.objects.filter(id=user.id).update(**updated_data)

    # Получаем обновленного пользователя
    updated_user = User.objects.get(id=user.id)

    payload = {
        'id': updated_user.id,
        'name': updated_user.name,
        'email': updated_user.email,
        'avatar': updated_user.avatar.url if user.avatar else '',
        'exp': datetime.now(UTC) + timedelta(minutes=60),
        'iat': datetime.now(UTC)
    }

    access_token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

    refresh_payload = {
        "id": updated_user.id,
        'exp': datetime.now(UTC) + timedelta(days=7),
        'iat': datetime.now(UTC)
    }

    refresh_token = jwt.encode(refresh_payload, SECRET_KEY, algorithm='HS256')

    response = JSONResponse({"message": "User update successfully"})

    response.set_cookie(
        "access-token", access_token, httponly=True, samesite="none", secure=True
    )
    response.set_cookie(
        "refresh-token", refresh_token, httponly=True, samesite="none", secure=True
    )

    return response
