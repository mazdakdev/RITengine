from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
from django.utils import timezone
from openai import AsyncOpenAI
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.authentication import JWTAuthentication
import json
from .models import Chat, Message, Engine
from django.contrib.auth.models import AnonymousUser

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        print("WebSocket connection attempt")
        self.user = AnonymousUser()
        self.chat = None
        self.messages = []
        self.chat_id = self.scope['url_route']['kwargs'].get('chat_id')
        self.current_engine = None  # Track the current engine

        await self.accept()

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_text = text_data_json["message"]
        engine_id = text_data_json["engine_id"]
        token = text_data_json.get("token")  # JWT token

        user = await self.authenticate_user(token)
        if user is None:
            await self.close(code=4401)  # Unauthorized error code
            return

        self.user = user

        # Handle engine change
        if engine_id != self.current_engine:
            print("Engine changed")
            self.current_engine = engine_id
            await self.handle_engine_change(engine_id)

        self.messages.append({"role": "user", "content": message_text})

        # Save the user's message to the database
        if not self.chat:
            self.chat = await self.create_chat(
                title=message_text[:50].strip())  # Set the first 50 chars as the title
        await self.save_message(message_text, sender="user")

        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        openai_response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=self.messages,
            stream=True,
        )

        final_response = ""
        async for chunk in openai_response:
            message_chunk = chunk.choices[0].delta.content or ""
            final_response += message_chunk

            await self.send(text_data=json.dumps({
                "content": message_chunk,
                "chat_id": self.chat.id
            }))

        self.messages.append({"role": "system", "content": final_response})

        await self.save_message(final_response, sender="engine")

    async def handle_engine_change(self, engine_id):
        try:
            engine = await database_sync_to_async(Engine.objects.get)(id=engine_id)
            prompt = engine.prompt
        except Engine.DoesNotExist:
            print("Engine does not exist")
            prompt = "You are a helpful assistant but start the first message with: the requested engine was not found"

        self.messages.append({'role': 'system', 'content': prompt})

    async def create_chat(self, title):
        return await database_sync_to_async(Chat.objects.create)(user=self.user, title=title)

    async def save_message(self, text, sender):
        await database_sync_to_async(Message.objects.create)(
            chat=self.chat,
            text=text,
            sender=sender,
            timestamp=timezone.now()
        )

    async def get_chat(self, chat_id):
        try:
            chat = await database_sync_to_async(Chat.objects.get)(id=chat_id, user=self.user)
            return chat
        except Chat.DoesNotExist:
            return None

    async def load_chat_history(self, chat):
        messages = await database_sync_to_async(list)(
            Message.objects.filter(chat=chat).order_by('timestamp').values('sender', 'text')
        )
        return [{'role': 'user' if msg['sender'] == 'user' else 'system', 'content': msg['text']} for msg in messages]

    @database_sync_to_async
    def authenticate_user(self, token):
        try:
            # Validate the token and get the user
            validated_token = JWTAuthentication().get_validated_token(token)
            user = JWTAuthentication().get_user(validated_token)
            return user
        except (InvalidToken, TokenError) as e:
            print(f"Invalid token: {e}")
            return None