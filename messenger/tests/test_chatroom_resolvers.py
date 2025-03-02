from datetime import datetime, UTC, timedelta

import jwt
import pytest
from unittest.mock import MagicMock

from messenger.middlewares import AuthMiddleware
from messenger.resolvers.chatroom_resolver import resolve_user_chatrooms, \
    resolve_filter_chatroom, resolve_filter_not_created_chats, resolve_chatroom_by_id, resolve_chatroom_create, \
    resolve_chat_create, resolve_favorite_create, resolve_chatroom_update, resolve_chatroom_delete
from messenger.models import Chatroom, User, Chat
from graphql import GraphQLError

from myproject.settings import SECRET_KEY


@pytest.mark.django_db
def test_resolve_user_chatrooms():
    # Создаем пользователей и чатрумы
    user = User.objects.create(id=1, name='test_user', email='test_email')
    chatroom1 = Chatroom.objects.create(name='chatroom_1')
    chatroom2 = Chatroom.objects.create(name='chatroom_2')
    chatroom1.participants.add(user)
    chatroom2.participants.add(user)

    payload = {
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'exp': datetime.now(UTC) + timedelta(minutes=60),
        'iat': datetime.now(UTC)
    }
    access_token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    mock_request = MagicMock()
    mock_request.headers = MagicMock()
    mock_request.headers.get = MagicMock(return_value=f"access_token={access_token}")
    info = MagicMock()
    info.context = MagicMock()
    info.context.request = mock_request

    # Создаем экземпляр GrapheneAuthMiddleware
    middleware = AuthMiddleware(None)

    # Вызываем middleware
    middleware.resolve(MagicMock(), None, info)

    mock_user = user
    info.context.request.user = mock_user

    # Выполняем запрос
    result = resolve_user_chatrooms(None, info)

    assert len(result) == 2
    assert chatroom1 in result
    assert chatroom2 in result


@pytest.mark.django_db
def test_resolve_filter_not_created_chats():
    current_user = User.objects.create(id=1, name='current_user', email='tesl_mail1')
    user1 = User.objects.create(id=2, name='user1', email='test_mail2')
    user2 = User.objects.create(id=3, name='user2', email='test_mail3')
    payload = {
        'id': current_user.id,
        'name': current_user.name,
        'email': current_user.email,
        'exp': datetime.now(UTC) + timedelta(minutes=60),
        'iat': datetime.now(UTC)
    }

    access_token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    mock_request = MagicMock()
    mock_request.headers = MagicMock()
    mock_request.headers.get = MagicMock(return_value=f"access_token={access_token}")
    info = MagicMock()
    info.context = MagicMock()
    info.context.request = mock_request

    # Создаем экземпляр GrapheneAuthMiddleware
    middleware = AuthMiddleware(None)

    # Вызываем middleware
    middleware.resolve(MagicMock(), None, info)

    mock_user = current_user
    info.context.request.user = mock_user
    resolve_chat_create(None, info,  'user1')
    # Выполняем запрос
    result = resolve_filter_not_created_chats(None, info, 'user')

    assert user1 not in result
    assert user2 in result


@pytest.mark.django_db
def test_resolve_chatroom_by_id():
    user = User.objects.create(id=1, name='test_user', email='test_email')
    chatroom = Chatroom.objects.create(name='chatroom_1')

    payload = {
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'exp': datetime.now(UTC) + timedelta(minutes=60),
        'iat': datetime.now(UTC)
    }
    access_token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    mock_request = MagicMock()
    mock_request.headers = MagicMock()
    mock_request.headers.get = MagicMock(return_value=f"access_token={access_token}")
    info = MagicMock()
    info.context = MagicMock()
    info.context.request = mock_request

    # Создаем экземпляр GrapheneAuthMiddleware
    middleware = AuthMiddleware(None)

    # Вызываем middleware
    middleware.resolve(MagicMock(), None, info)

    mock_user = user
    info.context.request.user = mock_user

    # Выполняем запрос
    result = resolve_chatroom_by_id(None, info, chatroom.id)

    assert result == chatroom


@pytest.mark.django_db
def test_resolve_chatroom_create():
    user1 = User.objects.create(id=1, name='test_user1', email='test_email1')
    user2 = User.objects.create(id=2, name='test_user2', email='test_email2')

    payload = {
        'id': user1.id,
        'name': user1.name,
        'email': user1.email,
        'exp': datetime.now(UTC) + timedelta(minutes=60),
        'iat': datetime.now(UTC)
    }
    access_token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    mock_request = MagicMock()
    mock_request.headers = MagicMock()
    mock_request.headers.get = MagicMock(return_value=f"access_token={access_token}")
    info = MagicMock()
    info.context = MagicMock()
    info.context.request = mock_request

    # Создаем экземпляр GrapheneAuthMiddleware
    middleware = AuthMiddleware(None)

    # Вызываем middleware
    middleware.resolve(MagicMock(), None, info)

    mock_user = user1
    info.context.request.user = mock_user

    # Выполняем запрос
    result = resolve_chatroom_create(None, info, 'chatroom_1', {'user_2': user2.id})

    assert result.name == 'chatroom_1'
    assert user1 in result.participants.all()
    assert user2 in result.participants.all()


@pytest.mark.django_db
def test_resolve_chat_create():
    user1 = User.objects.create(id=1, name='test_user1', email='test_email1')
    user2 = User.objects.create(id=2, name='test_user2', email='test_email2')

    payload = {
        'id': user1.id,
        'name': user1.name,
        'email': user1.email,
        'exp': datetime.now(UTC) + timedelta(minutes=60),
        'iat': datetime.now(UTC)
    }
    access_token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    mock_request = MagicMock()
    mock_request.headers = MagicMock()
    mock_request.headers.get = MagicMock(return_value=f"access_token={access_token}")
    info = MagicMock()
    info.context = MagicMock()
    info.context.request = mock_request

    # Создаем экземпляр GrapheneAuthMiddleware
    middleware = AuthMiddleware(None)

    # Вызываем middleware
    middleware.resolve(MagicMock(), None, info)

    mock_user = user1
    info.context.request.user = mock_user

    # Выполняем запрос
    result = resolve_chat_create(None, info, 'test_user2')

    assert result.participants.count() == 2
    assert result.name == 'test_user1 & test_user2'
    assert user1 in result.participants.all()
    assert user2 in result.participants.all()


@pytest.mark.django_db
def test_resolve_favorite_create():
    user = User.objects.create(id=1, name='test_user1')

    payload = {
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'exp': datetime.now(UTC) + timedelta(minutes=60),
        'iat': datetime.now(UTC)
    }
    access_token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    mock_request = MagicMock()
    mock_request.headers = MagicMock()
    mock_request.headers.get = MagicMock(return_value=f"access_token={access_token}")
    info = MagicMock()
    info.context = MagicMock()
    info.context.request = mock_request

    # Создаем экземпляр GrapheneAuthMiddleware
    middleware = AuthMiddleware(None)

    # Вызываем middleware
    middleware.resolve(MagicMock(), None, info)

    mock_user = user
    info.context.request.user = mock_user

    # Выполняем запрос
    result = resolve_favorite_create(None, info)

    assert result.participants.count() == 1
    assert user in result.participants.all()


@pytest.mark.django_db
def test_resolve_chatroom_update_success():
    # Создаем пользователей
    user = User.objects.create(id=1, name='test_user1', email='test_mail1')
    user2 = User.objects.create(id=2, name='test_user2', email='test_mail2')

    # Создаем чат
    chatroom = Chatroom.objects.create(id=1, name="Test Chat")
    chatroom.participants.add(user)  # Добавляем участника в чат

    payload = {
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'exp': datetime.now(UTC) + timedelta(minutes=60),
        'iat': datetime.now(UTC)
    }
    access_token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    mock_request = MagicMock()
    mock_request.headers = MagicMock()
    mock_request.headers.get = MagicMock(return_value=f"access_token={access_token}")
    info = MagicMock()
    info.context = MagicMock()
    info.context.request = mock_request

    # Создаем экземпляр GrapheneAuthMiddleware
    middleware = AuthMiddleware(None)

    # Вызываем middleware
    middleware.resolve(MagicMock(), None, info)

    mock_user = user
    info.context.request.user = mock_user

    # Пытаемся обновить чат (добавить пользователей)
    users_to_add = {1: user2.id}
    response = resolve_chatroom_update(None, info, chatroom.id, users_to_add, name = "New Chat")

    # Проверяем, что чат обновился и пользователи добавлены
    assert response.participants.count() == Chatroom.objects.get(id=chatroom.id).participants.count()
    assert response.name == Chatroom.objects.get(id=chatroom.id).name


@pytest.mark.django_db
def test_resolve_chat_delete():
    user1 = User.objects.create(id=1, name='test_user1', email='test_email1')

    chatroom = Chatroom.objects.create(id=1, name="Test Chat")
    chatroom.participants.add(user1)

    payload = {
        'id': user1.id,
        'name': user1.name,
        'email': user1.email,
        'exp': datetime.now(UTC) + timedelta(minutes=60),
        'iat': datetime.now(UTC)
    }
    access_token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    mock_request = MagicMock()
    mock_request.headers = MagicMock()
    mock_request.headers.get = MagicMock(return_value=f"access_token={access_token}")
    info = MagicMock()
    info.context = MagicMock()
    info.context.request = mock_request

    # Создаем экземпляр GrapheneAuthMiddleware
    middleware = AuthMiddleware(None)

    # Вызываем middleware
    middleware.resolve(MagicMock(), None, info)

    mock_user = user1
    info.context.request.user = mock_user

    # Выполняем запрос
    resolve_chatroom_delete(None, info, chatroom.id)

    chat = Chatroom.objects.filter(id=chatroom.id)

    assert list(chat) == []