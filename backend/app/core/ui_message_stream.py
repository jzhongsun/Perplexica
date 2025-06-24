from typing import Any, Dict, Generic, Literal, Optional, TypeVar, Union
from pydantic import BaseModel

from .ui_messages import UIDataTypes, UIMessage

ProviderMetadata = Dict[str, Any]


class TextUIMessageStreamPart(BaseModel):
    type: Literal["text"] = "text"
    text: str


class ErrorUIMessageStreamPart(BaseModel):
    type: Literal["error"] = "error"
    errorText: str


class ToolInputStartUIMessageStreamPart(BaseModel):
    type: Literal["tool-input-start"] = "tool-input-start"
    toolCallId: str
    toolName: str


class ToolInputDeltaUIMessageStreamPart(BaseModel):
    type: Literal["tool-input-delta"] = "tool-input-delta"
    toolCallId: str
    inputTextDelta: str


class ToolInputAvailableUIMessageStreamPart(BaseModel):
    type: Literal["tool-input-available"] = "tool-input-available"
    toolCallId: str
    toolName: str
    input: Any


class ToolOutputAvailableUIMessageStreamPart(BaseModel):
    type: Literal["tool-output-available"] = "tool-output-available"
    toolCallId: str
    output: Any
    providerMetadata: Optional[ProviderMetadata] = None


class ReasoningUIMessageStreamPart(BaseModel):
    type: Literal["reasoning"] = "reasoning"
    text: str
    providerMetadata: Optional[Dict[str, Any]] = None


class ReasoningPartFinishUIMessageStreamPart(BaseModel):
    type: Literal["reasoning-part-finish"] = "reasoning-part-finish"


class SourceUrlUIMessageStreamPart(BaseModel):
    type: Literal["source-url"] = "source-url"
    sourceId: str
    url: str
    title: Optional[str] = None
    providerMetadata: Optional[ProviderMetadata] = None


class SourceDocumentUIMessageStreamPart(BaseModel):
    type: Literal["source-document"] = "source-document"
    sourceId: str
    mediaType: str
    title: str
    filename: Optional[str] = None
    providerMetadata: Optional[ProviderMetadata] = None


class FileUIMessageStreamPart(BaseModel):
    type: Literal["file"] = "file"
    url: str
    mediaType: str


class DataUIMessageStreamPart(BaseModel):
    type: str  # Will be validated to start with 'data-'
    id: Optional[str] = None
    data: Any

    def __init__(self, **data):
        super().__init__(**data)
        if not self.type.startswith("data-"):
            raise ValueError("Data stream part type must start with 'data-'")


class StartStepUIMessageStreamPart(BaseModel):
    type: Literal["start-step"] = "start-step"


class FinishStepUIMessageStreamPart(BaseModel):
    type: Literal["finish-step"] = "finish-step"


class StartUIMessageStreamPart(BaseModel):
    type: Literal["start"] = "start"
    messageId: Optional[str] = None
    messageMetadata: Optional[ProviderMetadata] = None


class FinishUIMessageStreamPart(BaseModel):
    type: Literal["finish"] = "finish"
    messageMetadata: Optional[ProviderMetadata] = None


class MessageMetadataUIMessageStreamPart(BaseModel):
    type: Literal["message-metadata"] = "message-metadata"
    messageMetadata: ProviderMetadata


# Union of all possible stream parts
UIMessageStreamPart = Union[
    TextUIMessageStreamPart,
    ErrorUIMessageStreamPart,
    ToolInputStartUIMessageStreamPart,
    ToolInputDeltaUIMessageStreamPart,
    ToolInputAvailableUIMessageStreamPart,
    ToolOutputAvailableUIMessageStreamPart,
    ReasoningUIMessageStreamPart,
    ReasoningPartFinishUIMessageStreamPart,
    SourceUrlUIMessageStreamPart,
    SourceDocumentUIMessageStreamPart,
    FileUIMessageStreamPart,
    DataUIMessageStreamPart,
    StartStepUIMessageStreamPart,
    FinishStepUIMessageStreamPart,
    StartUIMessageStreamPart,
    FinishUIMessageStreamPart,
    MessageMetadataUIMessageStreamPart,
]


def is_data_ui_message_stream_part(part: UIMessageStreamPart) -> bool:
    """Check if a stream part is a data stream part."""
    if isinstance(part, dict):
        return part.get("type", "").startswith("data-")
    return getattr(part, "type", "").startswith("data-")


# Generic type for DataUIMessageStreamPart
DATA_TYPES = TypeVar("DATA_TYPES", bound=UIDataTypes)


class DataUIMessageStreamPart(BaseModel, Generic[DATA_TYPES]):
    type: str  # Will be validated to start with 'data-'
    id: Optional[str] = None
    data: DATA_TYPES

    def __init__(self, **data):
        super().__init__(**data)
        if not self.type.startswith("data-"):
            raise ValueError("Data stream part type must start with 'data-'")


# Type alias for InferUIMessageStreamPart
T = TypeVar("T", bound=UIMessage)
InferUIMessageStreamPart = UIMessageStreamPart  # This is a simplification, as Python's type system can't fully express the TypeScript equivalent
