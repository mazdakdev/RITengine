from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
from django.utils import timezone
from openai import AsyncOpenAI
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.authentication import JWTAuthentication
import json
from .models import Chat, Message, Engine, EngineCategory
import requests

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
        reply_to_id = data.get("reply_to")

        self.user = await self.authenticate_user(token)

        if self.user:
            reply_to_text = None
            reply_to_message = None
            if reply_to_id:
                reply_to_message = await self.get_message_by_id(reply_to_id)
                if reply_to_message:
                    reply_to_text = reply_to_message.text

            final_msg, initial_prompt = await self.get_final_prompt(message=message_text, engines_list=engines_list, reply_to_text=reply_to_text)

            print(final_msg)

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

            await self.save_message(message_text, sender="user", engine_ids=engines_list, reply_to=reply_to_message)
            self.messages.append({"role": "user", "content": final_msg})

            client = AsyncOpenAI()
            openai_response = await client.chat.completions.create(
                messages=self.messages,
                model=settings.OPENAI_MODEL,
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

            engine_msg = await self.save_message(final_response, "engine", engines_list)
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
    def save_message(self, text, sender, engine_ids, reply_to=None):
        """
        Save the base form of the message to the db
        """
        engines = Engine.objects.filter(id__in=engine_ids)

        message = Message.objects.create(
            chat=self.chat,
            text=text,
            sender=sender,
            timestamp=timezone.now(),
            reply_to=reply_to
        )

        message.engines.set(engines)

        return message

    @database_sync_to_async
    def get_chat(self, slug):
        try:
            return Chat.objects.get(slug=slug, user=self.user)
        except Chat.DoesNotExist:
            return None

    @database_sync_to_async
    def get_message_by_id(self, message_id):
        try:
            return Message.objects.get(id=message_id)
        except Message.DoesNotExist:
            return None

    @database_sync_to_async
    def load_chat_history(self, chat):
        """
        returns the chat history in a format readable
        by chatgpt context based API
        """
        messages = Message.objects.filter(chat=chat).order_by('timestamp').values('sender', 'text')
        return [{'role': 'user' if msg['sender'] == 'user' else 'system', 'content': msg['text']} for msg in messages]

    @database_sync_to_async
    def fetch_engine_data(self, engines_list):
        """
        return prompts and categories of given engines by their id
        """
        engines = Engine.objects.filter(id__in=engines_list).select_related('category')
        engine_prompts = [prompt for prompt in engines.values_list('prompt', flat=True) if prompt]
        categories = list(engines.values_list('category__id', 'category__prompt').distinct())

        return engine_prompts, categories

    async def get_final_prompt(self, message, engines_list, reply_to_text=""):
        """
        return the prompt of category and the prompt of each engine if needed.
        in scenarios where external services like darkob is required,
        the engine prompts would be empty and thus the data would be retrieved
        dynamically by their adapter.
        """
        engine_prompts, categories = await self.fetch_engine_data(engines_list)

        if len(categories) > 1:
            await self.close(code=4400, reason="All engines must be in the same category.")
            return None, None

        category_id, category_prompt = categories[0] if categories else (None, None)

        if not category_id:
            await self.close(code=4404, reason="Category not found.")
            return None, None

        category = await database_sync_to_async(EngineCategory.objects.get)(id=category_id)
        service_adapter = category.get_service_adapter()

        if service_adapter:
            patents_data = await service_adapter.perform_action(message)
            final_prompt = await self.generate_prompt(message=message, other_data=patents_data, in_reply_to=reply_to_text)
        else:
            if not engine_prompts:
                await self.close(code=4404, reason="engines are empty.")
                return None, None

            final_prompt = await self.generate_prompt(message=message, other_data=engine_prompts, in_reply_to=reply_to_text)

        return final_prompt, category_prompt

    @database_sync_to_async
    def authenticate_user(self, token):
        try:
            validated_token = JWTAuthentication().get_validated_token(token)
            return JWTAuthentication().get_user(validated_token)

        except (InvalidToken, TokenError):
            return None

    async def generate_prompt(self, message, other_data, in_reply_to=""):
        """
        generate the finalized message to give to chatgpt.
        """
        if in_reply_to:
            return f"msg: {message}\n\nother_data: {str(other_data)}\n\nin_reply_to: {in_reply_to}"
        return f"msg: {message} \n\n other_data: {str(other_data)}"
