"""Format chat history as string."""
from typing import List

def format_chat_history_as_string(history: List[any]) -> str:
    """Format chat history as string.
    
    Args:
        history: Chat history
        
    Returns:
        Formatted history string
    """
    formatted = []
    for msg in history:
        role = "Human" if msg.type == "human" else "Assistant"
        formatted.append(f"{role}: {msg.content}")
    return "\n".join(formatted) 