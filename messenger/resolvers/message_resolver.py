from datetime import datetime, UTC
from asgiref.sync import sync_to_async

from messenger.middlewares import get_user_from_token
from messenger.models import User, Chatroom, Message
from messenger.strawberry import notify_new_message, notify_new_chatroom


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


async def resolve_send_message(self, info, access_token, chatroom_name, text):
    user = await sync_to_async(get_user_from_token)(access_token)
    if not user:
        raise ValueError("Invalid access token")

    # Получаем чат
    chatroom = await get_chat_by_name(chatroom_name)

    # Создаем сообщение
    message = await create_message(chatroom, user, text)

    # Уведомляем всех участников чата о новом сообщении
    await notify_new_message(chatroom_name, message)

    # Возвращаем новое сообщение
    return message
