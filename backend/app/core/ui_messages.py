"""UI message types and interfaces for communication between frontend and API routes."""
from typing import Any, Dict, List, Optional, TypeVar, Union, Literal
from typing_extensions import TypedDict
from pydantic import BaseModel, Field

# Type aliases
UIDataTypes = Dict[str, Any]
UITools = Dict[str, Dict[str, Any]]

class TextUIPart(BaseModel):
    """A text part of a message."""
    type: Literal['text'] = 'text'
    text: str

class ReasoningUIPart(BaseModel):
    """A reasoning part of a message."""
    type: Literal['reasoning'] = 'reasoning'
    text: str
    providerMetadata: Optional[Dict[str, Any]]

class SourceUrlUIPart(BaseModel):
    """A source URL part of a message."""
    type: Literal['source-url'] = 'source-url'
    sourceId: str
    url: str
    title: Optional[str]
    providerMetadata: Optional[Dict[str, Any]]

class SourceDocumentUIPart(BaseModel):
    """A document source part of a message."""
    type: Literal['source-document'] = 'source-document'
    sourceId: str
    mediaType: str
    title: str
    filename: Optional[str]
    providerMetadata: Optional[Dict[str, Any]]

class FileUIPart(BaseModel):
    """A file part of a message."""
    type: Literal['file'] = 'file'
    mediaType: str
    filename: Optional[str]
    url: str

class StepStartUIPart(BaseModel):
    """A step boundary part of a message."""
    type: Literal['step-start'] = 'step-start'

class DataUIPart(BaseModel):
    """A data part of a message."""
    type: str  # Will be 'data-{NAME}'
    id: Optional[str]
    data: Any

class ToolUIPartBase(BaseModel):
    """Base class for tool UI parts."""
    type: str  # Will be 'tool-{NAME}'
    toolCallId: str

class ToolUIPartPartialCall(ToolUIPartBase):
    """Tool UI part for partial calls."""
    state: Literal['partial-call'] = 'partial-call'
    args: Dict[str, Any]

class ToolUIPartCall(ToolUIPartBase):
    """Tool UI part for complete calls."""
    state: Literal['call'] = 'call'
    args: Dict[str, Any]

class ToolUIPartResult(ToolUIPartBase):
    """Tool UI part for results."""
    state: Literal['result'] = 'result'
    args: Dict[str, Any]
    result: Any

ToolUIPart = Union[ToolUIPartPartialCall, ToolUIPartCall, ToolUIPartResult]

UIMessagePart = Union[
    TextUIPart,
    ReasoningUIPart,
    ToolUIPart,
    SourceUrlUIPart,
    SourceDocumentUIPart,
    FileUIPart,
    DataUIPart,
    StepStartUIPart
]

class UIMessage(BaseModel):
    """UI Message interface for client-API communication."""
    id: Optional[str] = Field(default=None, description="ID of the message")
    role: Literal['system', 'user', 'assistant'] = Field(..., description="Role of the message sender (system/user/assistant)")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Metadata for the message")
    parts: List[UIMessagePart] = Field(..., description="Parts of the message")

def is_tool_ui_part(part: UIMessagePart) -> bool:
    """Check if a message part is a tool part."""
    return part['type'].startswith('tool-')

def get_tool_name(part: ToolUIPart) -> str:
    """Get the tool name from a tool part."""
    return part['type'].split('-')[1]
