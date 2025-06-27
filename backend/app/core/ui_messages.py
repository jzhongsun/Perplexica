"""UI message types and interfaces for communication between frontend and API routes."""
from typing import Any, Dict, List, Optional, Union, Literal
from pydantic import BaseModel, Field
import uuid
# Type aliases
UIDataTypes = Dict[str, Any]
UITools = Dict[str, Dict[str, Any]]

class TextUIPart(BaseModel):
    """A text part of a message."""
    type: Literal['text'] = 'text'
    text: str
    state: Optional[Literal['streaming', 'done']] = None

class ReasoningUIPart(BaseModel):
    """A reasoning part of a message."""
    type: Literal['reasoning'] = 'reasoning'
    text: str
    state: Optional[Literal['streaming', 'done']] = None
    providerMetadata: Optional[Dict[str, Any]] = None

class SourceUrlUIPart(BaseModel):
    """A source URL part of a message."""
    type: Literal['source-url'] = 'source-url'
    sourceId: str
    url: str
    title: Optional[str] = None
    providerMetadata: Optional[Dict[str, Any]] = None

class SourceDocumentUIPart(BaseModel):
    """A document source part of a message."""
    type: Literal['source-document'] = 'source-document'
    sourceId: str
    mediaType: str
    title: str
    filename: Optional[str] = None
    providerMetadata: Optional[Dict[str, Any]] = None

class FileUIPart(BaseModel):
    """A file part of a message."""
    type: Literal['file'] = 'file'
    mediaType: str
    filename: Optional[str] = None
    url: str

class StepStartUIPart(BaseModel):
    """A step boundary part of a message."""
    type: Literal['step-start'] = 'step-start'

class DataUIPart(BaseModel):
    """A data part of a message."""
    type: str  # Will be 'data-{NAME}'
    id: Optional[str] = None
    data: Any

class ToolUIPartBase(BaseModel):
    """Base class for tool UI parts."""
    type: str  # Will be 'tool-{NAME}'
    toolCallId: str
    providerExecuted: Optional[bool] = None

class ToolUIPartInputStreaming(ToolUIPartBase):
    """Tool UI part for input streaming state."""
    state: Literal['input-streaming'] = 'input-streaming'
    input: Dict[str, Any]  # DeepPartial in TypeScript

class ToolUIPartInputAvailable(ToolUIPartBase):
    """Tool UI part for input available state."""
    state: Literal['input-available'] = 'input-available'
    input: Dict[str, Any]

class ToolUIPartOutputAvailable(ToolUIPartBase):
    """Tool UI part for output available state."""
    state: Literal['output-available'] = 'output-available'
    input: Dict[str, Any]
    output: Any

class ToolUIPartOutputError(ToolUIPartBase):
    """Tool UI part for output error state."""
    state: Literal['output-error'] = 'output-error'
    input: Dict[str, Any]
    errorText: str

ToolUIPart = Union[
    ToolUIPartInputStreaming,
    ToolUIPartInputAvailable,
    ToolUIPartOutputAvailable,
    ToolUIPartOutputError
]

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
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="A unique identifier for the message")
    role: Literal['system', 'user', 'assistant'] = Field(..., description="Role of the message sender (system/user/assistant)")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Metadata for the message")
    parts: List[UIMessagePart] = Field(..., description="Parts of the message")
    
    def content(self) -> str:
        """Get the content of the message."""
        return ''.join([part.text for part in self.parts if isinstance(part, TextUIPart)])

def is_tool_ui_part(part: UIMessagePart) -> bool:
    """Check if a message part is a tool part."""
    return hasattr(part, 'type') and part.type.startswith('tool-')

def get_tool_name(part: ToolUIPart) -> str:
    """Get the tool name from a tool part."""
    return part.type.split('-')[1]
