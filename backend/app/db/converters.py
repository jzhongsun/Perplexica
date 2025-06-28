from typing import List
from app.db.models import DbMessage, DbMessagePart
import app.core.ui_messages as ui_messages
import logging
import a2a.types as a2a_types

logger = logging.getLogger(__name__)

def convert_a2a_message_part_to_db_message_part(part: a2a_types.Part) -> DbMessagePart:
    root_part = part.root
    if isinstance(root_part, a2a_types.TextPart):
        return DbMessagePart(id=root_part.id, part_type="text", part_data={"text": root_part.text})
    elif isinstance(root_part, a2a_types.FilePart):
        return DbMessagePart(id=root_part.id, part_type="file", part_data={"file_id": root_part.file_id})
    elif isinstance(root_part, a2a_types.DataPart):
        return DbMessagePart(id=root_part.id, part_type="data", part_data={"data": root_part.data})
    else:
        logger.warning(f"Unknown part type: {root_part.type}")
        return None

def convert_a2a_message_to_db_message(message: a2a_types.Message) -> DbMessage:
    return DbMessage(id=message.id, 
                     role=message.role, 
                     content=message.content,
                     metadata=message.metadata,
                     extensions=message.extensions)

def convert_db_message_to_ui_message(message: DbMessage, message_parts: List[DbMessagePart]) -> ui_messages.UIMessage:
    parts = []
    for message_part in message_parts:
        part = convert_db_message_part_to_ui_message_part(message_part)
        if part is not None:
            parts.append(part)
    metadata = message._metadata if message._metadata is not None else {}
    metadata["createdAt"] = message.created_at.isoformat()
    return ui_messages.UIMessage(id=message.id, role=message.role, parts=parts, metadata=metadata)

def convert_db_message_part_to_ui_message_part(message_part: DbMessagePart) -> ui_messages.UIMessagePart:
    if message_part.part_type == "text":
        return ui_messages.TextUIPart(text=message_part.part_data["text"], state="done")
    elif message_part.part_type == "file":
        return ui_messages.FileUIPart(file_id=message_part.part_data["file_id"], state="done")
    elif message_part.part_type == "data":
        return ui_messages.DataUIPart(data=message_part.part_data["data"], state="done")
    elif message_part.part_type.startswith("tool-"):
        part_data = message_part.part_data if message_part.part_data is not None else {}
        tool_state = part_data.get("state")
        if tool_state == "input-available":
            return ui_messages.ToolUIPartInputAvailable(type=message_part.part_type, 
                                                        toolCallId=message_part.id, 
                                                        input=part_data["input"] if "input" in part_data else {})
        elif tool_state == "output-available":
            return ui_messages.ToolUIPartOutputAvailable(type=message_part.part_type, 
                                                         toolCallId=message_part.id, 
                                                         input=part_data["input"] if "input" in part_data else {},
                                                         output=part_data["output"] if "output" in part_data else {})
        elif tool_state == "output-error":
            return ui_messages.ToolUIPartOutputError(type=message_part.part_type, 
                                                     toolCallId=message_part.id, 
                                                     input=part_data["input"] if "input" in part_data else {},
                                                     errorText=part_data["errorText"] if "errorText" in part_data else "")
        else:
            return None
    elif message_part.part_type.startswith("reasoning"):
        return ui_messages.ReasoningUIPart(reasoning=message_part.part_data["reasoning"], state="done")
    else:
        logger.warning(f"Unknown part type: {message_part.part_type}")
        return ui_messages.TextUIPart(text=message_part.part_data["text"] if "text" in message_part.part_data else "")
