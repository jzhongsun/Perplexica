from semantic_kernel.agents import Agent, ChatCompletionAgent, DeclarativeSpecMixin, register_agent_type
from semantic_kernel.agents import AgentThread
from semantic_kernel.agents import AgentResponseItem
from semantic_kernel.contents import ChatMessageContent, StreamingChatMessageContent

from typing import AsyncIterable, Awaitable, Callable

@register_agent_type("search_agent")
class SearchAgent(Agent, DeclarativeSpecMixin):
    """Search agent class."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "search_agent"
        self.description = "Agent for performing web searches"

    def invoke_stream(
        self,
        messages: str | ChatMessageContent | list[str | ChatMessageContent] | None = None,
        *,
        thread: AgentThread | None = None,
        on_intermediate_message: Callable[[ChatMessageContent], Awaitable[None]] | None = None,
        **kwargs,
    ) -> AsyncIterable[AgentResponseItem[StreamingChatMessageContent]]:
        pass

    def invoke(
        self,
        messages: str | ChatMessageContent | list[str | ChatMessageContent] | None = None,
        *,
        thread: AgentThread | None = None,
        on_intermediate_message: Callable[[ChatMessageContent], Awaitable[None]] | None = None,
        **kwargs,
    ) -> AsyncIterable[AgentResponseItem[ChatMessageContent]]:
        pass