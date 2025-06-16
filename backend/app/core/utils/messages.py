from typing import AsyncIterable
import uuid

from ..ui_messages import UIMessage, TextUIPart, UIMessagePart
from a2a.types import Message, Role, Part, TextPart, FilePart, DataPart
    
def a2a_part_to_ui_part(part: Part) -> UIMessagePart:
    if isinstance(part.root, TextPart):
        return TextUIPart(text=part.root.text)
    elif isinstance(part.root, FilePart):
        return FileUIPart(url=part.root.url)
    elif isinstance(part.root, DataPart):
        return DataUIPart(data=part.root.data)
    else:
        raise ValueError(f"Unsupported part type: {type(part.root)}")
    
def a2a_message_to_ui_message(message: Message) -> UIMessage:
    return UIMessage(
        id=message.messageId,
        role="user" if message.role == Role.user else "assistant",
        parts=[
            a2a_part_to_ui_part(part)
            for part in message.parts
        ],
        metadata=message.metadata,
    )
