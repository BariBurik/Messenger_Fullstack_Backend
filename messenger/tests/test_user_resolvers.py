import json
from datetime import datetime, timedelta, UTC
from io import BytesIO
from unittest.mock import MagicMock, Mock

import jwt
import pytest
from django.core.handlers.asgi import ASGIRequest
from graphql import GraphQLError
from messenger.models import User
from messenger.resolvers.user_resolver import encrypt_password, decrypt_password, isAuthorized, refresh_access_token, \
    resolve_user_by_id, resolve_user_register, resolve_user_login, resolve_access_token, resolve_update_user
from myproject.settings import SECRET_KEY


def test_encrypt_password():
    password = "testpassword123"
    encrypted_password = encrypt_password(password)
    assert encrypted_password != password  # Пароль должен быть зашифрован


def test_decrypt_password():
    password = "testpassword123"
    encrypted_password = encrypt_password(password)
    decrypted_password = decrypt_password(encrypted_password)
    assert decrypted_password == password


@pytest.mark.django_db
def test_isAuthorized_valid_token():
    # Создаем тестового пользователя
    encrypted_password1 = encrypt_password('111')
    user1 = User.objects.create(id=1, name='test_user1', email='test_email1', password=encrypted_password1)

    # Инициализируем GraphQL-клиент
    payload = {
        'id': user1.id,
        'name': user1.name,
        'email': user1.email,
        'exp': datetime.now(UTC) + timedelta(minutes=60),
        'iat': datetime.now(UTC)
    }
    access_token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

    mock_scope = {
        'headers': [(b'authorization', b'Bearer ' + access_token.encode('utf-8'))]
    }

    # Настраиваем context для info
    info = MagicMock()
    info.context = MagicMock()
    info.context.scope = mock_scope

    try:
        isAuthorized(info)  # Проверяем, чтобы не выбрасывало исключений
    except Exception as e:
        pytest.fail(f"Ошибка авторизации: {str(e)}")


def test_isAuthorized_missing_token():
    request = MagicMock()
    request.headers = {}
    with pytest.raises(GraphQLError):
        isAuthorized(request)


def test_isAuthorized_invalid_token():
    request = MagicMock()
    request.headers = {'Authorization': 'Bearer invalid_token'}
    with pytest.raises(GraphQLError):
        isAuthorized(request)


@pytest.mark.django_db
def test_refresh_access_token_valid():
    encrypted_password1 = encrypt_password('111')
    user = User.objects.create(id=1, name='test_user', email='test_email', password=encrypted_password1)

    # Генерация токена для аутентификации
    payload = {
        'id': user.id,
        'exp': datetime.now(UTC) + timedelta(minutes=60),
        'iat': datetime.now(UTC)
    }
    refreshToken = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

    new_access_token = refresh_access_token(refreshToken)
    assert new_access_token is not None  # Должен возвращаться новый токен


def test_refresh_access_token_invalid():
    with pytest.raises(GraphQLError):
        request = MagicMock()
        payload = {
            'id': 123,
            'exp': datetime.now(UTC) - timedelta(minutes=1),  # Истекший токен
            'iat': datetime.now(UTC) - timedelta(minutes=5),
        }
        expired_refresh_token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        refresh_access_token(expired_refresh_token)


@pytest.mark.django_db
def test_resolve_user_by_id_valid():
    encrypted_password1 = encrypt_password('111')
    user = User.objects.create(id=1, name='test_user', email='test_email', password=encrypted_password1)

    # Генерация токена для аутентификации
    payload = {
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'exp': datetime.now(UTC) + timedelta(minutes=60),
        'iat': datetime.now(UTC)
    }
    access_token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

    mock_scope = {
        'headers': [(b'authorization', b'Bearer ' + access_token.encode('utf-8'))]
    }

    # Настраиваем context для info
    info = MagicMock()
    info.context = MagicMock()
    info.context.scope = mock_scope

    # Выполнение запроса
    result = resolve_user_by_id(None, info, user.id)

    # Проверка, что возвращенный пользователь соответствует ожидаемому
    assert result.id == user.id


@pytest.mark.django_db
def test_resolve_user_register_valid():
    user_data = {
        'name': 'John Doe',
        'email': 'test@email.com',
        'password': '11111111'
    }
    info = MagicMock()
    info.context = {'request': MagicMock()}
    result = resolve_user_register(None, info, user_data)
    assert 'access_token' in result
    assert 'refresh_token' in result


@pytest.mark.django_db
def test_resolve_user_register_invalid_email():
    user_data = {
        'name': 'John Doe',
        'email': 'invalid_email',
        'password': '11111111'
    }
    info = MagicMock()
    info.context = {'request': MagicMock()}
    with pytest.raises(GraphQLError):
        resolve_user_register(None, info, user_data)


@pytest.mark.django_db
def test_resolve_user_login_valid():
    encrypted_password1 = encrypt_password('11111111')
    user = User.objects.create(id=1, name='test_user', email='test_email', password=encrypted_password1)
    email = 'test_email'
    password = '11111111'
    info = MagicMock()
    info.context = {'request': MagicMock()}
    result = resolve_user_login(None, info, email, password)
    assert 'access_token' in result
    assert 'refresh_token' in result


@pytest.mark.django_db
def test_resolve_user_login_invalid_password():
    encrypted_password1 = encrypt_password('11111111')
    user = User.objects.create(id=1, name='test_user', email='test_email', password=encrypted_password1)
    email = 'test_email'
    password = 'wrongPassword'
    info = MagicMock()
    info.context = {'request': MagicMock()}
    with pytest.raises(GraphQLError):
        resolve_user_login(None, info, email, password)


@pytest.mark.django_db
def test_resolve_user_login_user_not_found():
    encrypted_password1 = encrypt_password('11111111')
    user = User.objects.create(id=1, name='test_user', email='test_email', password=encrypted_password1)
    email = 'nonexistentuser@example.com'
    password = '11111111'
    info = MagicMock()
    info.context = {'request': MagicMock()}
    with pytest.raises(GraphQLError):
        resolve_user_login(None, info, email, password)


@pytest.mark.django_db
def test_resolve_access_token_valid():
    encrypted_password1 = encrypt_password('11111111')
    user = User.objects.create(id=1, name='test_user', email='test_email', password=encrypted_password1)
    payload = {
        'id': user.id,
        'exp': datetime.now(UTC) + timedelta(minutes=60),
        'iat': datetime.now(UTC)
    }
    refreshToken = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    info = MagicMock()
    info.context = {'request': MagicMock()}
    result = resolve_access_token(None, info, refreshToken)
    assert 'access_token' in result


@pytest.mark.django_db
def test_resolve_access_token_expired():
    # Создаем пользователя
    encrypted_password1 = encrypt_password('11111111')
    user = User.objects.create(id=1, name='test_user', email='test_email', password=encrypted_password1)

    # Создаем истекший refresh token
    payload = {
        'id': user.id,
        'exp': datetime.now(UTC) - timedelta(minutes=1),  # Истекший токен
        'iat': datetime.now(UTC) - timedelta(minutes=5),
    }
    expired_refresh_token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

    info = MagicMock()

    # Проверяем, что при попытке использовать истекший токен выбрасывается ошибка
    with pytest.raises(GraphQLError) as exc_info:
        resolve_access_token(None, info, expired_refresh_token)

    # Проверяем, что сообщение об ошибке содержит нужную строку
    assert "Refresh token expired" in str(exc_info.value)


@pytest.mark.django_db
def test_resolve_update_user():
    encrypted_password1 = encrypt_password('11111111')
    user = User.objects.create(id=1, name='test_user', email='test_email', password=encrypted_password1)
    new_user = {'name': 'updated_test_name'}
    payload = {
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'exp': datetime.now(UTC) + timedelta(minutes=60),
        'iat': datetime.now(UTC)
    }
    access_token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    mock_scope = {
        'headers': [(b'authorization', b'Bearer ' + access_token.encode('utf-8'))]
    }

    # Настраиваем context для info
    info = MagicMock()
    info.context = MagicMock()
    info.context.scope = mock_scope
    result = resolve_update_user(None, info, new_user, access_token)
    assert 'access_token' in result
    assert 'refresh_token' in result


def test_resolve_update_user_invalid_token():
    new_user = {'name': 'Updated Name'}
    access_token = 'invalid_access_token'
    mock_scope = {
        'headers': [(b'authorization', b'Bearer ' + access_token.encode('utf-8'))]
    }

    # Настраиваем context для info
    info = MagicMock()
    info.context = MagicMock()
    info.context.scope = mock_scope
    with pytest.raises(GraphQLError):
        resolve_update_user(None, info, new_user, access_token)