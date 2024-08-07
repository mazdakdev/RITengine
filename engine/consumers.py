from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
from django.utils import timezone
from openai import AsyncOpenAI
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.authentication import JWTAuthentication
import json
from .models import Chat, Message, Engine

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        print("WebSocket connection attempt")
        self.messages = []
        self.slug = self.scope['url_route']['kwargs'].get('slug')
        await self.accept()

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_text = data.get("message")
        engines_list = data.get("engines_list")
        token = data.get("token")

        self.user = await self.authenticate_user(token)

        if self.user:
            final_msg, initial_prompt = await self.get_final_prompt(message_text, engines_list)
            if final_msg is None:
                return
            self.messages.append({"role": "system", "content": initial_prompt})

            if self.slug:
                self.chat = await self.get_chat(self.slug)
                if not self.chat:
                    await self.send(text_data=json.dumps({"error": "Chat not found."}))
                    await self.close(code=4404)
                    return
                self.messages = await self.load_chat_history(self.chat)

            else:
                self.chat = await self.create_chat(title=message_text[:50].strip())
                self.slug = self.chat.slug

            await self.save_message(message_text, sender="user")
            self.messages.append({"role": "user", "content": final_msg})

            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            openai_response = await client.chat.completions.create(
                messages=self.messages,
                model="gpt-3.5-turbo", #TODO: .env
                stream=True,
            )

            final_response = ""
            async for chunk in openai_response:
                message_chunk = chunk.choices[0].delta.content or ""
                final_response += message_chunk
                if message_chunk:
                    await self.send(text_data=json.dumps({
                        "content": message_chunk,
                        "slug": self.slug,
                        "is_ended": False
                    }))

            engine_msg = await self.save_message(final_response, sender="engine")
            await self.send(text_data=json.dumps({
                "content": "",
                "slug": self.slug,
                "message_id": engine_msg.id,
                "is_ended": True
            }))

            self.messages.append({"role": "system", "content": final_response})

        else:
            await self.close(code=4401, reason="JWT token is invalid or expired.")


    @database_sync_to_async
    def create_chat(self, title):
        return Chat.objects.create(user=self.user, title=title)

    @database_sync_to_async
    def save_message(self, text, sender):
        message = Message.objects.create(
            chat=self.chat,
            text=text,
            sender=sender,
            timestamp=timezone.now()
        )
        return message

    @database_sync_to_async
    def get_chat(self, slug):
        try:
            return Chat.objects.get(slug=slug, user=self.user)
        except Chat.DoesNotExist:
            return None

    @database_sync_to_async
    def load_chat_history(self, chat):
        messages = Message.objects.filter(chat=chat).order_by('timestamp').values('sender', 'text')
        return [{'role': 'user' if msg['sender'] == 'user' else 'system', 'content': msg['text']} for msg in messages]

    @database_sync_to_async
    def fetch_engine_data(self, engines_list):
        engines = Engine.objects.filter(id__in=engines_list).select_related('category')
        engine_prompts = list(engines.values_list('prompt', flat=True))
        category_prompts = list(engines.values_list('category__prompt', flat=True).distinct())
        categories = list(engines.values_list('category__id', flat=True).distinct())
        return engine_prompts, category_prompts, categories

    async def get_final_prompt(self, message, engines_list):
        engine_prompts, category_prompts, categories = await self.fetch_engine_data(engines_list)

        if not engine_prompts:
            await self.close(code=4404, reason="Engines not found.")
            return None, None

        if len(categories) > 1:
            await self.close(code=4400, reason="All engines must be in the same category.")
            return None, None

        category_prompt = category_prompts[0] if category_prompts else "No category prompt available."
        final_prompt = f"msg: {message}\n\n prompts: {engine_prompts}"

        return final_prompt, category_prompt

    @database_sync_to_async
    def authenticate_user(self, token):
        try:
            validated_token = JWTAuthentication().get_validated_token(token)
            return JWTAuthentication().get_user(validated_token)

        except (InvalidToken, TokenError):
            return None