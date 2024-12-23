from django.db.models import Q
from graphql import GraphQLError
from graphql_jwt.decorators import login_required

from messenger.models import Chatroom, User, Chat, Favorite
from messenger.resolvers.user_resolver import isAuthorized


def resolve_user_chatrooms(self, info, user_id):
    isAuthorized(info)
    return Chatroom.objects.filter(participants=user_id)


def resolve_filter_chatroom(self, info, search_query, total=5):
    isAuthorized(info)
    chats = Chatroom.objects.filter(name__icontains=search_query)[:total]
    return chats


def resolve_filter_not_created_chats(self, info, this_user_id, filter_name, total=5):
    # Получаем текущего пользователя
    try:
        this_user = User.objects.get(id=this_user_id)
    except User.DoesNotExist:
        raise GraphQLError("Invalid user id")

    chat_participants = Chat.objects.filter(name__icontains=filter_name, participants=this_user) \
        .values_list('name', flat=True) \
        .distinct()

    # Получаем всех пользователей, чьи имена соответствуют фильтру
    filtered_users = User.objects.filter(name__icontains=filter_name).exclude(name=this_user.name)

    # Фильтруем пользователей, чьи имена уже есть среди участников чатов
    available_users = []
    for user in filtered_users:
        # Для каждого пользователя проверяем, встречается ли его имя в именах чатов
        if not any(user.name in chat_name for chat_name in chat_participants):
            available_users.append(user)

    # Ограничиваем выборку до total пользователей
    users_to_return = available_users[:total]

    return users_to_return


def resolve_chatroom_by_id(self, info, id):
    isAuthorized(info)
    return Chatroom.objects.get(id=id)


def resolve_chatroom_create(self, info, name, users):
    isAuthorized(info)
    try:
        user_ids = list(users.values())

        user_objects = [User.objects.get(id=user_id) for user_id in user_ids]
        chatroom = Chatroom.objects.create(name=name)
        chatroom.participants.set(user_objects)
        return chatroom

    except User.DoesNotExist:
        raise GraphQLError("Invalid user id")

    except Chatroom.DoesNotExist:
        raise GraphQLError("Invalid chatroom type")

    except Exception as e:
        raise GraphQLError(f"An error occurred: {str(e)}")  # Обработка других ошибок


def resolve_chat_create(self, info, users):
    isAuthorized(info)
    try:
        user_ids = list(users.values())

        if len(user_ids) > 2:
            raise GraphQLError("Invalid number of users")

        if Chat.objects.filter(participants=user_ids[0]).filter(participants=user_ids[1]).distinct():
            raise GraphQLError("Chat already exists")

        user_objects = [User.objects.get(id=user_id) for user_id in user_ids]
        chat = Chat.objects.create()
        chat.participants.add(*user_objects)
        chat.name = f"{chat.participants.first().name} & {chat.participants.last().name}"
        chat.save()
        return chat

    except User.DoesNotExist:
        raise GraphQLError("Invalid user id")

    except Chat.DoesNotExist:
        raise GraphQLError("Invalid chat type")

    except Exception as e:
        raise GraphQLError(f"An error occurred: {str(e)}")  # Обработка других ошибок


def resolve_favorite_create(self, info, users):
    isAuthorized(info)
    try:
        user_ids = list(users.values())

        if len(user_ids) > 1:
            raise GraphQLError("Invalid number of users")

        if Favorite.objects.filter(participants=user_ids[0]).exists():
            raise GraphQLError("Favorite already exists")

        user_objects = [User.objects.get(id=user_id) for user_id in user_ids]

        favorite = Favorite.objects.create()
        favorite.participants.set(user_objects)
        return favorite

    except User.DoesNotExist:
        raise GraphQLError("Invalid user id")

    except Favorite.DoesNotExist:
        raise GraphQLError("Invalid favorite type")

    except Exception as e:
        raise GraphQLError(f"An error occurred: {str(e)}")  # Обработка других ошибок


def resolve_chatroom_update(self, info, id, users, name=None):
    isAuthorized(info)
    try:
        user_ids = list(users.values())
        chatroom = Chatroom.objects.filter(id=id).first()
        if chatroom.participants.all().count() + len(user_ids) > 8:
            raise GraphQLError("Invalid number of users")
        if name:
            chatroom.name = name
        user_objects = [User.objects.get(id=user_id) for user_id in user_ids]
        chatroom.participants.add(*user_objects)
        chatroom.save()
        return chatroom

    except User.DoesNotExist:
        raise GraphQLError("Invalid user id")

    except Chatroom.DoesNotExist:
        raise GraphQLError("Invalid chatroom type")

    except Exception as e:
        raise GraphQLError(f"An error occurred: {str(e)}")  # Обработка других ошибок


def resolve_chatroom_delete(self, info, id):
    isAuthorized(info)  # Проверка авторизации

    try:
        # Получаем объект чата по ID (если он существует)
        chatroom = Chatroom.objects.get(id=id)

        # Удаляем объект
        chatroom.delete()
        chatroom.save()

        return chatroom

    except Chatroom.DoesNotExist:
        raise GraphQLError("Chatroom not found")  # Ошибка, если чат не существует

    except Exception as e:
        raise GraphQLError(f"An error occurred: {str(e)}")  # Обработка других ошибок