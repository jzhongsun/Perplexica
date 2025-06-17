from typing import List
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
from ..ui_messages import UIMessage


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


def a2a_message_to_ui_message_stream_parts(message: Message) -> List[UIMessageStreamPart]:
    return [
        a2a_part_to_ui_part(part) for part in message.parts
    ]
