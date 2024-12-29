from datetime import datetime, UTC, timedelta
from io import BytesIO
from unittest.mock import Mock, MagicMock

import jwt
import pytest
from django.core.handlers.asgi import ASGIRequest
from graphene.test import Client
from graphql_jwt.shortcuts import get_token

from messenger.resolvers.user_resolver import encrypt_password, resolve_users
from messenger.graphene import graphene_schema
from messenger.models import User
from myproject.settings import SECRET_KEY


@pytest.mark.django_db
def test_schema():
    encrypted_password1 = encrypt_password('111')
    encrypted_password2 = encrypt_password('222')
    user1 = User.objects.create(id=1, name='test_user1', email='test_email1', password=encrypted_password1)
    user2 = User.objects.create(id=2, name='test_user2', email='test_email2', password=encrypted_password2)

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

    # Выполняем запрос с заголовками
    response = resolve_users(None, info)
    print(response)
    print(User.objects.all())
    # Проверка данных пользователей
    assert list(response) == list(User.objects.all())