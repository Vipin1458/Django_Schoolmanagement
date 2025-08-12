# chat/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.shortcuts import get_object_or_404
from .models import Conversation, Message
from .serializers import MessageSerializer

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]
        self.room_group_name = f"chat_{self.conversation_id}"

        user = self.scope.get("user")
        if not user or not user.is_authenticated:
            await self.close()
            return

        # Check if user is participant
        is_participant = await self.user_in_conversation(user, self.conversation_id)
        if not is_participant:
            await self.close()
            return

        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_text = data.get("text")

        if not message_text:
            return

        user = self.scope["user"]
        msg = await self.save_message(user, self.conversation_id, message_text)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": MessageSerializer(msg).data
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            "type": "chat.message",
            "message": event["message"]
        }))

    @database_sync_to_async
    def user_in_conversation(self, user, conversation_id):
        try:
            conv = Conversation.objects.get(id=conversation_id)
            if user.is_staff:
                return True
            if hasattr(user, "teacher") and conv.teacher == user.teacher:
                return True
            if hasattr(user, "student") and conv.student == user.student:
                return True
            return False
        except Conversation.DoesNotExist:
            return False

    @database_sync_to_async
    def save_message(self, user, conversation_id, text):
        conv = Conversation.objects.get(id=conversation_id)
        return Message.objects.create(conversation=conv, sender=user, text=text)
