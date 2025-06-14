from semantic_kernel.agents import ChatCompletionAgent, Agent
from semantic_kernel.kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion


def create_agent(
    name: str, description: str, instructions: str, tools: list[str], kernel: Kernel
) -> Agent:
    """Create an agent."""
    return ChatCompletionAgent(
        name=name,
        description=description,
        instructions=instructions,
        tools=tools,
        kernel=kernel,
        service=OpenAIChatCompletion()
    )
