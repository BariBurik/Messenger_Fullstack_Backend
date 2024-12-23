from datetime import datetime
from typing import Optional, List, AsyncGenerator
from asyncio import Queue

import strawberry
from strawberry.types import Info

from messenger.models import Message
from messenger.resolvers.user_resolver import isAuthorized


@strawberry.type
class UserType:
    id: int
    name: str
    email: str
    avatar: Optional[str]
    chatrooms: List['ChatroomType']  # Связь с Chatroom
    created_at: datetime
    updated_at: datetime


@strawberry.type
class ChatroomType:
    id: int
    name: str
    avatar: Optional[str]
    participants: List[UserType]  # Связь с User
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
    created_at: str


@strawberry.type
class Subscription:
    @strawberry.subscription
    async def chatroom_message(self, info: Info, chatroom_name: str) -> AsyncGenerator[MessageType, None]:
        async for message in message_stream(chatroom_name, info):
            isAuthorized(info.context.get('request'))
            yield MessageType(
                id=message.id,
                chatroom=ChatroomType(
                    id=message.chatroom.id,
                    name=message.chatroom.name
                ),
                user=UserType(
                    id=message.user.id,
                    name=message.user.name
                ),
                text=message.text,
                created_at=message.created_at
            )


message_queues = {}


async def message_stream(chatroom_name: str, info: Info):
    if chatroom_name not in message_queues:
        message_queues[chatroom_name] = Queue()

    queue = message_queues[chatroom_name]

    while True:
        message = await queue.get()
        yield message


async def notify_new_message(chatroom_name: str, user: UserType, message: MessageType):
    if chatroom_name in message_queues:
        queue = message_queues[chatroom_name]
        queue.put_nowait({
            "room_name": chatroom_name,
            "current_user": user,
            "text": message
        })


@strawberry.type
class Query:
    @strawberry.field
    def hello(self) -> str:
        return "Hello, GraphQL!"


schema = strawberry.Schema(query=Query, subscription=Subscription)
