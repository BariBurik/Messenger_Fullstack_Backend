from datetime import datetime, UTC

import jwt
from asgiref.sync import sync_to_async
from graphql import GraphQLError

from messenger.models import User, Chatroom, Message
from messenger.strawberry import notify_new_message
from myproject.settings import SECRET_KEY


@sync_to_async
def get_chat_by_name(chatroom_name):
    chatroom = Chatroom.objects.filter(name=chatroom_name).first()
    if not chatroom:
        raise ValueError(f"Chatroom with name {chatroom_name} not found")  # Или другое исключение
    return chatroom


@sync_to_async
def create_message(chatroom, user, text):
    message = Message.objects.create(
        chatroom=chatroom,
        user=user,
        text=text,
        created_at=datetime.now(UTC),
    )
    return message


@sync_to_async
def get_user_by_id(user_id):
    return User.objects.get(id=user_id)


async def is_authorized_for_strawberry(info):
    token = info.context['request'].headers.get('Authorization', None)
    if not token:
        raise GraphQLError("Authorization token missing")
    if token.startswith('Bearer '):
        token = token[7:]

    try:
        decode_token = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        user_id = decode_token.get('id')
        if user_id is None:
            raise GraphQLError("Invalid refresh token")

        user = await get_user_by_id(user_id)
        if user is None:
            raise GraphQLError("Invalid refresh token")
    except jwt.ExpiredSignatureError:
        raise GraphQLError("Token expired")
    except jwt.InvalidTokenError:
        raise GraphQLError("Invalid token")


async def get_id_from_token_for_strawberry(info):
    try:
        token = info.context['request'].headers.get('Authorization', None)
        if not token:
            raise GraphQLError("Authorization token missing")
        if token.startswith('Bearer '):
            token = token[7:]

        decode_token = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return decode_token.get('id')
    except jwt.ExpiredSignatureError:
        raise GraphQLError("Token expired")


async def resolve_send_message(self, info, chatroom_name, text):
    # Проверяем, авторизован ли пользователь
    await is_authorized_for_strawberry(info)

    user_id = await get_id_from_token_for_strawberry(info)
    user = await get_user_by_id(user_id)

    # Получаем чат
    chatroom = await get_chat_by_name(chatroom_name)

    # Создаем сообщение
    message = await create_message(chatroom, user, text)

    # Уведомляем всех участников чата о новом сообщении
    await notify_new_message(chatroom_name, user, message)

    # Возвращаем новое сообщение
    return message


def resolve_get_messages(self, info, chatroom_name):
    isAuthorized(info)
    messages = Message.objects.filter(chatroom__name=chatroom_name).order_by('-created_at')
    return messages

