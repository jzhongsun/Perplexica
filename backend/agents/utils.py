import json
import os
import re
from datetime import datetime
from typing import Type, TypeVar, Any, Sequence
from pydantic import BaseModel
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.contents import ChatHistory, ChatMessageContent, AuthorRole

import logging
logger = logging.getLogger(__name__)

def parse_json_response(response: str) -> dict:
    # First try direct JSON parsing
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        # Try to extract JSON from markdown code blocks
        patterns = [
            r"```json\n(.*?)\n```",  # JSON code block
            r"```\n(.*?)\n```",  # Generic code block
            r"{[\s\S]*}",  # Bare JSON object
            r"\[[\s\S]*\]",  # Bare JSON array
        ]

        for pattern in patterns:
            match = re.search(pattern, response, re.DOTALL)
            if match:
                try:
                    return json.loads(
                        match.group(1) if "```" in pattern else match.group(0)
                    )
                except json.JSONDecodeError:
                    continue

        # If no valid JSON found, return original response
        return response

async def save_image_file(image_bytes: bytes, folder_path: str, file_name: str):
    os.makedirs(folder_path, exist_ok=True)
    file_path = os.path.join(folder_path, file_name)
    with open(file_path, "wb") as f:
        f.write(image_bytes)
    return file_path

BASE_MODEL_EXTEND_TYPE = TypeVar("BASE_MODEL_EXTEND_TYPE", bound=BaseModel)
async def model_invoke_structured_output(service: ChatCompletionClientBase, cls: Type[BASE_MODEL_EXTEND_TYPE], chat_history: ChatHistory, retry_max: int, model_config: dict[str, Any] = {}) -> BASE_MODEL_EXTEND_TYPE:
    for _ in range(retry_max):
        try:
            response = await service.get_chat_message_content(chat_history, service.instantiate_prompt_execution_settings(**model_config))
            if response is None:
                raise Exception("No response from model")
            
            json_response = parse_json_response(response.content)
            return cls.model_validate(json_response)
        except Exception as e:
            logger.error(f"Error getting structured output: {e}")
            continue
    raise Exception("Failed to get structured output")


def get_today_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def get_buffer_string(
    messages: Sequence[ChatMessageContent], human_prefix: str = "Human", ai_prefix: str = "AI"
) -> str:
    r"""Convert a sequence of Messages to strings and concatenate them into one string.

    Args:
        messages: Messages to be converted to strings.
        human_prefix: The prefix to prepend to contents of HumanMessages.
            Default is "Human".
        ai_prefix: THe prefix to prepend to contents of AIMessages. Default is "AI".

    Returns:
        A single string concatenation of all input messages.

    Raises:
        ValueError: If an unsupported message type is encountered.

    Example:
        .. code-block:: python

            from langchain_core import AIMessage, HumanMessage

            messages = [
                HumanMessage(content="Hi, how are you?"),
                AIMessage(content="Good, how are you?"),
            ]
            get_buffer_string(messages)
            # -> "Human: Hi, how are you?\nAI: Good, how are you?"
    """
    string_messages = []
    for m in messages:
        if m.role == AuthorRole.USER:
            role = human_prefix
        elif m.role == AuthorRole.ASSISTANT:
            role = ai_prefix
        elif m.role == AuthorRole.SYSTEM:
            role = "System"            
        # elif isinstance(m, SystemMessage):
        #     role = "System"
        # elif isinstance(m, FunctionMessage):
        #     role = "Function"
        # elif isinstance(m, ToolMessage):
        #     role = "Tool"
        # elif isinstance(m, ChatMessage):
        #     role = m.role
        else:
            msg = f"Got unsupported message type: {m}"
            raise ValueError(msg)  # noqa: TRY004
        message = f"{role}: {m.content}"
        # if isinstance(m, AIMessage) and "function_call" in m.additional_kwargs:
        #     message += f"{m.additional_kwargs['function_call']}"
        string_messages.append(message)

    return "\n".join(string_messages)
