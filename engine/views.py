from django.http import StreamingHttpResponse
from django.conf import settings
import openai

from rest_framework.views import APIView

openai.api_key = settings.OPENAI_API_KEY

class StreamGeneratorView(APIView):

    def openaichatter(self, message):
        stream = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": message}],
            stream=True,
        )

        for chunk in stream:
            yield chunk.choices[0].delta.content or ""

    def get(self, request):
        message = 'Send a greetings message for me and ask me to ask you a question to continue a conversation'
        chat = self.openaichatter(message)
        response = StreamingHttpResponse(chat, status=200, content_type='text/event-stream')
        response['Cache-Control'] = 'no-cache'
        return response

    def post(self, request):
        message = request.data.get('message', 'Send a greetings message for me and ask me to ask you a question to continue a conversation')
        chat = self.openaichatter(message)
        response = StreamingHttpResponse(chat, status=200, content_type='text/event-stream')
        return response