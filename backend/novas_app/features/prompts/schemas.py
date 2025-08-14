from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class PromptTemplate(BaseModel):
    """Prompt template schema."""
    name: str = Field(..., description="Template name")
    template: str = Field(..., description="The prompt template text")
    description: Optional[str] = Field(None, description="Template description")
    variables: List[str] = Field(default_factory=list, description="List of variables used in the template")
    metadata: Dict = Field(default_factory=dict, description="Additional metadata")

class PromptRequest(BaseModel):
    """Prompt generation request."""
    template_name: str = Field(..., description="Name of the template to use")
    variables: Dict[str, str] = Field(..., description="Variables to fill in the template")

class PromptResponse(BaseModel):
    """Prompt generation response."""
    prompt: str = Field(..., description="Generated prompt")
    template_name: str = Field(..., description="Name of the template used")
    metadata: Dict = Field(default_factory=dict, description="Additional metadata") 