from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from openai import AsyncOpenAI
import json
import uuid
from .models import Chat, Message, Engine

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        self.chat = await self.create_chat()
        self.messages = []
        await self.accept()

    async def disconnect(self, close_code):
        await self.close()

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_text = text_data_json["message"]
        engine_id = text_data_json["engine_id"]

        try:
            engine = await database_sync_to_async(Engine.objects.create)(id=engine_id)
            prompt = engine.prompt

        except Engine.DoesNotExist:
            print("engine does not exist")
            prompt("You are a helpful assistant but start the first message with: the requested engine was not found")


        self.messages.append({'role':'system', 'content':prompt})
        self.messages.append({"role": "user", "content": message_text})

        # Save the user's message to the database
        await self.save_message(message_text, sender="user")



        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        # Send the message to OpenAI and get the response in chunks
        openai_response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=self.messages,
            stream=True,
        )

        chunks = []
        async for chunk in openai_response:
            message_chunk = chunk.choices[0].delta.content or ""
            chunks.append(message_chunk)

        # Concatenate all the chunks to form the final response message
        final_response = "".join(chunks)


        self.messages.append({"role": "system", "content": final_response})

        # Save the OpenAI response to the database
        await self.save_message(final_response, sender="engine")

        # Send the OpenAI response back to the WebSocket client
        await self.send(text_data=json.dumps({
            "content": final_response,
        }))

    async def create_chat(self):
        return await database_sync_to_async(Chat.objects.create)(user=self.user)

    async def save_message(self, text, sender):
        await database_sync_to_async(Message.objects.create)(
            chat=self.chat,
            text=text,
            sender=sender,
            timestamp=timezone.now()
        )
