from channels.db import database_sync_to_async
from django.utils import timezone
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import Chat, Message, Engine, EngineCategory

@database_sync_to_async
def save_message(chat, text, sender, engine_ids, reply_to=None):
    """
    Save a message to the database with the associated engines and reply-to message if provided.
    """
    engines = Engine.objects.filter(id__in=engine_ids)
    message = Message.objects.create(
        chat=chat,
        text=text,
        sender=sender,
        timestamp=timezone.now(),
        reply_to=reply_to
    )
    message.engines.set(engines)
    return message


@database_sync_to_async
def load_chat_history(chat):
    """
    Load the chat history and return it in a format suitable for the chat model (e.g., ChatGPT).
    """
    messages = Message.objects.filter(chat=chat).order_by('timestamp').values('sender', 'text')
    return [{'role': 'user' if msg['sender'] == 'user' else 'system', 'content': msg['text']} for msg in messages]

@database_sync_to_async
def fetch_engines(engines_list):
    """
    Fetch engines and their related categories by their IDs.
    """
    return list(Engine.objects.filter(id__in=engines_list).select_related('category'))

async def format_message(message, extra_data=[], in_reply_to=""):
    """
    Format the given data by combining the message with any additional data
    and reply-to text to give to chatGPT.
    """
    extra_data_str = str(extra_data)
    if in_reply_to:
        return f"msg: {message}\n\nextra_data: {extra_data_str}\n\nin_reply_to: {in_reply_to}"
    return f"msg: {message}\n\nextra_data: {extra_data_str}"

async def get_prompts(message, engines_list, reply_to_text=""):
    """
    Generate prompts by aggregating data from all engines, either from external services
    or internal prompts, and handling the associated category prompt.
    """
    if not engines_list:
        default_category = await database_sync_to_async(EngineCategory.objects.get)(is_default=True).prompt
        default_final_message = await format_message(message, in_reply_to=reply_to_text)
        return default_final_message, default_category, None

    engines = await fetch_engines(engines_list)
    if not engines:
        return None, None, "Engines not found."

    categories = {engine.category.id for engine in engines}
    if len(categories) > 1:
        return None, None, "All engines must be in the same category."

    # aggregating data from engines prompts or from their external services
    extra_data = []
    for engine in engines:
        if engine.external_service:
            service_adapter = engine.get_service_adapter()
            if service_adapter:
                data = await service_adapter.perform_action(message)
                extra_data.append(data)
        elif engine.prompt:
            extra_data.append({"filter": engine.prompt})

    if not extra_data:
        return None, None, "No valid prompts or external data found."

    category = engines[0].category
    final_message = await format_message(message, extra_data, reply_to_text)
    return final_message, category.prompt, None

@database_sync_to_async
def authenticate_user(token):
    """
    Authenticate the user by validating the provided JWT token.
    """
    try:
        validated_token = JWTAuthentication().get_validated_token(token)
        return JWTAuthentication().get_user(validated_token)
    except (InvalidToken, TokenError):
        return None
