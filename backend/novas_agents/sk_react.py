from semantic_kernel.agents import Agent
from pydantic import BaseModel
from typing import Optional

class ReActStep(BaseModel):
    observation: Optional[str] = None
    thought: Optional[str] = None
    action: Optional[str] = None
    action_variables: Optional[dict[str, str]] = None
    final_answer: Optional[str] = None
    original_response: Optional[str] = None
    
class ReActExecutor:
    pass

class ReActAgentConfig(BaseModel):
    steps: list[ReActStep]

class ReActAgent(Agent):
    pass

class CodeActAgent(ReActAgent):
    pass

class ToolCallingAgent(ReActAgent):
    pass