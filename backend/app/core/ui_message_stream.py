from typing import Any, Dict, Generic, Literal, Optional, TypeVar, Union
from pydantic import BaseModel, field_validator

from .ui_messages import UIDataTypes, UIMessage

ProviderMetadata = Dict[str, Any]


class TextStartUIMessageStreamPart(BaseModel):
    type: Literal["text-start"] = "text-start"
    id: str


class TextDeltaUIMessageStreamPart(BaseModel):
    type: Literal["text-delta"] = "text-delta"
    id: str
    delta: str


class TextEndUIMessageStreamPart(BaseModel):
    type: Literal["text-end"] = "text-end"
    id: str


class ErrorUIMessageStreamPart(BaseModel):
    type: Literal["error"] = "error"
    errorText: str


class ToolInputStartUIMessageStreamPart(BaseModel):
    type: Literal["tool-input-start"] = "tool-input-start"
    toolCallId: str
    toolName: str
    providerExecuted: Optional[bool] = None


class ToolInputDeltaUIMessageStreamPart(BaseModel):
    type: Literal["tool-input-delta"] = "tool-input-delta"
    toolCallId: str
    inputTextDelta: str


class ToolInputAvailableUIMessageStreamPart(BaseModel):
    type: Literal["tool-input-available"] = "tool-input-available"
    toolCallId: str
    toolName: str
    input: Any
    providerExecuted: Optional[bool] = None


class ToolOutputAvailableUIMessageStreamPart(BaseModel):
    type: Literal["tool-output-available"] = "tool-output-available"
    toolCallId: str
    output: Any
    providerExecuted: Optional[bool] = None


class ToolOutputErrorUIMessageStreamPart(BaseModel):
    type: Literal["tool-output-error"] = "tool-output-error"
    toolCallId: str
    errorText: str
    providerExecuted: Optional[bool] = None


class ReasoningUIMessageStreamPart(BaseModel):
    type: Literal["reasoning"] = "reasoning"
    text: str
    providerMetadata: Optional[Dict[str, Any]] = None


class ReasoningStartUIMessageStreamPart(BaseModel):
    type: Literal["reasoning-start"] = "reasoning-start"
    id: str
    providerMetadata: Optional[Dict[str, Any]] = None


class ReasoningDeltaUIMessageStreamPart(BaseModel):
    type: Literal["reasoning-delta"] = "reasoning-delta"
    id: str
    delta: str
    providerMetadata: Optional[Dict[str, Any]] = None


class ReasoningEndUIMessageStreamPart(BaseModel):
    type: Literal["reasoning-end"] = "reasoning-end"
    id: str
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

    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        if not v.startswith("data-"):
            raise ValueError("Data stream part type must start with 'data-'")
        return v


class StartStepUIMessageStreamPart(BaseModel):
    type: Literal["start-step"] = "start-step"


class FinishStepUIMessageStreamPart(BaseModel):
    type: Literal["finish-step"] = "finish-step"


class StartUIMessageStreamPart(BaseModel):
    type: Literal["start"] = "start"
    messageId: Optional[str] = None
    messageMetadata: Optional[Any] = None


class FinishUIMessageStreamPart(BaseModel):
    type: Literal["finish"] = "finish"
    messageMetadata: Optional[Any] = None


class MessageMetadataUIMessageStreamPart(BaseModel):
    type: Literal["message-metadata"] = "message-metadata"
    messageMetadata: Any


# Union of all possible stream parts
UIMessageStreamPart = Union[
    TextStartUIMessageStreamPart,
    TextDeltaUIMessageStreamPart,
    TextEndUIMessageStreamPart,
    ErrorUIMessageStreamPart,
    ToolInputStartUIMessageStreamPart,
    ToolInputDeltaUIMessageStreamPart,
    ToolInputAvailableUIMessageStreamPart,
    ToolOutputAvailableUIMessageStreamPart,
    ToolOutputErrorUIMessageStreamPart,
    ReasoningUIMessageStreamPart,
    ReasoningStartUIMessageStreamPart,
    ReasoningDeltaUIMessageStreamPart,
    ReasoningEndUIMessageStreamPart,
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


class GenericDataUIMessageStreamPart(BaseModel, Generic[DATA_TYPES]):
    """Generic version of DataUIMessageStreamPart with proper typing."""
    type: str  # Will be validated to start with 'data-'
    id: Optional[str] = None
    data: DATA_TYPES

    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        if not v.startswith("data-"):
            raise ValueError("Data stream part type must start with 'data-'")
        return v


# Type alias for InferUIMessageStreamPart
T = TypeVar("T", bound=UIMessage)
InferUIMessageStreamPart = UIMessageStreamPart  # This is a simplification, as Python's type system can't fully express the TypeScript equivalent
