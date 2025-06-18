import logging
import os
from typing import (
    override,
    Callable,
    Awaitable,
    AsyncIterable,
    Any,
)
from openai import AsyncOpenAI
from semantic_kernel.kernel import Kernel, KernelArguments
from semantic_kernel.kernel_pydantic import KernelBaseSettings
from semantic_kernel.functions import KernelPlugin
from semantic_kernel.contents import (
    ChatMessageContent,
    StreamingChatMessageContent,
)
from semantic_kernel.agents import (
    Agent,
    AgentThread,
    AgentResponseItem,
    ChatCompletionAgent,
    register_agent_type,
    DeclarativeSpecMixin,
)
from semantic_kernel.utils.telemetry.agent_diagnostics.decorators import (
    trace_agent_get_response,
    trace_agent_invocation,
)
from pydantic import Field
from semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion import (
    OpenAIChatCompletion,
)

logger: logging.Logger = logging.getLogger(__name__)


class MetaSearchAgentConfig(KernelBaseSettings):
    search_web: bool = Field(default=True)
    rerank: bool = Field(default=True)
    summarizer: bool = Field(default=True)
    rerank_threshold: float = Field(default=0.5)
    query_generator_prompt: str = Field(default="")
    response_prompt: str = Field(default="")
    active_engines: list[str] = Field(default_factory=list)


@register_agent_type("meta_search_agent")
class MetaSearchAgent(DeclarativeSpecMixin, Agent):
# class MetaSearchAgent(ChatCompletionAgent):
    search_config: MetaSearchAgentConfig | None = None
    inner_chat_completion_agent: ChatCompletionAgent | None = None

    def __init__(
        self,
        *,
        config: MetaSearchAgentConfig,
        id: str | None = None,
    ):
        instructions = config.response_prompt
        super().__init__(
            id=id,
            instructions=instructions,
        )
        self.search_config = config
        self.inner_chat_completion_agent = ChatCompletionAgent(
            id=id,
            service=OpenAIChatCompletion(
                ai_model_id=os.getenv("OPENAI_MODEL_NAME"),
                async_client=AsyncOpenAI(
                    api_key=os.getenv("OPENAI_API_KEY"),
                    base_url=os.getenv("OPENAI_BASE_URL"),
                ),
            ),
            instructions=instructions,
        )

    @trace_agent_get_response
    @override
    async def get_response(
        self,
        messages: (
            str | ChatMessageContent | list[str | ChatMessageContent] | None
        ) = None,
        *,
        thread: AgentThread | None = None,
        arguments: KernelArguments | None = None,
        kernel: "Kernel | None" = None,
        **kwargs: Any,
    ) -> AgentResponseItem[ChatMessageContent]:
        pass

    @trace_agent_invocation
    @override
    async def invoke(
        self,
        messages: (
            str | ChatMessageContent | list[str | ChatMessageContent] | None
        ) = None,
        *,
        thread: AgentThread | None = None,
        on_intermediate_message: (
            Callable[[ChatMessageContent], Awaitable[None]] | None
        ) = None,
        arguments: KernelArguments | None = None,
        kernel: "Kernel | None" = None,
        **kwargs: Any,
    ) -> AsyncIterable[AgentResponseItem[ChatMessageContent]]:
        pass

    @trace_agent_invocation
    @override
    async def invoke_stream(
        self,
        messages: (
            str | ChatMessageContent | list[str | ChatMessageContent] | None
        ) = None,
        *,
        thread: AgentThread | None = None,
        on_intermediate_message: (
            Callable[[ChatMessageContent], Awaitable[None]] | None
        ) = None,
        arguments: KernelArguments | None = None,
        kernel: "Kernel | None" = None,
        **kwargs: Any,
    ) -> AsyncIterable[AgentResponseItem[StreamingChatMessageContent]]:
        logger.info(f"invoke_stream for {self.inner_chat_completion_agent}.")
        async for item in self.inner_chat_completion_agent.invoke_stream(
            messages=messages,
            thread=thread,
            on_intermediate_message=on_intermediate_message,
            arguments=arguments,
            kernel=kernel,
            **kwargs
        ):
            yield item

    @override
    @classmethod
    async def _from_dict(
        cls,
        data: dict,
        *,
        kernel: "Kernel | None" = None,
        plugins: (
            list[KernelPlugin | object] | dict[str, KernelPlugin | object] | None
        ) = None,
        **kwargs,
    ) -> "MetaSearchAgent":
        # Returns the normalized spec fields and a kernel configured with plugins, if present.
        fields, kernel = cls._normalize_spec_fields(
            data, kernel=kernel, plugins=plugins, **kwargs
        )

        if "service" in kwargs:
            fields["service"] = kwargs["service"]

        if "function_choice_behavior" in kwargs:
            fields["function_choice_behavior"] = kwargs["function_choice_behavior"]

        return cls(**fields, kernel=kernel)
