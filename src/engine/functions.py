import json
from openai import AsyncOpenAI
from .constants import EXTERNAL_SERVICE_FUNCTIONS
from django.conf import settings

with open('functions.json', 'r') as f:
    FUNCTIONS_CONFIG = json.load(f)

async def call_openai_function(messages, tool):
    """
    This function calls OpenAI's chat completion API.
    If tools and tool_choice are provided, it will pass them in the request.
    Otherwise, it performs a regular OpenAI completion.
    """
    
    if tool not in EXTERNAL_SERVICE_FUNCTIONS:
        raise ValueError(f"Error: '{tool}' is not a valid service function. Choose from: {EXTERNAL_SERVICE_FUNCTIONS}")

    tool_config = FUNCTIONS_CONFIG.get(tool)
    
    if not tool_config:
        raise ValueError(f"Error: '{tool}' does not have a valid configuration in the functions.json file.")

    client = AsyncOpenAI()

    response = await client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=messages,
        tools=tool_config,
        tool_choice="required",
    )

    return response.choices[0].message.tool_calls[0].function.arguments

# import asyncio

# # Example messages and tool
# messages = [
#     {"role": "system", "content": "You are a helpful assistant."},
#     {"role": "user", "content": "Tell me a joke."}
# ]
# tool = "google_patents_search"

# async def main():
#     try:
#         response = await call_openai_function(messages, tool)
#         print(response)
#     except ValueError as e:
#         print(e)

# # Run the main function
# asyncio.run(main())