from django.contrib import admin
from messenger.models import User, Chat, Chatroom, Favorite, Message


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    pass


@admin.register(Chatroom)
class ChatroomAdmin(admin.ModelAdmin):
    pass


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    pass


@admin.register(Favorite)
class FavoritesAdmin(admin.ModelAdmin):
    pass


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    pass
