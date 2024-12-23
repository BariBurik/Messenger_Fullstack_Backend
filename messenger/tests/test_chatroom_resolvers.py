from datetime import datetime, UTC, timedelta

import jwt
import pytest
from unittest.mock import MagicMock
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
    info = MagicMock()
    request_mock = MagicMock()
    request_mock.headers.get.return_value = f"Bearer {access_token}"
    info.context = {'request': request_mock}

    # Выполняем запрос
    result = resolve_user_chatrooms(None, info, user.id)

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
    info = MagicMock()
    request_mock = MagicMock()
    request_mock.headers.get.return_value = f"Bearer {access_token}"
    info.context = {'request': request_mock}
    resolve_chat_create(None, info,  {1: user1.id, 2: current_user.id})
    # Выполняем запрос
    result = resolve_filter_not_created_chats(None, info, current_user.id, 'user')

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
    info = MagicMock()
    request_mock = MagicMock()
    request_mock.headers.get.return_value = f"Bearer {access_token}"
    info.context = {'request': request_mock}

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
    info = MagicMock()
    request_mock = MagicMock()
    request_mock.headers.get.return_value = f"Bearer {access_token}"
    info.context = {'request': request_mock}

    # Выполняем запрос
    result = resolve_chatroom_create(None, info, 'chatroom_1', {1: user1.id, 2: user2.id})

    assert result.name == 'chatroom_1'
    assert user1 in result.participants.all()
    assert user2 in result.participants.all()


@pytest.mark.django_db
def test_resolve_chat_create():
    user1 = User.objects.create(id=1, name='test_user1', email='test_email1')
    user2 = User.objects.create(id=2, name='test_user2', email='test_email2')
    user3 = User.objects.create(id=3, name='test_user3', email='test_email3')

    payload = {
        'id': user1.id,
        'name': user1.name,
        'email': user1.email,
        'exp': datetime.now(UTC) + timedelta(minutes=60),
        'iat': datetime.now(UTC)
    }
    access_token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    info = MagicMock()
    request_mock = MagicMock()
    request_mock.headers.get.return_value = f"Bearer {access_token}"
    info.context = {'request': request_mock}

    # Выполняем запрос
    result = resolve_chat_create(None, info, {1: user1.id, 2: user2.id})

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
    info = MagicMock()
    request_mock = MagicMock()
    request_mock.headers.get.return_value = f"Bearer {access_token}"
    info.context = {'request': request_mock}

    # Выполняем запрос
    result = resolve_favorite_create(None, info, {1: user.id})

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
    info = MagicMock()
    request_mock = MagicMock()
    request_mock.headers.get.return_value = f"Bearer {access_token}"
    info.context = {'request': request_mock}

    # Пытаемся обновить чат (добавить пользователей)
    users_to_add = {1: user2.id}
    response = resolve_chatroom_update(None, info, chatroom.id, users_to_add, name = "New Chat")

    # Проверяем, что чат обновился и пользователи добавлены
    assert response.participants.count() == Chatroom.objects.get(id=chatroom.id).participants.count()
    assert response.name == Chatroom.objects.get(id=chatroom.id).name


@pytest.mark.django_db
def test_resolve_chat_delete():
    user1 = User.objects.create(id=1, name='test_user1', email='test_email1')
    user2 = User.objects.create(id=2, name='test_user2', email='test_email2')

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
    info = MagicMock()
    request_mock = MagicMock()
    request_mock.headers.get.return_value = f"Bearer {access_token}"
    info.context = {'request': request_mock}

    # Выполняем запрос
    resolve_chatroom_delete(None, info, chatroom.id)

    chat = Chatroom.objects.filter(id=chatroom.id)

    assert list(chat) == []