from datetime import datetime
from typing import Optional, List, AsyncGenerator
from asyncio import Queue

import strawberry
from strawberry.types import Info

from messenger.models import Message, Chatroom, User, Chat
from messenger.resolvers.chatroom_resolver import get_id_from_token, resolve_filter_not_created_chats, \
    resolve_chatroom_by_id, resolve_user_chatrooms, resolve_filter_chatroom, resolve_chatroom_update, \
    resolve_chatroom_delete, resolve_favorite_create, resolve_chat_create, resolve_chatroom_create
from messenger.resolvers.user_resolver import isAuthorized, resolve_users, resolve_user_by_id, resolve_user_register, \
    resolve_user_login, resolve_update_user, resolve_access_token


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
class ChatType:
    id: int
    name: str
    avatar: Optional[str] = None
    participants: List[UserType]
    max_participants: int
    created_at: datetime
    updated_at: datetime


@strawberry.type
class FavoriteType:
    id = int
    name: str
    avatar: Optional[str] = None
    participants: List[UserType]
    max_participants: int
    created_at: datetime
    updated_at: datetime


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


@strawberry.input
class UserRegisterType:
    name: str
    email: str
    password: str
    avatar: Optional[str] = None


@strawberry.type
class UserRegisterResponseType:
    access_token: str
    refresh_token: str


@strawberry.type
class RefreshAccessTokenResponseType:
    access_token: str


@strawberry.input
class ChatroomCreateUsersType:
    user_2: Optional[int] = None
    user_3: Optional[int] = None
    user_4: Optional[int] = None
    user_5: Optional[int] = None
    user_6: Optional[int] = None
    user_7: Optional[int] = None
    user_8: Optional[int] = None


@strawberry.type
class Query:
    @strawberry.field
    async def helloWorld(self) -> str:
        return "Hello World"

    # @strawberry.field
    # async def users(self, info) -> List[UserType]:
    #     users = await resolve_users(self, info)
    #     return [
    #         UserType(
    #             id=user.id,
    #             name=user.name,
    #             email=user.email,
    #             avatar=user.avatar,
    #             chatroom=user.chatrooms.all(),
    #             password=user.password,  # Смотрите комментарий выше о защите пароля
    #             created_at=user.created_at,
    #             updated_at=user.updated_at,
    #         )
    #         for user in users
    #     ]
    #
    # @strawberry.field
    # async def user(self, info, id: int) -> UserType:
    #     user = await resolve_user_by_id(self, info, id)
    #     return UserType(
    #             id=user.id,
    #             name=user.name,
    #             email=user.email,
    #             avatar=user.avatar,
    #             chatroom=user.chatrooms.all(),
    #             password=user.password,
    #             created_at=user.created_at,
    #             updated_at=user.updated_at,
    #     )
    #
    # @strawberry.field
    # async def users_without_chat_with_this_user(self, info, search_query: str, total: int) -> List[UserType]:
    #     users = await resolve_filter_not_created_chats(self, info, search_query, total)
    #     return [
    #         UserType(
    #             id=user.id,
    #             name=user.name,
    #             email=user.email,
    #             avatar=user.avatar,
    #             chatroom=user.chatrooms.all(),
    #             password=user.password,  # Смотрите комментарий выше о защите пароля
    #             created_at=user.created_at,
    #             updated_at=user.updated_at,
    #         )
    #         for user in users
    #     ]
    #
    # @strawberry.field
    # async def user_chatrooms(self, info) -> List[ChatroomType]:
    #     chatrooms = await resolve_user_chatrooms(self, info)
    #     return [
    #         ChatroomType(
    #             id=chatroom.id,
    #             name=chatroom.name,
    #             avatar=chatroom.avatar,
    #             participants=chatroom.participants.all(),
    #             max_participants=chatroom.max_participants,
    #             created_at=chatroom.created_at,
    #             updated_at=chatroom.updated_at,
    #         )
    #         for chatroom in chatrooms
    #     ]
    #
    # @strawberry.field
    # async def chatroom(self, info, id: int) -> ChatroomType:
    #     chatroom = await resolve_chatroom_by_id(self, info, id)
    #     return ChatroomType(
    #         id=chatroom.id,
    #         name=chatroom.name,
    #         avatar=chatroom.avatar,
    #         participants=chatroom.participants.all(),
    #         max_participants=chatroom.max_participants,
    #         created_at=chatroom.created_at,
    #         updated_at=chatroom.updated_at,
    #     )
    #
    # @strawberry.field
    # async def filtered_chatrooms(self, info, search_query: str, total: int) -> List[ChatroomType]:
    #     chatrooms = await resolve_filter_chatroom(self, info, search_query, total)
    #     return [
    #         ChatroomType(
    #             id=chatroom.id,
    #             name=chatroom.name,
    #             avatar=chatroom.avatar,
    #             participants=chatroom.participants.all(),
    #             max_participants=chatroom.max_participants,
    #             created_at=chatroom.created_at,
    #             updated_at=chatroom.updated_at,
    #         )
    #         for chatroom in chatrooms
    #     ]


@strawberry.type
class Mutation:
    # @strawberry.mutation
    # async def user_register(self, info: Info, user: UserRegisterType) -> UserRegisterResponseType:
    #     result = await resolve_user_register(self, info, user)
    #
    #     return UserRegisterResponseType(
    #         access_token=result['access_token'],
    #         refresh_token=result['refresh_token']
    #     )
    #
    # @strawberry.mutation
    # async def user_login(self, info: Info, email: str, password: str) -> UserRegisterResponseType:
    #     result = await resolve_user_login(self, info, email, password)
    #
    #     return UserRegisterResponseType(
    #         access_token=result['access_token'],
    #         refresh_token=result['refresh_token']
    #     )
    #
    #
    # @strawberry.mutation
    # async def user_update(self, info: Info, access_token: str, new_user: UserRegisterType) -> UserRegisterResponseType:
    #     result = await resolve_update_user(self, info, access_token, new_user)
    #
    #     return UserRegisterResponseType(
    #         access_token=result['access_token'],
    #         refresh_token=result['refresh_token']
    #     )
    #
    # @strawberry.mutation
    # async def refresh_access_token(self, info: Info, refresh_token: str) -> RefreshAccessTokenResponseType:
    #     result = await resolve_access_token(self, info, refresh_token)
    #
    #     return RefreshAccessTokenResponseType(
    #         access_token=result['access_token']
    #     )
    #
    # @strawberry.mutation
    # async def chatroom_create(self, info: Info, name: str, users: ChatroomCreateUsersType) -> ChatroomType:
    #     chatroom = await resolve_chatroom_create(self, info, name, users)
    #     return ChatroomType(
    #         id=chatroom.id,
    #         name=chatroom.name,
    #         avatar=chatroom.avatar,
    #         participants=chatroom.participants.all(),
    #         max_participants=chatroom.max_participants,
    #         created_at=chatroom.created_at,
    #         updated_at=chatroom.updated_at,
    #     )
    #
    # @strawberry.mutation
    # async def chat_create(self, info: Info, user_name: str) -> ChatType:
    #     chat = await resolve_chat_create(self, info, user_name)
    #     return ChatType(
    #         id=chat.id,
    #         name=chat.name,
    #         avatar=chat.avatar,
    #         participants=chat.participants.all(),
    #         max_participants=chat.max_participants,
    #         created_at=chat.created_at,
    #         updated_at=chat.updated_at,
    #     )
    #
    # @strawberry.mutation
    # async def favorite_create(self, info: Info) -> FavoriteType:
    #     favorite = await resolve_favorite_create(self, info)
    #     return FavoriteType(
    #         id=favorite.id,
    #         name=favorite.name,
    #         avatar=favorite.avatar,
    #         participants=favorite.participants.all(),
    #         max_participants=favorite.max_participants,
    #         created_at=favorite.created_at,
    #         updated_at=favorite.updated_at,
    #     )
    #
    # @strawberry.mutation
    # async def chatroom_update(self, info: Info, id: int, name: str, users: ChatroomCreateUsersType) -> ChatroomType:
    #     chatroom = await resolve_chatroom_update(self, info, id, name, users)
    #     return ChatroomType(
    #         id=chatroom.id,
    #         name=chatroom.name,
    #         avatar=chatroom.avatar,
    #         participants=chatroom.participants.all(),
    #         max_participants=chatroom.max_participants,
    #         created_at=chatroom.created_at,
    #         updated_at=chatroom.updated_at,
    #     )
    #
    # @strawberry.mutation
    # async def chatroom_delete(self, info: Info, id: int) -> None:
    #     await resolve_chatroom_delete(self, info, id)
    #     return None

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

schema = strawberry.Schema(query=Query, mutation=Mutation, subscription=Subscription)