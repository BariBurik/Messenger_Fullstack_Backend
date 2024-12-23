from datetime import datetime, UTC, timedelta
from io import BytesIO
from unittest.mock import Mock, MagicMock

import jwt
import pytest
from django.core.handlers.asgi import ASGIRequest
from graphene.test import Client
from graphql_jwt.shortcuts import get_token

from messenger.resolvers.user_resolver import encrypt_password
from messenger.schema import schema
from messenger.models import User
from myproject.settings import SECRET_KEY


@pytest.mark.django_db
def test_schema():
    encrypted_password1 = encrypt_password('111')
    encrypted_password2 = encrypt_password('222')
    user1 = User.objects.create(id=1, name='test_user1', email='test_email1', password=encrypted_password1)
    user2 = User.objects.create(id=2, name='test_user2', email='test_email2', password=encrypted_password2)

    client = Client(schema)

    payload = {
        'id': user1.id,
        'name': user1.name,
        'email': user1.email,
        'exp': datetime.now(UTC) + timedelta(minutes=60),
        'iat': datetime.now(UTC)
    }
    access_token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

    mock_request = ASGIRequest(
        scope={
            "type": "http",
            "headers": [(b"authorization", f"Bearer {access_token}".encode())],
            "method": "GET",
            "path": "/graphql",
        },
        body_file=BytesIO(b"")  # Передаем пустое тело запроса
    )

    # Запрос с использованием accessToken
    query = '''
        query {
            users {
                id
                name
            }
        }
    '''

    context_value = {
        'request': mock_request  # Передаем мок-объект в контекст
    }
    # Выполняем запрос с заголовками
    response = client.execute(query, context_value=context_value)

    # Проверка данных пользователей
    assert response['data']['users'] == [
        {"id": "1", "name": "test_user1"},
        {"id": "2", "name": "test_user2"},
    ]