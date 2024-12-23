from django.core.exceptions import ValidationError
from django.db import models


class User(models.Model):
    name = models.CharField(max_length=255, unique=True)
    email = models.CharField(max_length=255, unique=True)
    password = models.CharField(max_length=255)
    avatar = models.ImageField(upload_to='avatars/user/', null=True, blank=True, default=None)
    chatroom = models.ManyToManyField('Chatroom', null=True, related_name='chatrooms_with_users', blank=True, default=None)
    chat = models.ManyToManyField('Chat', null=True, related_name='chats_with_users', blank=True, default=None)
    favorite = models.ManyToManyField('Favorite', null=True, related_name='favorite_for_user', blank=True, default=None)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Chatroom(models.Model):
    name = models.CharField(max_length=255)
    avatar = models.ImageField(upload_to='avatars/chat/', null=True, blank=True, default=None)
    participants = models.ManyToManyField('User', null=True, related_name='chatrooms')
    max_participants = models.PositiveIntegerField(default=8, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def get_messages(self):
        return Message.objects.filter(chat=self).order_by('created_at')

    def get_max_participants(self):
        return self.max_participants

    def get_name(self):
        return self.name

    def clean(self):
        # Если объект уже сохранен, выполняем проверку
        if self.pk is not None:
            # Проверка: количество участников не превышает максимальное
            if self.participants.count() > self.max_participants:
                raise ValidationError(f"Количество участников не может превышать {self.max_participants}.")


class Chat(Chatroom):
    def __init__(self, *args, **kwargs):
        # Вызываем конструктор родительского класса, без переопределения поля
        super().__init__(*args, **kwargs)

    def get_max_participants(self):
        return 2  # Переопределяем для Chat

    def __str__(self):
        return f"Chat: {self.name}"


class Favorite(Chatroom):
    def __init__(self, *args, **kwargs):
        # Вызываем конструктор родительского класса, без переопределения поля
        super().__init__(*args, **kwargs)

    def get_max_participants(self):
        return 1  # Переопределяем для Chat

    def get_name(self):
        return self.participants.first().name

    def __str__(self):
        return f"Chat: {self.name}"


class Message(models.Model):
    chatroom = models.ForeignKey('Chatroom', on_delete=models.CASCADE, null=True, blank=True, default=None, related_name='message_to_chatroom')
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_chat = models.BooleanField(default=False)
    is_favorite = models.BooleanField(default=False)

    def __str__(self):
        return f"Message: {self.user} to {self.chatroom} with text: {self.text}"

    def save(self, *args, **kwargs):

        if isinstance(self.chatroom, Chatroom):
            self.is_chat = False
            self.is_favorite = False

        if isinstance(self.chatroom, Favorite):
            self.is_chat = False
            self.is_favorite = True

        if isinstance(self.chatroom, Chat):
            self.is_chat = True
            self.is_favorite = False

        super().save(*args, **kwargs)

