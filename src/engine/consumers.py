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

        if not message_text:
            await self.close(code=4400, reason="message not provided.")

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
        Return the chat history in a format readable
        by chatgpt context based API
        """
        messages = Message.objects.filter(chat=chat).order_by('timestamp').values('sender', 'text')
        return [{'role': 'user' if msg['sender'] == 'user' else 'system', 'content': msg['text']} for msg in messages]

    @database_sync_to_async
    def fetch_engines(self, engines_list):
        """
        Fetch the engines and their related categories.
        """
        return list(Engine.objects.filter(id__in=engines_list).select_related('category'))

    async def get_final_prompt(self, message, engines_list, reply_to_text=""):
        """
        Return the final prompt by aggregating data from all engines, either via
        their external services or internal prompts.
        """

        if not engines_list:
            default_category = """تو یه دستیار هوشمند و تخصصی تو زمینه اختراعات و نوآوری‌ها هستی. فقط به سوالایی جواب بده که درباره اختراعات یا نوآوری‌ها باشه. اگه یکی یه سوال غیر از اینا پرسید، خیلی محترمانه بگو نمی‌تونی جواب بدی.

            هر وقت سوالی کاربرها ازت بپرسن، بعد از ‘msg:’ میاد. یادت نره هر پیامی که میگیری به هر زبانی بود، تو هم باید به همون زبون جواب بدی مثلا یا فارسی یا انگلیسی.

            راستی کاربر هارو راهنمایی کن که می‌تونن با تیک زدن گزینه های مختلف از سایدبار  قابلیت های مختلف بیشتری رو ببینن و بتونن با تو ایده هاشون رو بهتر و تخصصی تر تحلیل کنن.

            اینجا واست یه فرم کلی پیام دریافتی رو واست می‌زارم تا یاد بگیری چجوری هندلش کنی.
            راستی حواست باشه ارتباط بین تو و کاربر فقط در msg خلاصه می‌شه. پس بقیه داده هارو لو نده.


            msg: {پیامی که کاربر فرستاده}

            اگه کاربر بخواد از طریق برنامه رو یه پیامی ریپلای کنه، یه in_reply_to هم به این فرمت اضافه می‌شه تا بدونی رو تکست کدوم پیام داره ریپلای می‌کنه.

            مثلا:
            in_reply_to: {سلام}"""

            default_final_prompt = await self.generate_prompt(message, in_reply_to=reply_to_text)

            return default_final_prompt, default_category

        engines = await self.fetch_engines(engines_list)

        if not engines:
            await self.close(code=4404, reason="Engines not found.")
            return None, None

        categories = {engine.category.id for engine in engines}
        if len(categories) > 1:
            await self.close(code=4400, reason="All engines must be in the same category.")
            return None, None

        # Collect data from all engines, either from prompts or external services
        extra_data = []
        for engine in engines:
            if engine.external_service:
                service_adapter = engine.get_service_adapter()
                if service_adapter:
                    data = await service_adapter.perform_action(message)
                    extra_data.append(data)
            elif engine.prompt:
                extra_data.append({engine.name:engine.prompt})

        if not extra_data:
            await self.close(code=4404, reason="No valid prompts or external data found.")

        category = engines[0].category
        final_prompt = await self.generate_prompt(message, extra_data, reply_to_text)

        return final_prompt, category.prompt

    async def generate_prompt(self, message, extra_data="", in_reply_to=""):
        """
        Generate the final message to give to ChatGPT.
        """
        extra_data_str = str(extra_data)
        if in_reply_to:
            return f"msg: {message}\n\nextra_data: {extra_data_str}\n\nin_reply_to: {in_reply_to}"
        return f"msg: {message}\n\nextra_data: {extra_data_str}"

    @database_sync_to_async
    def authenticate_user(self, token):
        try:
            validated_token = JWTAuthentication().get_validated_token(token)
            return JWTAuthentication().get_user(validated_token)

        except (InvalidToken, TokenError):
            return None
