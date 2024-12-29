from graphql import GraphQLError
from messenger.models import Chatroom, User, Chat, Favorite


def resolve_user_chatrooms(self, info):
    this_user = info.context.get('user')
    return Chatroom.objects.filter(participants=this_user.id)


def resolve_filter_chatroom(self, info, search_query=None, total=5):
    chats = Chat.objects.filter(name__icontains=search_query)[:total]
    return chats


def resolve_filter_not_created_chats(self, info, search_query=None, total=5):
    this_user_id = info.context.get('user').id

    try:
        this_user = User.objects.get(id=this_user_id)
    except User.DoesNotExist:
        raise GraphQLError("Invalid user id")

    chat_participants = Chat.objects.filter(name__icontains=search_query, participants=this_user) \
        .values_list('name', flat=True) \
        .distinct()

    # Получаем всех пользователей, чьи имена соответствуют фильтру
    filtered_users = User.objects.filter(name__icontains=search_query).exclude(name=this_user.name)

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
    return Chatroom.objects.get(id=id)


def resolve_chatroom_create(self, info, name, users):
    this_user_id = info.context.get('user').id
    try:
        user_ids = list(users.values())

        user_objects = [User.objects.get(id=user_id) for user_id in user_ids]
        user_objects += [this_user_id]
        chatroom = Chatroom.objects.create(name=name)
        chatroom.participants.set(user_objects)
        return chatroom

    except User.DoesNotExist:
        raise GraphQLError("Invalid user id")

    except Chatroom.DoesNotExist:
        raise GraphQLError("Invalid chatroom type")

    except Exception as e:
        raise GraphQLError(f"An error occurred: {str(e)}")  # Обработка других ошибок


def resolve_chat_create(self, info, user_name):
    this_user_id = info.context.get('user').id
    other_user_id = User.objects.get(name=user_name).id

    if not other_user_id:
        raise GraphQLError("Invalid user name")

    if this_user_id == other_user_id:
        raise GraphQLError("Cannot create chat with yourself")

    try:
        if Chat.objects.filter(participants=this_user_id).filter(participants=other_user_id).distinct():
            raise GraphQLError("Chat already exists")

        user_objects = [this_user_id, other_user_id]
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


def resolve_favorite_create(self, info):
    this_user_id = info.context.get('user')
    try:
        if Favorite.objects.filter(participants=this_user_id).exists():
            raise GraphQLError("Favorite already exists")

        favorite = Favorite.objects.create()
        favorite.participants.set([this_user_id])
        favorite.name = "Избранные"
        return favorite

    except User.DoesNotExist:
        raise GraphQLError("Invalid user id")

    except Favorite.DoesNotExist:
        raise GraphQLError("Invalid favorite type")

    except Exception as e:
        raise GraphQLError(f"An error occurred: {str(e)}")  # Обработка других ошибок


def resolve_chatroom_update(self, info, id, users=None, name=None, avatar=None):
    try:
        # Проверяем существование чата
        chatroom = Chatroom.objects.get(id=id)
        if not chatroom:
            raise GraphQLError("Chatroom does not exist")

        # Добавляем участников
        if users:
            user_ids = list(users.values())

            if chatroom.participants.all().count() + len(user_ids) > 8:
                raise GraphQLError("Invalid number of users")

            user_objects = [User.objects.get(id=user_id) for user_id in user_ids]
            chatroom.participants.add(*user_objects)

        # Обновляем имя чата
        if name:
            if  Chatroom.objects.filter(name=name).exists():
                raise GraphQLError("Chatroom already exists")
            Chatroom.objects.filter(name=name).exists()

        if avatar:
            chatroom.avatar = avatar

        chatroom.save()
        return chatroom

    except User.DoesNotExist:
        raise GraphQLError("Invalid user id")

    except Chatroom.DoesNotExist:
        raise GraphQLError("Invalid chatroom type")

    except Exception as e:
        raise GraphQLError(f"An error occurred: {str(e)}")  # Обработка других ошибок


def resolve_chatroom_delete(self, info, id):
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