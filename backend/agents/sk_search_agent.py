import logging
import os
from typing import (
    override,
    Callable,
    Awaitable,
    AsyncIterable,
    Any,
    AsyncGenerator,
    Optional,
)
from openai import AsyncOpenAI
from semantic_kernel.kernel import Kernel, KernelArguments
from semantic_kernel.connectors.ai.chat_completion_client_base import (
    ChatCompletionClientBase,
)
from semantic_kernel.kernel_pydantic import KernelBaseSettings
from semantic_kernel.functions import KernelPlugin
from semantic_kernel.contents import (
    ChatMessageContent,
    StreamingChatMessageContent,
    AuthorRole,
    FunctionCallContent,
    FunctionResultContent,
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
from semantic_kernel.prompt_template import PromptTemplateConfig
from semantic_kernel.agents.chat_completion.chat_completion_agent import (
    ChatHistoryAgentThread,
)
from semantic_kernel.agents.chat_completion.chat_completion_agent import ChatHistory
from pydantic import BaseModel, ConfigDict, Field
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
# class MetaSearchAgent(DeclarativeSpecMixin, Agent):
class MetaSearchAgent(ChatCompletionAgent):
    search_config: MetaSearchAgentConfig | None = None

    def __init__(
        self,
        *,
        config: MetaSearchAgentConfig,
        id: str | None = None,
    ):
        instructions = config.response_prompt
        super().__init__(
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
        self.search_config = config

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
        logger.debug(f"[{type(self).__name__}] Invoking {type(self).__name__}.")

        thread = await self._ensure_thread_exists_with_messages(
            messages=messages,
            thread=thread,
            construct_thread=lambda: ChatHistoryAgentThread(),
            expected_type=ChatHistoryAgentThread,
        )
        assert thread.id is not None  # nosec

        chat_history = ChatHistory()
        async for message in thread.get_messages():
            chat_history.add_message(message)

        if arguments is None:
            arguments = KernelArguments(**kwargs)
        else:
            arguments.update(kwargs)

        kernel = kernel or self.kernel
        arguments = self._merge_arguments(arguments)

        chat_completion_service, settings = (
            await self._get_chat_completion_service_and_settings(
                kernel=kernel, arguments=arguments
            )
        )

        # If the user hasn't provided a function choice behavior, use the agent's default.
        if settings.function_choice_behavior is None:
            settings.function_choice_behavior = self.function_choice_behavior

        agent_chat_history = await self._prepare_agent_chat_history(
            history=chat_history,
            kernel=kernel,
            arguments=arguments,
        )

        message_count_before_completion = len(agent_chat_history)

        logger.debug(
            f"[{type(self).__name__}] Invoking {type(chat_completion_service).__name__}."
        )

        settings.function_choice_behavior = None
        responses: AsyncGenerator[list[StreamingChatMessageContent], Any] = (
            chat_completion_service.get_streaming_chat_message_contents(
                chat_history=agent_chat_history,
                settings=settings,
                kernel=kernel,
                arguments=arguments,
            )
        )

        logger.debug(
            f"[{type(self).__name__}] Invoked {type(chat_completion_service).__name__} "
            f"with message count: {message_count_before_completion}."
        )

        role = None
        response_builder: list[str] = []
        start_idx = len(agent_chat_history)

        async for response_list in responses:
            logger.info(f"[{type(self).__name__}] Response: {response_list}")
            for response in response_list:
                role = response.role
                response.name = self.name
                response_builder.append(response.content)

                if (
                    role == AuthorRole.ASSISTANT
                    and (response.items or response.metadata.get("usage"))
                    and not any(
                        isinstance(item, (FunctionCallContent, FunctionResultContent))
                        for item in response.items
                    )
                ):
                    yield AgentResponseItem(message=response, thread=thread)

            # Drain newly added tool messages since last index to maintain
            # correct order and avoid duplicates
            new_messages = await self._drain_mutated_messages(
                agent_chat_history,
                start_idx,
                thread,
            )
            # resets start_idx to the latest length of agent_chat_history.
            start_idx = len(agent_chat_history)

            if on_intermediate_message:
                for message in new_messages:
                    await on_intermediate_message(message)

        if role != AuthorRole.TOOL:
            # Tool messages will be automatically added to the chat history by the auto function invocation loop
            # if it's the response (i.e. terminated by a filter), thus we need to avoid notifying the thread about
            # them multiple times.
            await thread.on_new_message(
                ChatMessageContent(
                    role=role if role else AuthorRole.ASSISTANT,
                    content="".join(response_builder),
                    name=self.name,
                )
            )

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
