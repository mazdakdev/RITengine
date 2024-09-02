from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.conf import settings
from openai import AsyncOpenAI
from .models import Chat, Message
from .utils import save_message, authenticate_user, get_prompts, load_chat_history
import json

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.messages = []
        self.slug = self.scope['url_route']['kwargs'].get('slug')
        await self.accept()

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_text = data.get("message")
        engines_list = data.get("engines_list")
        token = data.get("token")
        reply_to_id = data.get("reply_to")

        self.user = await authenticate_user(token)
        if not self.user:
            await self.close(code=4401, reason="JWT token is invalid or expired.")
            return

        if not message_text:
            await self.close(code=4400, reason="Message not provided.")
            return

        # Handle reply-to logic
        reply_to_text = None
        reply_to_message = None
        if reply_to_id:
            reply_to_message = await database_sync_to_async(Message.objects.get)(
                id=reply_to_id, chat__user=self.user
            )
            if reply_to_message:
                reply_to_text = reply_to_message.text

        final_msg, initial_prompt, error_message = await get_prompts(
            message_text, engines_list, reply_to_text
        )

        print(final_msg)

        if error_message:
            await self.close(code=4404, reason=error_message)
            return

        self.messages.append({"role": "system", "content": initial_prompt})

        await self._retrieve_or_create_chat(message_text)

        await save_message(self.chat, message_text, sender="user", engine_ids=engines_list, reply_to=reply_to_message)
        self.messages.append({"role": "user", "content": final_msg})

        await self._generate_and_send_response(engines_list, reply_to_id)

    async def _retrieve_or_create_chat(self, message_text):
        if self.slug:
            self.chat = await database_sync_to_async(Chat.objects.get)(
                slug=self.slug, user=self.user
            )
            if not self.chat:
                await self.close(code=4404, reason="Chat not found")
                return
            self.messages = await load_chat_history(self.chat)
        else:
            self.chat = await database_sync_to_async(Chat.objects.create)(
                user=self.user, title=message_text[:50].strip()
            )
            self.slug = self.chat.slug

    async def _generate_and_send_response(self, engines_list, reply_to_id):
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

        engine_msg = await save_message(
            self.chat, final_response, sender="engine", engine_ids=engines_list, reply_to=reply_to_id
        )
        await self.send(text_data=json.dumps({
            "content": "",
            "slug": self.slug,
            "message_id": engine_msg.id,
            "is_ended": True
        }))

        self.messages.append({"role": "system", "content": final_response})
