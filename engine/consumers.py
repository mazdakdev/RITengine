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
        self.messages = [
            {
                'role': 'system', 'content': (
                    "You are an expert assistant specializing in the field of inventions and innovations.\n"
                    "Users will present questions, indicated after 'msg:'.\n"
                    "Additionally, you’ll receive a list of prompts in a Python list format that represent filters or themes to consider when answering.\n"
                    "If there’s only one prompt, use it as the main guide for your response.\n"
                    "If there are multiple prompts, combine them to formulate a comprehensive answer.\n"
                    "User’s Question:\n"
                    "msg: {message}\n\n"
                    "Prompts to Consider:\n"
                    "prompts: {prompts}"
                )
            }
        ]
        self.slug = self.scope['url_route']['kwargs'].get('slug')
        await self.accept()

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_text = data.get("message")
        engines_list = data.get("engines_list")
        token = data.get("token")

        user = await self.authenticate_user(token)
        if user is None:
            await self.close(code=4401)  # Unauthorized
            return

        self.user = user
        if self.slug:
            self.chat = await self.get_chat(self.slug)
            if not self.chat:
                await self.send(text_data=json.dumps({"error": "Chat not found."}))
                await self.close(code=4404)  # Not Found
                return
            self.messages = await self.load_chat_history(self.chat)
        else:
            self.chat = await self.create_chat(title=message_text[:50].strip())
            self.slug = self.chat.slug

        await self.save_message(message_text, sender="user")
        final_msg = await self.get_final_prompt(message_text, engines_list)
        self.messages.append({"role": "user", "content": final_msg})

        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        openai_response = await client.chat.completions.create(
            messages=self.messages,
            model="gpt-4o",
            stream=True,
        )

        async for chunk in openai_response:
            message_chunk = chunk.choices[0].delta.content
            if message_chunk:
                await self.send(text_data=json.dumps({
                    "content": message_chunk,
                    "slug": self.slug
                }))

    async def create_chat(self, title):
        return await database_sync_to_async(Chat.objects.create)(user=self.user, title=title)

    async def save_message(self, text, sender):
        await database_sync_to_async(Message.objects.create)(
            chat=self.chat,
            text=text,
            sender=sender,
            timestamp=timezone.now()
        )

    async def get_chat(self, slug):
        try:
            return await database_sync_to_async(Chat.objects.get)(slug=slug, user=self.user)
        except Chat.DoesNotExist:
            return None

    async def load_chat_history(self, chat):
        messages = await database_sync_to_async(list)(
            Message.objects.filter(chat=chat).order_by('timestamp').values('sender', 'text')
        )
        return [{'role': 'user' if msg['sender'] == 'user' else 'system', 'content': msg['text']} for msg in messages]

    async def get_final_prompt(self, message, engines_list):
        prompts = await database_sync_to_async(list)(
            Engine.objects.filter(id__in=engines_list).values_list('prompt', flat=True)
        )
        return f"msg: {message}\nprompts: {prompts}"

    @database_sync_to_async
    def authenticate_user(self, token):
        try:
            validated_token = JWTAuthentication().get_validated_token(token)
            return JWTAuthentication().get_user(validated_token)
        except (InvalidToken, TokenError) as e:
            print(f"Invalid token: {e}")
            return None
