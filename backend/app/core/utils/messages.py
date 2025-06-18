from typing import List
import uuid
from a2a.types import (
    Message,
    Role,
    Part,
    TextPart,
    FilePart,
    DataPart,
    FileWithUri,
    FileWithBytes,
)

from ..ui_message_stream import (
    UIMessageStreamPart,
    TextUIMessageStreamPart,
    FileUIMessageStreamPart,
    DataUIMessageStreamPart,
)
from ..ui_messages import UIMessage, UIMessagePart, TextUIPart, FileUIPart, DataUIPart


def ui_message_to_a2a_message(
    message: UIMessage, context_id: str = None, task_id: str = None, **kwargs
) -> Message:
    message_id = message.id
    if message_id is None or len(message_id) == 0:
        message_id = str(uuid.uuid4())
    a2a_parts = []
    for part in message.parts:
        if isinstance(part, TextUIPart):
            a2a_parts.append(TextPart(text=part.text))
        elif isinstance(part, FileUIPart):
            a2a_parts.append(
                FilePart(file=FileWithUri(uri=part.url, mimeType=part.mediaType))
            )
        elif isinstance(part, DataUIPart):
            a2a_parts.append(DataPart(data=part.data))
        else:
            raise ValueError(f"Unsupported part type: {type(part)}")

    return Message(
        messageId=message_id,
        role=Role.user if message.role == "user" else Role.agent,
        parts=a2a_parts,
        contextId=context_id if context_id else None,
        taskId=task_id if task_id else None,
        **kwargs,
    )


def a2a_part_to_ui_part(part: Part) -> UIMessageStreamPart:
    if isinstance(part.root, TextPart):
        return TextUIMessageStreamPart(text=part.root.text)
    elif isinstance(part.root, FilePart):
        if isinstance(part.root.file, FileWithUri):
            return FileUIMessageStreamPart(
                url=part.root.file.uri, mediaType=part.root.file.mimeType
            )
        elif isinstance(part.root.file, FileWithBytes):
            return FileUIMessageStreamPart(
                url=part.root.file.bytes, mediaType=part.root.file.mimeType
            )
        else:
            raise ValueError(f"Unsupported file type: {type(part.root.file)}")
    elif isinstance(part.root, DataPart):
        return DataUIMessageStreamPart(data=part.root.data)
    else:
        raise ValueError(f"Unsupported part type: {type(part.root)}")


def a2a_message_to_ui_message_stream_parts(
    message: Message,
) -> List[UIMessageStreamPart]:
    return [a2a_part_to_ui_part(part) for part in message.parts]
