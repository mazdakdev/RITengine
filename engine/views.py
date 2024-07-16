from .models import Chat, Engine, Message
from rest_framework.views import APIView
from rest_framework import generics
from django.http import StreamingHttpResponse
from django.conf import settings
from openai import AsyncOpenAI
from .serializers import StreamGeneratorSerializer, EngineSerializer
from rest_framework.response import Response
from rest_framework import status

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


class StreamGeneratorView(APIView):
    async def chatter(self, initial_prompt, message, model="gpt-4"):
        stream = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": initial_prompt},
                {"role": "user", "content": message}
            ],
            stream=True,
        )

        for chunk in stream:
            yield chunk.choices[0].delta.content or ""

    async def post(self, request):
        serializer = StreamGeneratorSerializer(data=request.data)

        if serializer.is_valid():
            engine_id = serializer.validated_data["engine_id"]
            message = serializer.validated_data["message"]

            try:
                engine = Engine.objects.get(id=engine_id)
                prompt = engine.prompt

                chat = self.chatter(prompt, message, 'gpt-3.5-turbo')
                response = StreamingHttpResponse(chat, status=200, content_type='text/event-stream')
                response['Cache-Control'] = 'no-cache'
                return response

            except Engine.DoesNotExist:
                return Response({
                    "status": "error",
                    "details": "Engine does not exist",
                    "error_code": "error-engine-404"
                }
                , status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'status': 'error',
            'details': serializer.errors,
            'error_code': 'error-serializer-validation'
        }, status=status.HTTP_400_BAD_REQUEST)


class EngineListCreateView(generics.ListCreateAPIView):
    queryset = Engine.objects.all()
    serializer_class = EngineSerializer

class EngineDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Engine.objects.all()
    serializer_class = EngineSerializer


#TODO: login and save chats


