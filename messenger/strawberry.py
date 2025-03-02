import asyncio
from collections import defaultdict
from datetime import datetime
from typing import Optional, List, AsyncGenerator, Dict, Set
from asyncio import Queue, create_task
from venv import logger

import jwt
import strawberry
from asgiref.sync import sync_to_async
from strawberry.types import Info

from messenger.middlewares import get_user_from_token
from messenger.models import Message


@strawberry.type
class UserTypeStrawberry:
    id: int
    name: str
    email: str
    avatar: Optional[str] = None
    chatroom: List['ChatroomTypeStrawberry']
    password: str
    created_at: datetime
    updated_at: datetime


@strawberry.type
class ChatroomTypeStrawberry:
    id: int
    name: str
    avatar: Optional[str] = None
    participants: List[UserTypeStrawberry]
    max_participants: int
    created_at: datetime
    updated_at: datetime

    @strawberry.field
    def messages(self, info) -> List['MessageTypeStrawberry']:
        # Получение сообщений для чата
        return Message.objects.filter(chatroom_id=self.id).order_by('created_at')

    @strawberry.field
    def max_participants_count(self) -> int:
        return self.max_participants


@strawberry.type
class MessageTypeStrawberry:
    id: strawberry.ID
    chatroom: ChatroomTypeStrawberry
    user: UserTypeStrawberry
    text: str
    is_chat: bool
    is_favorite: bool
    created_at: datetime
    updated_at: datetime


@strawberry.type
class ResponseTypeStrawberry:
    message: str


@strawberry.type
class MessagesCountType:
    count: int


class ChatroomMessagesSubscription:
    def __init__(self):
        self.queues: Dict[str, Set[Queue]] = defaultdict(set)

    def add_subscriber(self, chatroom_name: str, queue: Queue):
        self.queues[chatroom_name].add(queue)

    def remove_subscriber(self, chatroom_name: str, queue: Queue):
        if chatroom_name in self.queues:
            self.queues[chatroom_name].discard(queue)
            if not self.queues[chatroom_name]:
                del self.queues[chatroom_name]

    async def notify_subscribers(self, chatroom_name: str, message: MessageTypeStrawberry):
        if chatroom_name in self.queues:
            dead_queues = set()
            for queue in self.queues[chatroom_name]:
                try:
                    await queue.put(message)
                except asyncio.QueueFull:
                    dead_queues.add(queue)
            for queue in dead_queues:
                self.remove_subscriber(chatroom_name, queue)


chatroom_messages_subscriptions = ChatroomMessagesSubscription()


class ChatroomSubscriptions:
    def __init__(self):
        self._subscribers: Dict[int, Queue] = {}  # user_id -> Queue

    async def subscribe(self, user_id: int) -> Queue:
        """Создает новую подписку для пользователя"""
        if user_id not in self._subscribers:
            self._subscribers[user_id] = Queue()
        return self._subscribers[user_id]

    async def unsubscribe(self, user_id: int):
        """Удаляет подписку пользователя"""
        if user_id in self._subscribers:
            del self._subscribers[user_id]

    async def notify_subscribers(self, chatroom):
        """Уведомляет всех подписчиков о новом чате"""
        for user_id, queue in self._subscribers.items():
            try:
                await queue.put(chatroom)
            except Exception as e:
                print(f"Error notifying user {user_id} about new chatroom: {e}")


chatroom_subscribers = ChatroomSubscriptions()


@strawberry.type
class Query:
    @strawberry.field
    async def get_messages(self, info: Info, chatroom_name: str, before_id: Optional[int] = None, limit: Optional[int] = 100) -> List[MessageTypeStrawberry]:
        # Используем select_related для user и chatroom, и prefetch_related для связанных полей
        query = Message.objects.filter(chatroom__name=chatroom_name)

        # Добавляем фильтрацию по before_id в SQL запрос
        if before_id is not None:
            message = await sync_to_async(Message.objects.get)(id=before_id)
            query = query.filter(created_at__lt=message.created_at)

        # Применяем сортировку и лимит
        messages = await sync_to_async(list)(
            query
            .select_related('user', 'chatroom')
            .prefetch_related('chatroom__participants', 'user__chatroom')
            .order_by('-created_at')
            [:limit]  # Применяем лимит здесь
        )

        result = []

        for message in messages:
            # Теперь эти данные уже предзагружены
            participants = list(message.chatroom.participants.all())
            user_chatrooms = list(message.user.chatroom.all())

            message_obj = MessageTypeStrawberry(
                id=message.id,
                chatroom=ChatroomTypeStrawberry(
                    id=message.chatroom.id,
                    name=message.chatroom.name,
                    avatar=message.chatroom.avatar,
                    participants=participants,
                    max_participants=message.chatroom.max_participants,
                    updated_at=message.chatroom.updated_at,
                    created_at=message.chatroom.created_at
                ),
                user=UserTypeStrawberry(
                    id=message.user.id,
                    name=message.user.name,
                    email=message.user.email,
                    password=message.user.password,
                    avatar=message.user.avatar,
                    chatroom=user_chatrooms,
                    created_at=message.user.created_at,
                    updated_at=message.user.updated_at
                ),
                text=message.text,
                is_chat=message.is_chat,
                is_favorite=message.is_favorite,
                created_at=message.created_at,
                updated_at=message.updated_at,
            )
            result.append(message_obj)

        return result


@strawberry.type
class Mutation:
    @strawberry.mutation
    async def send_message(self, info: Info, access_token: str, chatroom_name: str, text: str) -> MessageTypeStrawberry:
        from messenger.resolvers.message_resolver import resolve_send_message
        message = await resolve_send_message(self, info, access_token, chatroom_name, text)
        return MessageTypeStrawberry(
            id=message.id,
            chatroom=message.chatroom,
            user=message.user,
            text=message.text,
            is_chat=message.is_chat,
            is_favorite=message.is_favorite,
            created_at=message.created_at,
            updated_at=message.updated_at,
        )

    @strawberry.mutation
    async def change_message(self, info: Info, access_token: str, chatroom_name: str, message_id: strawberry.ID,
                       new_text: Optional[str] = None) -> ResponseTypeStrawberry:
        user = sync_to_async(get_user_from_token)(access_token)
        message = sync_to_async(Message.objects.filter(id=message_id).first())

        if user == message.user:
            message.is_read = True
            message.save()

            if new_text:
                message.text = new_text
                message.save()

            await notify_new_message(chatroom_name, message)

            return ResponseTypeStrawberry("Сообщение успешно обновлено")
        else:
            return ResponseTypeStrawberry("У вас нет прав для изменения этого сообщения")

    @strawberry.mutation
    async def delete_message(self, info: Info, access_token: str, chatroom_name: str, message_id: strawberry.ID) -> ResponseTypeStrawberry:
        user = sync_to_async(get_user_from_token)(access_token)
        message = Message.objects.filter(id=message_id).first()
        await notify_new_message(chatroom_name, message)
        if user == message.user:
            message.delete()
            return ResponseTypeStrawberry("Сообщение успешно удалено")
        else:
            return ResponseTypeStrawberry("У вас нет прав для удаления этого сообщения")


@strawberry.type
class Subscription:
    @strawberry.subscription
    async def chatroom_message(self, info: Info, chatroom_names: List[str]) -> AsyncGenerator[MessageTypeStrawberry, None]:
        queue = Queue()

        for chatroom_name in chatroom_names:
            chatroom_messages_subscriptions.add_subscriber(chatroom_name, queue)

        try:
            while True:
                message = await queue.get()
                print(message)
                yield MessageTypeStrawberry(
                    id=message.id,
                    chatroom=ChatroomTypeStrawberry(
                        id=message.chatroom.id,
                        name=message.chatroom.name,
                        avatar=message.chatroom.avatar,
                        participants=message.chatroom.participants.all(),
                        max_participants=message.chatroom.max_participants,
                        updated_at=message.chatroom.updated_at,
                        created_at=message.chatroom.created_at
                    ),
                    user=UserTypeStrawberry(
                        id=message.user.id,
                        name=message.user.name,
                        email=message.user.email,
                        password=message.user.password,
                        avatar=message.user.avatar,
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
            chatroom_messages_subscriptions.remove_subscriber(chatroom_name, queue)
            raise
        finally:
            chatroom_messages_subscriptions.remove_subscriber(chatroom_name, queue)

    @strawberry.subscription
    async def new_chatroom(self, info: Info, access_token: str) -> AsyncGenerator[ChatroomTypeStrawberry, None]:
        try:
            user = await sync_to_async(get_user_from_token)(access_token)
            if not user:
                raise ValueError("Invalid access token")

            queue = asyncio.Queue()
            chatroom_queues[user.id] = queue

            try:
                while True:
                    chatroom = await queue.get()

                    # Проверяем, является ли пользователь участником
                    participants = await sync_to_async(list)(chatroom.participants)
                    if user in participants:
                        yield chatroom

            except asyncio.CancelledError:
                print(f"[User {user.id}] Subscription cancelled")
                raise

        except Exception as e:
            print(f"Error in subscription: {e}")
            raise

        finally:
            if user and user.id in chatroom_queues:
                del chatroom_queues[user.id]

    @strawberry.subscription
    async def updated_chatroom(self, info: Info, access_token: str) -> AsyncGenerator[ChatroomTypeStrawberry, None]:
        try:
            user = await sync_to_async(get_user_from_token)(access_token)
            if not user:
                raise ValueError("Invalid access token")

            queue = asyncio.Queue()
            chatroom_update_queues[user.id] = queue

            try:
                while True:
                    chatroom = await queue.get()
                    # Проверяем, является ли пользователь участником
                    participants = await sync_to_async(list)(chatroom.participants)
                    yield chatroom

            except asyncio.CancelledError:
                print(f"[User {user.id}] Update subscription cancelled")
                raise

        except Exception as e:
            print(f"Error in update subscription: {e}")
            raise

        finally:
            if user and user.id in chatroom_update_queues:
                del chatroom_update_queues[user.id]

    @strawberry.subscription
    async def deleted_chatroom(self, info: Info, access_token: str) -> AsyncGenerator[ChatroomTypeStrawberry, None]:
        try:
            user = await sync_to_async(get_user_from_token)(access_token)
            if not user:
                raise ValueError("Invalid access token")

            queue = asyncio.Queue()
            chatroom_delete_queues[user.id] = queue

            try:
                while True:
                    chatroom = await queue.get()
                    # Проверяем, является ли пользователь участником
                    participants = await sync_to_async(list)(chatroom.participants)
                    yield chatroom

            except asyncio.CancelledError:
                print(f"[User {user.id}] Delete subscription cancelled")
                raise

        except Exception as e:
            print(f"Error in delete subscription: {e}")
            raise

        finally:
            if user and user.id in chatroom_delete_queues:
                del chatroom_delete_queues[user.id]


message_queues = {}
chatroom_queues = {}
chatroom_update_queues = {}
chatroom_delete_queues = {}
message_ready_event = asyncio.Event()


async def notify_new_message(chatroom_name: str,  message: MessageTypeStrawberry):
    await chatroom_messages_subscriptions.notify_subscribers(chatroom_name, message)


async def notify_new_chatroom(chatroom: ChatroomTypeStrawberry):
    try:
        subscriber_ids = list(chatroom_queues.keys())

        for user_id in subscriber_ids:
            try:
                queue = chatroom_queues.get(user_id)
                if queue:
                    await queue.put(chatroom)
            except Exception as e:
                print(f"Error notifying user {user_id}: {e}")

    except Exception as e:
        raise


async def notify_chatroom_update(chatroom: ChatroomTypeStrawberry):
    try:
        subscriber_ids = list(chatroom_update_queues.keys())

        for user_id in subscriber_ids:
            try:
                queue = chatroom_update_queues.get(user_id)
                if queue:
                    await queue.put(chatroom)
            except Exception as e:
                print(f"Error notifying user {user_id}: {e}")

    except Exception as e:
        raise


async def notify_chatroom_delete(chatroom: ChatroomTypeStrawberry):
    try:
        subscriber_ids = list(chatroom_delete_queues.keys())
        for user_id in subscriber_ids:
            try:
                print('1')
                queue = chatroom_delete_queues.get(user_id)
                if queue:
                    print('2')
                    await queue.put(chatroom)
            except Exception as e:
                print(f"Error notifying user {user_id}: {e}")

    except Exception as e:
        raise


schema = strawberry.Schema(query=Query, mutation=Mutation, subscription=Subscription)