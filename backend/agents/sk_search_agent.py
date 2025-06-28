from urllib.parse import urljoin
import uuid
from functools import reduce
import json
import logging
import os
from typing import (
    AsyncGenerator,
    Dict,
    List,
    Optional,
    override,
    Callable,
    Awaitable,
    AsyncIterable,
    Any,
    Annotated,
    TypedDict,
)
from openai import AsyncOpenAI
from semantic_kernel.kernel import Kernel, KernelArguments
from semantic_kernel.kernel_pydantic import KernelBaseSettings
from semantic_kernel.functions import KernelPlugin, KernelFunction
from semantic_kernel.contents import (
    ChatMessageContent,
    StreamingChatMessageContent,
    FunctionCallContent,
    FunctionResultContent,
)
from semantic_kernel.agents import (
    Agent,
    AgentThread,
    AgentResponseItem,
    ChatCompletionAgent,
    ChatHistoryAgentThread,
    register_agent_type,
    DeclarativeSpecMixin,
)
from semantic_kernel.utils.telemetry.agent_diagnostics.decorators import (
    trace_agent_get_response,
    trace_agent_invocation,
)
from pydantic import BaseModel, Field
from semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion import (
    OpenAIChatCompletion,
)
from semantic_kernel.connectors.ai.function_choice_behavior import (
    FunctionChoiceBehavior,
)
from semantic_kernel.functions import kernel_function
from semantic_kernel.contents import ChatHistory
from semantic_kernel.contents import AuthorRole

logger: logging.Logger = logging.getLogger(__name__)

LOCAL_SEARCH_PLUGIN_NAME = "local_search"
LOCAL_SEARCH_FUNCTION_NAME = "local_search"

WEB_SEARCH_PLUGIN_NAME = "web_search"
WEB_SEARCH_AND_FETCH_FUNCTION_NAME = "search_and_fetch"
WEB_SEARCH_FUNCTION_NAME = "web_search"
WEB_PAGE_FETCH_FUNCTION_NAME = "web_page_fetch"


class MetaSearchAgentConfig(KernelBaseSettings):
    search_web: bool = Field(default=True)
    rerank: bool = Field(default=True)
    summarizer: bool = Field(default=True)
    rerank_threshold: float = Field(default=0.5)
    query_generator_prompt: str = Field(default="")
    response_prompt: str = Field(default="")
    active_engines: list[str] = Field(default_factory=list)


class WebSearchAndFetchResult(BaseModel):
    request_id: str
    request_type: str  # web_search, web_page_fetch
    query: str | None = Field(default=None)
    arguments: Optional[dict[str, Any]] = Field(default=None)
    result: Optional[Any] = Field(default=None)


@register_agent_type("meta_search_agent")
class MetaSearchAgent(DeclarativeSpecMixin, Agent):
    # class MetaSearchAgent(ChatCompletionAgent):
    instructions: str | None = None
    search_config: MetaSearchAgentConfig | None = None
    inner_chat_completion_agent: ChatCompletionAgent | None = None

    def __init__(
        self,
        *,
        config: MetaSearchAgentConfig,
        id: str | None = None,
    ):
        super().__init__(
            id=id,
            instructions=config.response_prompt,
        )
        self.instructions = config.response_prompt
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
            instructions=self.instructions,
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

    @kernel_function(
        name="local_search_and_retrieve",
        description="Search the local database for the query",
    )
    async def local_search_and_retrieve(
        self, query: Annotated[str, "The query to search for"]
    ):
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
        function_call_arguments: KernelArguments | None = None,
        kernel: "Kernel | None" = None,
        **kwargs: Any,
    ) -> AsyncIterable[AgentResponseItem[StreamingChatMessageContent]]:

        kernel = Kernel()
        kernel.add_service(
            OpenAIChatCompletion(
                ai_model_id=os.getenv("OPENAI_MODEL_NAME"),
                async_client=AsyncOpenAI(
                    api_key=os.getenv("OPENAI_API_KEY"),
                    base_url=os.getenv("OPENAI_BASE_URL"),
                ),
            )
        )
        # kernel.add_function(function=KernelFunction.from_method(
        #     method=self.local_search_and_retrieve,
        #     plugin_name="local_search_and_retrieve",
        # ))
        if self.search_config.search_web:
            kernel.add_function(
                plugin_name=WEB_SEARCH_PLUGIN_NAME,
                function_name=WEB_SEARCH_AND_FETCH_FUNCTION_NAME,
                function=KernelFunction.from_method(self.__web_search_and_fetch),
            )
            # kernel.add_plugin(plugin_name=WEB_SEARCH_PLUGIN_NAME, plugin=MetaSearchPlugin())

        inner_chat_completion_service = kernel.get_service(type=OpenAIChatCompletion)
        chat_history = ChatHistory()
        chat_history.add_system_message(self.instructions)
        for message in messages:
            chat_history.add_message(message)

        agent_thread = ChatHistoryAgentThread(chat_history=chat_history)

        settings = inner_chat_completion_service.instantiate_prompt_execution_settings(
            function_choice_behavior=FunctionChoiceBehavior.Auto(auto_invoke=False),
            temperature=0.0,
        )
        logger.info(
            f"invoke_stream for {kernel} \n chat_history = {chat_history.model_dump_json(indent=2)} \n settings = {settings.model_dump_json(indent=2, exclude_none=True)}."
        )
        all_messages: list["StreamingChatMessageContent"] = []
        function_call_returned = False
        async for (
            message_content_chunk
        ) in inner_chat_completion_service.get_streaming_chat_message_content(
            chat_history=chat_history, settings=settings, kernel=kernel
        ):
            logger.info(
                f"{type(message_content_chunk)}: {message_content_chunk.model_dump_json(indent=2, exclude_none=True)}"
            )
            if message_content_chunk is None:
                continue

            all_messages.append(message_content_chunk)
            if not function_call_returned and any(
                isinstance(item, FunctionCallContent)
                for item in message_content_chunk.items
            ):
                function_call_returned = True

            role = message_content_chunk.role
            if (
                role == AuthorRole.ASSISTANT
                and (
                    message_content_chunk.items
                    or message_content_chunk.metadata.get("usage")
                )
                and not any(
                    isinstance(item, (FunctionCallContent, FunctionResultContent))
                    for item in message_content_chunk.items
                )
            ):
                yield AgentResponseItem(
                    message=message_content_chunk, thread=agent_thread
                )

            # yield AgentResponseItem(message=message_content_chunk, thread=agent_thread)
        if not function_call_returned:
            return

        full_completion: StreamingChatMessageContent = reduce(
            lambda x, y: x + y, all_messages
        )
        logger.info(
            f"full_completion = \n{full_completion.model_dump_json(indent=2, exclude_none=True)}"
        )
        function_calls = [
            item
            for item in full_completion.items
            if isinstance(item, FunctionCallContent)
        ]
        logger.info(f"function_calls = \n{function_calls}")

        for function_call in function_calls:
            call_id = function_call.id
            message = StreamingChatMessageContent(
                role=AuthorRole.ASSISTANT,
                items=[FunctionCallContent(
                    id=call_id,
                    call_id=call_id,
                    name=function_call.name,
                    ai_model_id=function_call.ai_model_id,
                    function_name=function_call.function_name,
                    plugin_name=function_call.plugin_name,
                    arguments=function_call.arguments if isinstance(function_call.arguments, dict) else json.loads(function_call.arguments),
                    metadata={
                        "inner_part_type": "tool_call",
                        **function_call.metadata,
                    },
                )],
                choice_index=full_completion.choice_index if full_completion else 0,
                metadata=full_completion.metadata if full_completion else {},
            )
            chat_history.add_message(message)
            logger.info(f"function_call = \n{message}")
            yield AgentResponseItem(
                message=message,
                thread=agent_thread,
            )
            if (
                function_call.function_name == WEB_SEARCH_AND_FETCH_FUNCTION_NAME
                and function_call.plugin_name == WEB_SEARCH_PLUGIN_NAME
            ):
                logger.info(f"handling function_call = \n{function_call}")
                function_call_arguments = json.loads(function_call.arguments)
                function_call_results: List[Any] = []
                async for search_and_fetch_result in self.__web_search_and_fetch(
                    function_call_arguments["query"],
                    language=function_call_arguments["language"],
                ):
                    result: WebSearchAndFetchResult = search_and_fetch_result
                    logger.info(f"__web_search_and_fetch result = {result}")
                    if result.request_type == "web_page_fetch_begin":
                        yield AgentResponseItem(
                            message=StreamingChatMessageContent(
                                role=AuthorRole.ASSISTANT,
                                items=[
                                    FunctionCallContent(
                                        id=result.request_id,
                                        call_id=result.request_id,
                                        name=f"{WEB_SEARCH_PLUGIN_NAME}-{WEB_PAGE_FETCH_FUNCTION_NAME}",
                                        function_name=WEB_PAGE_FETCH_FUNCTION_NAME,
                                        plugin_name=WEB_SEARCH_PLUGIN_NAME,
                                        arguments=result.arguments,
                                    )
                                ],
                                choice_index=(
                                    full_completion.choice_index
                                    if full_completion
                                    else 0
                                ),
                                metadata={
                                    "internal_type": "artifact",
                                },
                            ),
                            thread=agent_thread,
                        )
                    elif result.request_type == "web_page_fetch_end":
                        yield AgentResponseItem(
                            message=StreamingChatMessageContent(
                                role=AuthorRole.TOOL,
                                items=[
                                    FunctionResultContent(
                                        id=result.request_id,
                                        call_id=result.request_id,
                                        name=f"{WEB_SEARCH_PLUGIN_NAME}-{WEB_PAGE_FETCH_FUNCTION_NAME}",
                                        function_name=WEB_PAGE_FETCH_FUNCTION_NAME,
                                        plugin_name=WEB_SEARCH_PLUGIN_NAME,
                                        result=result.result,
                                    )
                                ],
                                choice_index=(
                                    full_completion.choice_index
                                    if full_completion
                                    else 0
                                ),
                                metadata={
                                    "internal_type": "artifact",
                                },
                            ),
                            thread=agent_thread,
                        )
                        if result.result.get("success"):
                            function_call_results.append(result.result)

                    elif result.request_type == "web_search_begin":
                        yield AgentResponseItem(
                            message=StreamingChatMessageContent(
                                role=AuthorRole.ASSISTANT,
                                items=[
                                    FunctionCallContent(
                                        id=result.request_id,
                                        call_id=result.request_id,
                                        name=f"{WEB_SEARCH_PLUGIN_NAME}-{WEB_SEARCH_FUNCTION_NAME}",
                                        function_name=WEB_SEARCH_FUNCTION_NAME,
                                        plugin_name=WEB_SEARCH_PLUGIN_NAME,
                                        arguments=result.arguments,
                                    ),
                                ],
                                choice_index=(
                                    full_completion.choice_index
                                    if full_completion
                                    else 0
                                ),
                                metadata={
                                    "internal_type": "artifact",
                                },
                            ),
                            thread=agent_thread,
                        )
                    elif result.request_type == "web_search_end":
                        yield AgentResponseItem(
                            message=StreamingChatMessageContent(
                                role=AuthorRole.TOOL,
                                items=[
                                    FunctionResultContent(
                                        id=result.request_id,
                                        name=f"{WEB_SEARCH_PLUGIN_NAME}-{WEB_SEARCH_FUNCTION_NAME}",
                                        call_id=result.request_id,
                                        function_name=WEB_SEARCH_FUNCTION_NAME,
                                        plugin_name=WEB_SEARCH_PLUGIN_NAME,
                                        result=result.result,
                                    ),
                                ],
                                choice_index=(
                                    full_completion.choice_index
                                    if full_completion
                                    else 0
                                ),
                                metadata={
                                    "internal_type": "artifact",
                                },
                            ),
                            thread=agent_thread,
                        )
                    else:
                        raise ValueError(f"Unknown request_type: {result.request_type}")

                function_call_result_message = StreamingChatMessageContent(
                    role=AuthorRole.TOOL,
                    items=[
                        FunctionResultContent(
                            id=call_id,
                            name=function_call.name,
                            call_id=function_call.id,
                            function_name=WEB_SEARCH_AND_FETCH_FUNCTION_NAME,
                            plugin_name=WEB_SEARCH_PLUGIN_NAME,
                            result=function_call_results,
                        )
                    ],
                    choice_index=(
                        full_completion.choice_index if full_completion else 0
                    ),
                    metadata=(full_completion.metadata if full_completion else {}),
                )
                logger.info(
                    f"function_call_result_message = \n{function_call_result_message}"
                )

                yield AgentResponseItem(
                    message=function_call_result_message,
                    thread=agent_thread,
                )
        chat_history.add_message(function_call_result_message)
        logger.info(
            f"chat_history = \n{chat_history.model_dump_json(indent=2, exclude_none=True)}"
        )
        async for (
            message_content_chunk
        ) in inner_chat_completion_service.get_streaming_chat_message_content(
            chat_history=chat_history, settings=settings, kernel=kernel
        ):
            logger.info(
                f"{type(message_content_chunk)}: {message_content_chunk.model_dump_json(indent=2, exclude_none=True)}"
            )
            if message_content_chunk is None:
                continue
            yield AgentResponseItem(
                message=message_content_chunk,
                thread=agent_thread,
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
        return cls(**fields, kernel=kernel)

    @kernel_function(
        name=WEB_SEARCH_AND_FETCH_FUNCTION_NAME,
        description="Search the web using either a query or specific links. When links are provided, retrieve content from those URLs directly. When no links are provided, use the query to search the web.",
    )
    async def __web_search_and_fetch(
        self,
        query: Annotated[str, "The query to search for"] = None,
        language: Annotated[str, "The language to search for"] = "en",
        links: Annotated[list[str], "The links to search for"] = None,
    ) -> Annotated[AsyncGenerator[WebSearchAndFetchResult], "The search results"]:
        import httpx

        WEB_SEARCH_BASE_URL = os.getenv("WEB_SEARCH_BASE_URL", "http://localhost:9000")
        logger.info(f"WEB_SEARCH_BASE_URL = {WEB_SEARCH_BASE_URL}")

        async def __fetch_content_of_url(
            url: str, query: str | None = None, title: str | None = None
        ) -> dict[str, Any]:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(60.0 * 3, connect=60.0)
            ) as client:
                response = await client.post(
                    urljoin(WEB_SEARCH_BASE_URL, "/api/v1/web_page_fetch"),
                    json={"url": url, "query": query, "title": title},
                )
                response.raise_for_status()
                return response.json()

        async def __web_search(query: str, language: str = "en") -> dict[str, Any]:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(60.0, connect=60.0)
            ) as client:
                response = await client.post(
                    urljoin(WEB_SEARCH_BASE_URL, "/api/v1/web_search"),
                    json={"query": query, "language": language},
                )
                response.raise_for_status()
                return response.json()

        logger.info(f"web_search_and_retrieve: {query}, {links}")
        if links is not None and len(links) > 0:
            for link in links:
                request_id = str(uuid.uuid4())
                yield WebSearchAndFetchResult(
                    request_id=request_id,
                    request_type="web_page_fetch_begin",
                    query=query,
                    arguments={
                        "url": link,
                    },
                )
                page_content = await __fetch_content_of_url(link)
                yield WebSearchAndFetchResult(
                    request_id=request_id,
                    request_type="web_page_fetch_end",
                    query=query,
                    result=page_content,
                )
        if query is not None and len(query) > 0:
            request_id = str(uuid.uuid4())
            yield WebSearchAndFetchResult(
                request_id=request_id,
                request_type="web_search_begin",
                query=query,
                arguments={
                    "query": query,
                    "language": language,
                },
            )
            results = await __web_search(query, language)
            results["results"] = results.get("results", [])[0:2]
            yield WebSearchAndFetchResult(
                request_id=request_id,
                request_type="web_search_end",
                query=query,
                result=results,
            )
            search_results = results["results"] if "results" in results else []
            for result in search_results:
                url = result["url"]
                title = result["title"]
                request_id = str(uuid.uuid4())
                yield WebSearchAndFetchResult(
                    request_id=request_id,
                    request_type="web_page_fetch_begin",
                    query=query,
                    arguments={
                        "url": url,
                        "title": title,
                    },
                )
                page_content = await __fetch_content_of_url(
                    url=url, query=query, title=title
                )
                yield WebSearchAndFetchResult(
                    request_id=request_id,
                    request_type="web_page_fetch_end",
                    query=query,
                    result=page_content,
                )
            # return MetaSearchResult(query=query, docs=[MetaSearchDoc(content=result["content"], metadata=result["metadata"]) for result in data["results"]])
        else:
            raise ValueError("No query or links provided")
