from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from openai import AsyncOpenAI
import json
from .models import Chat, Message, Engine
from django.contrib.auth.models import AnonymousUser


User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        print("WebSocket connection attempt")
        self.user = self.scope.get("user", AnonymousUser())
        if not self.user.is_authenticated:
            print("User not authenticated")
            await self.accept()
            await self.close(code=4401)  # Close with a custom error code for unauthorized access
            return

        print("User authenticated:", self.user)
        self.chat = None
        self.messages = []
        self.chat_id = self.scope['url_route']['kwargs'].get('chat_id')
        self.current_engine = None  # Track the current engine

        if self.chat_id:
            # Load existing chat if chat_id is provided
            self.chat = await self.get_chat(self.chat_id)
            if self.chat:
                self.messages = await self.load_chat_history(self.chat)
            else:
                # If chat_id is invalid, send an error and close the connection
                await self.accept()
                await self.close(code=4000)  # Use a specific code for chat not found
                return

        await self.accept()

    async def disconnect(self, close_code):
        print("WebSocket disconnected with code:", close_code)
        await self.close()

    async def receive(self, text_data):
        if self.user.is_authenticated:
            text_data_json = json.loads(text_data)
            message_text = text_data_json["message"]
            engine_id = text_data_json["engine_id"]

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

            # Send the message to OpenAI and get the response in chunks
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


        # self.messages = []
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

#TODO: BUG: engine does not exists
#TODO: multiple engines
