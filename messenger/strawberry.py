import asyncio
from datetime import datetime
from typing import Optional, List, AsyncGenerator
from asyncio import Queue, create_task
from venv import logger

import jwt
import strawberry
from strawberry.types import Info

from messenger.models import Message


@strawberry.type
class UserType:
    id: int
    name: str
    email: str
    avatar: Optional[str] = None
    chatroom: List['ChatroomType']
    password: str
    created_at: datetime
    updated_at: datetime


@strawberry.type
class ChatroomType:
    id: int
    name: str
    avatar: Optional[str] = None
    participants: List[UserType]
    max_participants: int
    created_at: datetime
    updated_at: datetime

    @strawberry.field
    def messages(self, info) -> List['MessageType']:
        # Получение сообщений для чата
        return Message.objects.filter(chatroom_id=self.id).order_by('created_at')

    @strawberry.field
    def max_participants_count(self) -> int:
        return self.max_participants



@strawberry.type
class MessageType:
    id: strawberry.ID
    chatroom: ChatroomType
    user: UserType
    text: str
    is_chat: bool
    is_favorite: bool
    created_at: datetime
    updated_at: datetime


@strawberry.type
class Query:
    @strawberry.field
    def hello(self) -> str:
        return 'Hello, World!'


@strawberry.type
class Mutation:
    @strawberry.mutation
    async def send_message(self, info: Info, chatroom_name: str, text: str) -> MessageType:
        from messenger.resolvers.message_resolver import resolve_send_message
        message = await resolve_send_message(self, info, chatroom_name, text)
        return MessageType(
            id=message.id,
            chatroom=message.chatroom,
            user=message.user,
            text=message.text,
            is_chat=message.is_chat,
            is_favorite=message.is_favorite,
            created_at=message.created_at,
            updated_at=message.updated_at,
        )


@strawberry.type
class Subscription:
    @strawberry.subscription
    async def chatroom_message(self, info: Info, chatroom_name: str) -> AsyncGenerator[MessageType, None]:
        if chatroom_name not in message_queues:
            message_queues[chatroom_name] = Queue()

        queue = message_queues[chatroom_name]

        try:
            while True:
                message = await queue.get()
                yield MessageType(
                    id=message.id,
                    chatroom=ChatroomType(
                        id=message.chatroom.id,
                        name=message.chatroom.name,
                        participants=message.chatroom.participants.all(),
                        max_participants=message.chatroom.max_participants,
                        updated_at=message.chatroom.updated_at,
                        created_at=message.chatroom.created_at
                    ),
                    user=UserType(
                        id=message.user.id,
                        name=message.user.name,
                        email=message.user.email,
                        password=message.user.password,
                        chatroom=message.user.chatroom.all(),
                        created_at=message.user.created_at,
                        updated_at=message.user.updated_at
                    ),
                    text=message.text,
                    is_chat=message.is_chat,
                    is_favorite=message.is_favorite,
                    created_at=message.created_at,
                    updated_at=message.updated_at,
                )
        except asyncio.CancelledError:
            raise


message_queues = {}
message_ready_event = asyncio.Event()


async def notify_new_message(chatroom_name: str, user: UserType, message: MessageType):
    if chatroom_name not in message_queues:
        message_queues[chatroom_name] = Queue()

    queue = message_queues[chatroom_name]
    await queue.put(message)


schema = strawberry.Schema(query=Query, mutation=Mutation, subscription=Subscription)