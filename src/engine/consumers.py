from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.conf import settings
from openai import AsyncOpenAI
from .models import Chat, Message, EngineCategory
from .utils import save_message, authenticate_user, get_prompts, load_chat_history
import json
import asyncio

class ChatConsumer(AsyncWebsocketConsumer):
    TIMEOUT = 300

    async def connect(self):
        self.last_activity = asyncio.get_event_loop().time()
        self.messages = []
        self.slug = self.scope['url_route']['kwargs'].get('slug')

        self.timeout_task = asyncio.create_task(self.timeout_check())

        await self.accept()

    async def receive(self, text_data):
        self.last_activity = asyncio.get_event_loop().time()
        data = json.loads(text_data)
        message_text = data.get("message")
        engines_list = data.get("engines_list")
        token = data.get("token")
        reply_to_id = data.get("reply_to")

        self.user = await authenticate_user(token)
        if not self.user:
            await self.close(code=4401, reason="JWT token is invalid or expired.")
            return

        customer = await database_sync_to_async(lambda: getattr(self.user, 'customer', None))()
        if not customer or not await database_sync_to_async(customer.has_active_subscription)():
            await self.close(code=4429, reason="You must have an active subscription to use the chat.")
            return

        # Check if the user has reached the daily message limit
        messages_sent_today = await database_sync_to_async(lambda: customer.messages_sent_today)()
        messages_per_day = await database_sync_to_async(lambda: customer.subscription.plan.messages_limit)()
        if messages_sent_today >= messages_per_day:
            await self.close(code=4429, reason="You have reached the maximum number of messages allowed by your subscription plan.")
            return

        if not message_text:
            await self.close(code=4400, reason="Message not provided.")
            return

        # Validate engine categories based on the customer's plan
        allowed_engine_categories = await database_sync_to_async(lambda: list(customer.subscription.plan.engines_categories.all()))()
        if not all(engine in [category.id for category in allowed_engine_categories] for engine in engines_list):
            await self.close(code=4405, reason="One or more engine categories are not allowed by your subscription plan.")
            return

        # Handle reply-to logic
        reply_to_text = None
        reply_to_message = None
        if reply_to_id:
            try:
                reply_to_message = await database_sync_to_async(Message.objects.get)(
                    id=reply_to_id, chat__user=self.user
                )
                reply_to_text = reply_to_message.text
            except Message.DoesNotExist:
                await self.close(code=4404, reason="Reply-to message not found.")
                return

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
        customer.messages_sent_today += 1
        await database_sync_to_async(customer.save)()

        await self._generate_and_send_response(engines_list, reply_to_id)

    async def _retrieve_or_create_chat(self, message_text):
        if self.slug:
            try:
                self.chat = await database_sync_to_async(Chat.objects.get)(
                    slug=self.slug, user=self.user
                )
                self.messages = await load_chat_history(self.chat)
            except Chat.DoesNotExist:
                await self.close(code=4404, reason="Chat not found")
                return
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
            message_chunk = message_chunk.replace("CHATGPT", "RITengine").replace("chatgpt", "RITengine").replace("ChatGPT", "RITengine").replace("chatGPT", "RITengine")
            message_chunk = message_chunk.replace("OPENAI", "RIT team").replace("openai", "RIT team").replace("OpenAI", "RIT team").replace("openAI", "RIT team")
            message_chunk = message_chunk.replace("OPEN AI", "RIT team").replace("open ai", "RIT team").replace("Open AI", "RIT team").replace("open AI", "RIT team")

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

    async def timeout_check(self):
        while True:
            await asyncio.sleep(self.TIMEOUT)
            current_time = asyncio.get_event_loop().time()
            if current_time - self.last_activity > self.TIMEOUT:
                await self.close(code=4001, reason="closed due to inactivity.")
                break

    async def disconnect(self, close_code):
        self.messages = []
        # Cancel the timeout check task if it's running
        if hasattr(self, 'timeout_task'):
            self.timeout_task.cancel()
            try:
                await self.timeout_task
            except asyncio.CancelledError:
                pass
