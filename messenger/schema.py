import graphene
from graphene_django.types import DjangoObjectType
from .models import User, Chat, Chatroom, Favorite, Message

from .resolvers.user_resolver import resolve_users, resolve_user_by_id, resolve_user_register, resolve_user_login, \
    resolve_update_user, resolve_access_token
from .resolvers.chatroom_resolver import resolve_chatroom_by_id, resolve_user_chatrooms, \
    resolve_chatroom_create, resolve_favorite_create, resolve_chat_create, \
    resolve_filter_chatroom, resolve_filter_not_created_chats


class UserType(DjangoObjectType):
    class Meta:
        model = User
        fields = ('id', 'name', 'email', 'avatar', 'chatroom', 'password', 'created_at', 'updated_at')


class ChatroomType(DjangoObjectType):
    class Meta:
        model = Chatroom
        fields = ('id', 'name', 'participants', 'max_participants', 'created_at', 'updated_at')


class ChatType(DjangoObjectType):
    class Meta:
        model = Chat
        fields = ('id', 'name', 'participants', 'max_participants', 'created_at', 'updated_at')


class FavoriteType(DjangoObjectType):
    class Meta:
        model = Favorite
        fields = ('id', 'name', 'participants', 'max_participants', 'created_at', 'updated_at')


class MessageType(DjangoObjectType):
    class Meta:
        model = Message
        fields = ('id', 'chatroom', 'user', 'text', 'is_chat', 'is_favorite', 'created_at', 'updated_at')


class UserRegisterType(graphene.InputObjectType):
    name = graphene.String()
    email = graphene.String()
    password = graphene.String()
    avatar = graphene.String(required=False)


class UserRegisterResponseType(graphene.ObjectType):
    access_token = graphene.String()
    refresh_token = graphene.String()


class RefreshAccessTokenResponseType(graphene.ObjectType):
    access_token = graphene.String()


# class ChatUnion(graphene.Union):
#     class Meta:
#         types = (ChatroomType, ChatType, FavoriteType)


class ChatroomCreateTypeOfChat(graphene.Enum):
    CHAT = 'chat'
    FAVORITE = 'favorite'
    CHATROOM = 'chatroom'


class ChatroomCreateUsersType(graphene.InputObjectType):
    user_1 = graphene.Int(required=True)  # обязательное поле
    user_2 = graphene.Int()  # опциональные поля
    user_3 = graphene.Int()
    user_4 = graphene.Int()
    user_5 = graphene.Int()
    user_6 = graphene.Int()
    user_7 = graphene.Int()
    user_8 = graphene.Int()


class Query(graphene.ObjectType):
    users = graphene.List(UserType, resolver=resolve_users)
    user = graphene.Field(UserType, id=graphene.Int(), resolver=resolve_user_by_id)
    users_without_chat_with_this_user = graphene.List(UserType, search_query=graphene.String(), total=graphene.Int(), resolver=resolve_filter_not_created_chats)

    user_chatrooms = graphene.List(ChatroomType, user_id=graphene.Int(), resolver=resolve_user_chatrooms)
    chatroom = graphene.Field(ChatroomType, id=graphene.Int(), resolver=resolve_chatroom_by_id)
    filtered_chatrooms = graphene.List(ChatroomType, total=graphene.Int(), search_query=graphene.String(), resolver=resolve_filter_chatroom)


class Mutation(graphene.ObjectType):
    user_register = graphene.Field(UserRegisterResponseType, user=graphene.Argument(UserRegisterType), required=True, resolver=resolve_user_register)
    user_login = graphene.Field(UserRegisterResponseType, email=graphene.String(), password=graphene.String(), required=True, resolver=resolve_user_login)
    user_update = graphene.Field(UserRegisterResponseType, access_token=graphene.String(), new_user=UserRegisterType(), resolver=resolve_update_user)
    refresh_access_token = graphene.Field(RefreshAccessTokenResponseType, refresh_token=graphene.String(), required=True, resolver=resolve_access_token)

    chatroom_create = graphene.Field(ChatroomType, name=graphene.String(), users=ChatroomCreateUsersType(),
                                     required=True,
                                     resolver=resolve_chatroom_create)
    chat_create = graphene.Field(ChatType, users=ChatroomCreateUsersType(), required=True,
                                     resolver=resolve_chat_create)
    favorite_create = graphene.Field(FavoriteType, users=ChatroomCreateUsersType(), required=True,
                                     resolver=resolve_favorite_create)


schema = graphene.Schema(query=Query, mutation=Mutation)
