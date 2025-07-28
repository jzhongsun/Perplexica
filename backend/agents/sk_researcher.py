import asyncio
from collections.abc import AsyncIterable, Awaitable, Callable
from functools import reduce
import logging.config
import os
import uuid
from agents.utils import (
    parse_json_response,
    get_buffer_string,
    get_today_str,
)
from semantic_kernel.agents import (
    Agent,
    DeclarativeSpecMixin,
    AgentThread,
    AgentResponseItem,
    ChatHistoryAgentThread,
    AgentThread,
)
from enum import Enum
from pydantic import BaseModel, Field
from typing import (
    Literal,
    Optional,
    Any,
    override,
    Tuple,
    Annotated,
    Any,
)

from semantic_kernel.connectors.ai.chat_completion_client_base import (
    ChatCompletionClientBase,
)
import json
from semantic_kernel.connectors.ai.function_choice_behavior import (
    FunctionChoiceBehavior,
)
from semantic_kernel.contents import (
    ChatMessageContent,
    AuthorRole,
    FunctionCallContent,
    FunctionResultContent,
    StreamingChatMessageContent,
    ChatHistory,
)

from semantic_kernel.utils.telemetry.agent_diagnostics.decorators import (
    trace_agent_get_response,
    trace_agent_invocation,
)
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.connectors.ai import PromptExecutionSettings
from semantic_kernel.kernel import Kernel, KernelPlugin, KernelArguments
from semantic_kernel.functions import kernel_function, KernelFunction
from agents.sk_researcher_prompts import (
    clarify_with_user_instructions,
    lead_researcher_prompt,
    transform_messages_into_research_topic_prompt,
    final_report_generation_prompt,
    compress_research_system_prompt,
    compress_research_simple_human_message,
    research_system_prompt,
    summarize_webpage_prompt,
)
from openai import AsyncOpenAI

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


class DeepResearcherAgentConfig(BaseModel):
    # General Configuration
    max_structured_output_retries: int = Field(default=3, metadata={})
    allow_clarification: bool = Field(default=True, metadata={})
    max_concurrent_research_units: int = Field(default=5, metadata={})
    # Research Configuration
    search_api: Optional[str] = Field(default="tavily", metadata={})
    max_react_tool_calls: int = Field(default=5, metadata={})
    max_researcher_iterations: int = Field(default=3, metadata={})

    # Model Configuration
    clarify_model: str = Field(default="openai:gpt-4.1", metadata={})
    clarify_model_max_tokens: int = Field(default=8192, metadata={})
    clarify_model_config: Optional[dict[str, Any]] = Field(
        default=None, optional=True, metadata={}
    )
    summarization_model: str = Field(default="openai:gpt-4.1", metadata={})
    summarization_model_max_tokens: int = Field(default=8192, metadata={})
    summarization_model_config: Optional[dict[str, Any]] = Field(
        default=None, optional=True, metadata={}
    )
    research_model: str = Field(default="openai:gpt-4.1", metadata={})
    research_model_max_tokens: int = Field(default=10000, metadata={})
    research_model_config: Optional[dict[str, Any]] = Field(
        default=None, optional=True, metadata={}
    )
    compression_model: str = Field(default="openai:gpt-4.1-mini", metadata={})
    compression_model_max_tokens: int = Field(default=8192, metadata={})
    compression_model_config: Optional[dict[str, Any]] = Field(
        default=None, optional=True, metadata={}
    )
    final_report_model: str = Field(default="openai:gpt-4.1", metadata={})
    final_report_model_max_tokens: int = Field(default=10000, metadata={})
    final_report_model_config: Optional[dict[str, Any]] = Field(
        default=None, optional=True, metadata={}
    )

    # MCP server configuration
    # mcp_config: Optional[MCPConfig] = Field(default=None, optional=True, metadata={})
    mcp_prompt: Optional[str] = Field(default=None, optional=True, metadata={})

    # Prompt Configuration
    clarify_with_user_instructions: str = Field(
        default=clarify_with_user_instructions,
        description="The instructions to clarify with the user.",
    )
    lead_researcher_prompt: str = Field(
        default=lead_researcher_prompt, description="The prompt to lead the researcher."
    )
    transform_messages_into_research_topic_prompt: str = Field(
        default=transform_messages_into_research_topic_prompt,
        description="The prompt to transform the messages into a research topic.",
    )
    final_report_generation_prompt: str = Field(
        default=final_report_generation_prompt,
        description="The prompt to generate the final report.",
    )
    compress_research_system_prompt: str = Field(
        default=compress_research_system_prompt,
        description="The prompt to compress the research.",
    )
    compress_research_simple_human_message: str = Field(
        default=compress_research_simple_human_message,
        description="The simple human message to compress the research.",
    )
    research_system_prompt: str = Field(
        default=research_system_prompt,
        description="The prompt to conduct research.",
    )

    class Config:
        arbitrary_types_allowed = True


class DeepResearcherAgentStep(Enum):
    CLARIFY_WITH_USER = "clarify_with_user"
    WRITE_RESEARCH_BRIEF = "write_research_brief"
    RESEARCH_SUPERVISOR = "research_supervisor"
    FINAL_REPORT_GENERATION = "final_report_generation"
    END = "end"


class DeepResearcherAgentState(BaseModel):
    next_step: DeepResearcherAgentStep = Field(
        default=DeepResearcherAgentStep.CLARIFY_WITH_USER,
        description="The next step in the researcher agent.",
    )
    messages: list[ChatMessageContent] = Field(
        default=[],
        description="The messages in the conversation.",
    )
    research_brief: str = Field(
        default="",
        description="The research brief.",
    )
    supervisor_messages: list[ChatMessageContent] = Field(
        default=[],
        description="The messages in the supervisor conversation.",
    )
    research_iterations: int = Field(
        default=0,
        description="The number of research iterations.",
    )

    final_report: str = Field(
        default="",
        description="The final report.",
    )
    notes: list[str] = Field(
        default=[],
        description="The notes from the research.",
    )


class SupervisorStep(Enum):
    SUPERVISOR = "supervisor"
    SUPERVISOR_TOOLS = "supervisor_tools"
    END = "end"


class SupervisorState(BaseModel):
    agent_state: DeepResearcherAgentState = Field(
        default=DeepResearcherAgentState(),
        description="The state of the agent.",
    )
    next_step: SupervisorStep = Field(
        default=SupervisorStep.SUPERVISOR,
        description="The next step in the supervisor.",
    )
    supervisor_messages: list[ChatMessageContent] = Field(
        default=[],
        description="The messages in the supervisor conversation.",
    )
    research_iterations: int = Field(
        default=0,
        description="The number of research iterations.",
    )
    notes: list[str] = Field(
        default=[],
        description="The notes from the research.",
    )
    raw_notes: list[str] = Field(
        default=[],
        description="The raw notes from the research.",
    )


class ResearcherStep(Enum):
    RESEARCH = "research"
    RESEARCH_TOOLS = "research_tools"
    COMPRESS_RESEARCH = "compress_research"
    END = "end"


class ResearcherState(BaseModel):
    agent_state: DeepResearcherAgentState = Field(
        default=DeepResearcherAgentState(),
        description="The state of the agent.",
    )
    next_step: ResearcherStep = Field(
        default=ResearcherStep.RESEARCH,
        description="The next step in the researcher.",
    )
    researcher_messages: list[ChatMessageContent] = Field(
        default=[],
        description="The messages in the research conversation.",
    )
    research_topic: str = Field(
        default="",
        description="The research topic.",
    )
    compressed_research: str = Field(
        default="",
        description="The compressed research.",
    )
    raw_notes: list[str] = Field(
        default=[],
        description="The raw notes from the research.",
    )
    research_iterations: int = Field(
        default=0,
        description="The number of research iterations.",
    )
    tool_call_iterations: int = Field(
        default=0,
        description="The number of tool call iterations.",
    )


async def summarize_webpage(
    model: ChatCompletionClientBase, settings: PromptExecutionSettings, webpage_content: str, kernel: Kernel
) -> str:
    try:
        response = await asyncio.wait_for(
            model.get_chat_message_content(
                ChatHistory(
                    messages=[
                        ChatMessageContent(
                            role=AuthorRole.USER,
                            content=summarize_webpage_prompt.format(
                                webpage_content=webpage_content, date=get_today_str()
                            ),
                        )
                    ]
                ),
                settings,
                kernel=kernel,
            ),
            timeout=60.0,
        )
        summary_response = parse_json_response(response.content)
        return f"""<summary>\n{summary_response['summary']}\n</summary>\n\n<key_excerpts>\n{summary_response['key_excerpts']}\n</key_excerpts>"""
    except (asyncio.TimeoutError, Exception) as e:
        logger.warning(f"Failed to summarize webpage: {str(e)}")
        return webpage_content

async def tavily_search_async(search_queries: list[str], max_results: int = 5, topic: Literal["general", "news", "finance"] = "general", include_raw_content: bool = True, include_domains: list[str] = [], exclude_domains: list[str] = []):
    from tavily import AsyncTavilyClient
    tavily_async_client = AsyncTavilyClient()
    search_tasks = []
    for query in search_queries:
            search_tasks.append(
                tavily_async_client.search(
                    query,
                    max_results=max_results,
                    include_raw_content=include_raw_content,
                    topic=topic,
                    include_domains=include_domains,
                    exclude_domains=exclude_domains,
                )
            )
    search_docs = await asyncio.gather(*search_tasks)
    for search_doc in search_docs:
        logger.info(f"tavily_search_async - search_doc: {search_doc['query']}, {len(search_doc['results'])} results")
        for result in search_doc['results']:
            print(f"> {result['url']}\n  {result['title']}\n  {result['content'][:100]}")
    return search_docs

async def crawai_web_fetch_async(urls: list[str]):
    from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig, CacheMode, DefaultMarkdownGenerator
    browser_config = BrowserConfig(
        headless=False
    )
    run_config = CrawlerRunConfig(
        markdown_generator=DefaultMarkdownGenerator(
            options={
                "ignore_links": True,
                "escape_html": False,
                "body_width": 80
            }),
        
        # Content filtering
        word_count_threshold=10,
        excluded_tags=['form', 'header'],
        exclude_external_links=True,

        # Content processing
        process_iframes=True,
        remove_overlay_elements=True,
                
        cache_mode=CacheMode.ENABLED,  # Use cache if available
        wait_until="networkidle",
        pdf=True,
        stream=True,
    )
    async with AsyncWebCrawler(config=browser_config) as crawler:
        results = []
        for url in urls:
            try:
                result = await crawler.arun(url=url, config=run_config)
                print(f'crawai_web_fetch_async - {url} - {result.success} - {result.markdown}')
                results.append({
                    "url": url,
                    "success": result.success,
                    "markdown": str(result.markdown),
                })
            except Exception as e:
                logger.error(f"Error fetching {url}: {e}")
                results.append({
                    "url": url,
                    "success": False,
                    "markdown": "",
                })
                continue
        return results

web_search_tool_name = "web_search"

async def _web_search(
    configurable: DeepResearcherAgentConfig,
    kernel: Kernel,
    queries: Annotated[list[str], "The queries to search for"],
    max_results: Annotated[int, "The maximum number of results to return"] = 5,
    topic: Annotated[Literal["general", "news", "finance"], 'The category of the search. Determines which agent will be used. Supported values are "general" and "news".'] = "general",
    include_domains: Annotated[list[str], "A list of domains to specifically include in the search results."] = [],
    exclude_domains: Annotated[list[str], "A list of domains to specifically exclude from the search results."] = [],
):
    logger.info(f"web_search - queries: {queries}, max_results: {max_results}, topic: {topic}, include_domains: {include_domains}, exclude_domains: {exclude_domains}")
    unique_results = {}
    search_results = await tavily_search_async(
        queries,
        max_results=max_results,
        topic=topic,
        include_raw_content=True,
        include_domains=include_domains,
        exclude_domains=exclude_domains,
    )
    for search_result in search_results:
        for result in search_result['results']:
            url = result['url']
            if url not in unique_results:
                unique_results[url] = {**result, "query": search_result['query']}
                
    urls_web_fetch = [url for url in unique_results.keys() if not unique_results[url].get("raw_content") or len(unique_results[url]['raw_content']) < 100]
    crawai_results = await crawai_web_fetch_async(urls_web_fetch)
    for crawai_result in crawai_results:
        if crawai_result['success']:
            unique_results[crawai_result['url']]['raw_content'] = crawai_result['markdown']

    max_char_to_include = 50_000   # NOTE: This can be tuned by the developer. This character count keeps us safely under input token limits for the latest models.
    summarization_model = kernel.get_service(
        service_id=configurable.summarization_model, type=ChatCompletionClientBase
    )
    settings = summarization_model.instantiate_prompt_execution_settings(
        model=configurable.summarization_model,
        max_tokens=configurable.summarization_model_max_tokens,
    )        
    async def noop():
        return None
    
    summarization_tasks = [
        noop() if not result.get("raw_content") else summarize_webpage(
            summarization_model, 
            settings,
            result['raw_content'][:max_char_to_include],
            kernel,
        )
        for result in unique_results.values()
    ]
    summaries = await asyncio.gather(*summarization_tasks)
    summarized_results = {
        url: {'query': result['query'], 'title': result['title'], 'content': result['content'] if summary is None else summary}
        for url, result, summary in zip(unique_results.keys(), unique_results.values(), summaries)
    }
    
    final_outputs = []

    for i, (url, result) in enumerate(summarized_results.items()):
        final_outputs.append({
            # "source": i + 1,
            "query": result['query'],
            "title": result['title'],
            "url": url,
            "summary": result['content'],
        })
    if summarized_results:
        return json.dumps({
            "success": True,
            "query": queries,
            "results": final_outputs,
        }, indent=2, ensure_ascii=False)
    else:
        return json.dumps({
            "success": False,
            "query": queries,
            "error": "No valid search results found. Please try different search queries or use a different search API.",
        }, indent=2, ensure_ascii=False)

@kernel_function(
    name=web_search_tool_name, 
    description="A search engine optimized for comprehensive, accurate, and trusted results. Useful for when you need to answer questions about current events.."
)
async def _web_search_wrapper(
    queries: Annotated[list[str], "The queries to search for"],
    max_results: Annotated[int, "The maximum number of results to return"] = 5,
    topic: Annotated[Literal["general", "news", "finance"], 'The category of the search. Determines which agent will be used. Supported values are "general" and "news".'] = "general",
    include_domains: Annotated[list[str], "A list of domains to specifically include in the search results."] = [],
    exclude_domains: Annotated[list[str], "A list of domains to specifically exclude from the search results."] = [],
):
    pass

def get_all_tools(
    configurable: DeepResearcherAgentConfig,
) -> tuple[list[str], list[str]]:
    functions = [plugin_name + "-" + research_complete_tool_name]
    plugins = [plugin_name]

    if configurable.search_api:
        functions.append(plugin_name + "-" + web_search_tool_name)
    return functions, plugins


async def researcher(
    state: ResearcherState,
    kernel: Kernel,
    configurable: DeepResearcherAgentConfig,
    thread: AgentThread,
):
    research_messages = state.researcher_messages if state.researcher_messages else []
    functions, plugins = get_all_tools(configurable)
    logger.info(f"researcher - functions: {functions} \n plugins: {plugins}")
    if len(functions) == 0:
        raise ValueError(
            "No tools found to conduct research: Please configure either your search API or add MCP tools to your configuration."
        )

    research_model = kernel.get_service(
        service_id=configurable.research_model, type=ChatCompletionClientBase
    )
    settings = research_model.instantiate_prompt_execution_settings(
        model=configurable.research_model,
        max_tokens=configurable.research_model_max_tokens,
    )
    settings.function_choice_behavior = FunctionChoiceBehavior.Required(
        auto_invoke=False,
        auto_invoke_kernel_functions=False,
        filters={"included_functions": functions, "included_plugins": plugins},
    )
    researcher_system_prompt = configurable.research_system_prompt.format(
        mcp_prompt=configurable.mcp_prompt or "", date=get_today_str()
    )
    for _ in range(configurable.max_structured_output_retries):
        try:
            response = await research_model.get_chat_message_content(
                ChatHistory(messages=[ChatMessageContent(role=AuthorRole.SYSTEM, content=researcher_system_prompt)] + research_messages), settings, kernel=kernel
            )
            include_research_complete_tool_call = any(
                isinstance(item, FunctionCallContent)
                and item.function_name == research_complete_tool_name
                for item in response.items
            )
            if include_research_complete_tool_call:
                state.next_step = ResearcherStep.COMPRESS_RESEARCH
                return
            state.researcher_messages = research_messages + [response]
            state.tool_call_iterations = state.tool_call_iterations + 1
            state.next_step = ResearcherStep.RESEARCH_TOOLS
            return
        except Exception as e:
            logger.error(f"Error in researcher: {e}")
            continue
    logger.error(f"Error in researcher: Maximum retries exceeded")
    raise Exception("Error in researcher: Maximum retries exceeded")


async def execute_tool_safely(
    tool_call: FunctionCallContent, configurable: DeepResearcherAgentConfig, kernel: Kernel
):
    try:
        # return await tool_call.invoke(configurable)
        logger.info(f"execute_tool_safely - tool_call: {tool_call}")
        if tool_call.function_name == web_search_tool_name:
            args = tool_call.parse_arguments()
            result = await _web_search(configurable, kernel, **args)
            logger.info(f"execute_tool_safely - result: {result}")
            return result
        return f"SUCCESSFUL TOOL CALL " + str(uuid.uuid4()) + " \n " + str(tool_call)
    except Exception as e:
        return f"Error executing tool: {str(e)}"


async def researcher_tools(
    state: ResearcherState,
    kernel: Kernel,
    configurable: DeepResearcherAgentConfig,
    thread: AgentThread,
):
    researcher_messages = state.researcher_messages if state.researcher_messages else []
    most_recent_message = researcher_messages[-1]
    # Early Exit Criteria: No tool calls (or native web search calls)were made by the researcher

    shall_continue_research_loop = True
    for item in most_recent_message.items:
        if isinstance(item, FunctionCallContent):
            if item.function_name == research_complete_tool_name:
                shall_continue_research_loop = False
                break
    logger.info(
        f"researcher_tools - shall_continue_research_loop: {shall_continue_research_loop}"
    )
    if not shall_continue_research_loop:
        state.next_step = ResearcherStep.COMPRESS_RESEARCH
        return

    has_web_search_tool_calls = any(
        item.function_name == web_search_tool_name
        for item in most_recent_message.items
        if isinstance(item, FunctionCallContent)
    )
    if not has_web_search_tool_calls:
        state.next_step = ResearcherStep.COMPRESS_RESEARCH
        return

    tool_calls = [
        item
        for item in most_recent_message.items
        if isinstance(item, FunctionCallContent)
        and item.function_name != research_complete_tool_name
    ]
    logger.info(f"researcher_tools - tool_calls: {tool_calls}")
    # Otherwise, execute tools and gather results.
    coros = [execute_tool_safely(tool_call, configurable, kernel) for tool_call in tool_calls]
    observations = await asyncio.gather(*coros)
    tool_outputs = [
        FunctionResultContent.from_function_call_content_and_result(
            function_call_content=tool_call,
            result=observation,
        )
        for observation, tool_call in zip(observations, tool_calls)
    ]

    # Late Exit Criteria: We have exceeded our max guardrail tool call iterations or the most recent message contains a ResearchComplete tool call
    # These are late exit criteria because we need to add ToolMessages
    state.researcher_messages = state.researcher_messages + [
        item.to_chat_message_content() for item in tool_outputs
    ]
    if state.tool_call_iterations >= configurable.max_react_tool_calls or any(
        tool_call.function_name == research_complete_tool_name
        for tool_call in tool_calls
    ):
        state.next_step = ResearcherStep.COMPRESS_RESEARCH
        return
    state.next_step = ResearcherStep.RESEARCH


async def compress_research(
    state: ResearcherState,
    kernel: Kernel,
    configurable: DeepResearcherAgentConfig,
    thread: AgentThread,
) -> Tuple[DeepResearcherAgentStep, list[ChatMessageContent]]:
    synthesis_attempts = 0
    synthesizer_model = kernel.get_service(
        service_id=configurable.compression_model, type=ChatCompletionClientBase
    )
    settings = synthesizer_model.instantiate_prompt_execution_settings(
        model=configurable.compression_model,
        max_tokens=configurable.compression_model_max_tokens,
    )
    researcher_messages = state.researcher_messages if state.researcher_messages else []
    # Update the system prompt to now focus on compression rather than research.
    compress_research_system_prompt = configurable.compress_research_system_prompt
    compress_research_simple_human_message = (
        configurable.compress_research_simple_human_message
    )
    researcher_messages.append(
        ChatMessageContent(
            role=AuthorRole.USER, content=compress_research_simple_human_message
        )
    )
    while synthesis_attempts < 3:
        try:
            response = await synthesizer_model.get_chat_message_content(
                ChatHistory(messages=[ChatMessageContent(role=AuthorRole.SYSTEM, content=compress_research_system_prompt.format(date=get_today_str()))] + researcher_messages), 
                settings, kernel=kernel
            )
            state.compressed_research = str(response.content)
            state.raw_notes = [
                "\n".join(
                    [
                        str(m.content)
                        # for m in filter_messages(researcher_messages, include_types=["tool", "ai"])
                        for m in researcher_messages
                        if m.role == AuthorRole.ASSISTANT or m.role == AuthorRole.TOOL
                    ]
                )
            ]
            state.next_step = ResearcherStep.END
            state.compressed_research = str(response.content)
            state.raw_notes = [
                "\n".join(
                    [
                        str(m.content)
                        for m in researcher_messages
                        if m.role == AuthorRole.ASSISTANT or m.role == AuthorRole.TOOL
                    ]
                )
            ]
            return
        except Exception as e:
            logger.error(f"Error synthesizing research report: {e}")
            synthesis_attempts += 1
            if is_token_limit_exceeded(e, configurable.research_model):
                researcher_messages = remove_up_to_last_ai_message(researcher_messages)
                print(
                    f"Token limit exceeded while synthesizing: {e}. Pruning the messages to try again."
                )
                continue
            print(f"Error synthesizing research report: {e}")
    state.next_step = ResearcherStep.END
    state.compressed_research = (
        "Error synthesizing research report: Maximum retries exceeded"
    )
    state.raw_notes = [
        "\n".join(
            [
                str(m.content)
                for m in researcher_messages
                if m.role == AuthorRole.ASSISTANT or m.role == AuthorRole.TOOL
            ]
        )
    ]


async def invoke_researcher_engine(
    state: ResearcherState,
    kernel: Kernel,
    configurable: DeepResearcherAgentConfig,
    thread: AgentThread,
):
    # logger.info(f"invoke_researcher_engine - state - research_messages: {state.researcher_messages}")
    step = state.next_step
    while (
        step != ResearcherStep.END
        and state.research_iterations < configurable.max_researcher_iterations
    ):
        if step == ResearcherStep.RESEARCH:
            await researcher(
                state=state,
                kernel=kernel,
                configurable=configurable,
                thread=thread,
            )
        elif step == ResearcherStep.RESEARCH_TOOLS:
            await researcher_tools(
                state=state,
                kernel=kernel,
                configurable=configurable,
                thread=thread,
            )
        elif step == ResearcherStep.COMPRESS_RESEARCH:
            await compress_research(
                state=state,
                kernel=kernel,
                configurable=configurable,
                thread=thread,
            )
        step = state.next_step


conduct_research_tool_name = "conduct_research"
research_complete_tool_name = "research_complete"


@kernel_function(
    name=conduct_research_tool_name,
    description="Conduct research on the given topic.",
)
async def _conduct_research(
    research_topic: Annotated[str, "The topic of the research."],
):
    logger.info(f"[TOOL-INVOCATION] Conducting research on topic: {research_topic}")


@kernel_function(
    name=research_complete_tool_name,
    description="Research is complete.",
)
async def _research_complete():
    logger.info(f"[TOOL-INVOCATION] Research is complete.")


async def supervisor(
    state: SupervisorState,
    kernel: Kernel,
    configurable: DeepResearcherAgentConfig,
    thread: AgentThread,
):
    research_model = kernel.get_service(
        service_id=configurable.research_model, type=ChatCompletionClientBase
    )
    settings = research_model.instantiate_prompt_execution_settings(
        model=configurable.research_model,
        max_tokens=configurable.research_model_max_tokens,
    )
    settings.function_choice_behavior = FunctionChoiceBehavior.Required(
        auto_invoke=False,
        auto_invoke_kernel_functions=False,
        filters={
            "included_functions": [
                plugin_name + "-" + conduct_research_tool_name,
                plugin_name + "-" + research_complete_tool_name,
            ],
            "included_plugins": [plugin_name],
        },
    )
    supervisor_messages = state.supervisor_messages if state.supervisor_messages else []
    chat_history = ChatHistory(messages=supervisor_messages)
    for _ in range(configurable.max_structured_output_retries):
        try:
            response = await research_model.get_chat_message_content(
                chat_history, settings, kernel=kernel
            )
            # logger.info(f"Supervisor response: {response.model_dump_json(indent=2)}")
            has_research_complete_tool_call = any(
                isinstance(item, FunctionCallContent)
                and item.function_name == research_complete_tool_name
                for item in response.items
            )
            if has_research_complete_tool_call:
                state.next_step = SupervisorStep.END
                state.notes = get_notes_from_tool_calls(supervisor_messages)
                logger.info(f"Supervisor has_research_complete_tool_call: with notes: {state.notes}")
                return

            supervisor_messages.append(response)
            state.supervisor_messages = supervisor_messages
            state.research_iterations = state.research_iterations + 1
            state.next_step = SupervisorStep.SUPERVISOR_TOOLS
            return
        except Exception as e:
            logger.error(f"Error in supervisor: {e}")
            continue
    logger.error(f"Error in supervisor: Maximum retries exceeded")
    raise Exception("Error in supervisor: Maximum retries exceeded")


def get_notes_from_tool_calls(messages: list[ChatMessageContent]) -> list[str]:
    notes = []
    for message in messages:
        for item in message.items:
            if isinstance(item, FunctionResultContent):
                notes.append(item.result)
    return notes


async def supervisor_tools_stream(
    state: SupervisorState,
    kernel: Kernel,
    configurable: DeepResearcherAgentConfig,
    thread: AgentThread,
) -> AsyncIterable[AgentResponseItem[StreamingChatMessageContent]]:
    supervisor_messages = state.supervisor_messages if state.supervisor_messages else []
    research_iterations = state.research_iterations if state.research_iterations else 0
    most_recent_message = supervisor_messages[-1]
    # Exit Criteria
    # 1. We have exceeded our max guardrail research iterations
    # 2. No tool calls were made by the supervisor
    # 3. The most recent message contains a ResearchComplete tool call and there is only one tool call in the message
    exceeded_allowed_iterations = (
        research_iterations >= configurable.max_researcher_iterations
    )
    tool_calls = [
        item
        for item in most_recent_message.items
        if isinstance(item, FunctionCallContent)
    ]
    logger.info(f"supervisor_tools_stream - tool_calls: {tool_calls}")
    no_tool_calls = tool_calls is None or len(tool_calls) == 0
    research_complete_tool_call = any(
        tool_call.function_name == research_complete_tool_name
        for tool_call in tool_calls
    )
    if exceeded_allowed_iterations or no_tool_calls or research_complete_tool_call:
        state.next_step = SupervisorStep.END
        state.notes = get_notes_from_tool_calls(supervisor_messages)
        return
    # Otherwise, conduct research and gather results.
    try:
        all_conduct_research_calls = [
            tool_call
            for tool_call in tool_calls
            if tool_call.function_name == conduct_research_tool_name
        ]
        conduct_research_calls = all_conduct_research_calls[
            : configurable.max_concurrent_research_units
        ]
        overflow_conduct_research_calls = all_conduct_research_calls[
            configurable.max_concurrent_research_units :
        ]
        # logger.info(f"supervisor_tools_stream - researcher_system_prompt: {researcher_system_prompt} \n {conduct_research_calls}")
        coros = []
        for tool_call in conduct_research_calls:
            research_state = ResearcherState(
                agent_state=state.agent_state,
                next_step=ResearcherStep.RESEARCH,
                researcher_messages=[
                    ChatMessageContent(
                        role=AuthorRole.USER,
                        content=tool_call.parse_arguments()["research_topic"],
                    ),
                ],
                research_topic=tool_call.parse_arguments()["research_topic"],
                compressed_research="",
            )

            async def invoke_researcher_engine_wrapper(
                state: ResearcherState,
                kernel: Kernel,
                configurable: DeepResearcherAgentConfig,
                thread: AgentThread,
            ) -> ResearcherState:
                await invoke_researcher_engine(
                    state=state,
                    kernel=kernel,
                    configurable=configurable,
                    thread=thread,
                )
                return research_state

            coros.append(
                invoke_researcher_engine_wrapper(
                    research_state, kernel, configurable, thread
                )
            )

        tool_results = await asyncio.gather(*coros)
        tool_messages = [
            FunctionResultContent.from_function_call_content_and_result(
                function_call_content=tool_call,
                result=observation.compressed_research
                or "Error synthesizing research report: Maximum retries exceeded",
            ).to_chat_message_content()
            for observation, tool_call in zip(tool_results, conduct_research_calls)
        ]
        # Handle any tool calls made > max_concurrent_research_units
        for overflow_conduct_research_call in overflow_conduct_research_calls:
            tool_messages.append(
                FunctionResultContent.from_function_call_content_and_result(
                    function_call_content=overflow_conduct_research_call,
                    result=f"Error: Did not run this research as you have already exceeded the maximum number of concurrent research units. Please try again with {configurable.max_concurrent_research_units} or fewer research units.",
                ).to_chat_message_content()
            )
        raw_notes_concat = "\n".join(
            ["\n".join(observation.raw_notes or []) for observation in tool_results]
        )
        state.supervisor_messages = supervisor_messages + tool_messages
        state.raw_notes = state.raw_notes + [raw_notes_concat]
        state.research_iterations = state.research_iterations + 1
        state.next_step = SupervisorStep.SUPERVISOR
        return
    except Exception as e:
        logger.error(f"Error in supervisor_tools_stream: {e}")
        if is_token_limit_exceeded(e, configurable.research_model):
            print(f"Token limit exceeded while reflecting: {e}")
        else:
            print(f"Other error in reflection phase: {e}")
        state.next_step = SupervisorStep.END
        # return Command(
        #     goto=END,
        #     update={
        #         "notes": get_notes_from_tool_calls(supervisor_messages),
        #         "research_brief": state.get("research_brief", ""),
        #     },
        # )


async def research_supervisor(
    state: DeepResearcherAgentState,
    kernel: Kernel,
    configurable: DeepResearcherAgentConfig,
    thread: AgentThread,
):
    supervisor_state = SupervisorState(
        agent_state=state,
        next_step=SupervisorStep.SUPERVISOR,
        supervisor_messages=state.supervisor_messages,
        research_iterations=0,
    )
    step = supervisor_state.next_step
    while (
        step != SupervisorStep.END
        and supervisor_state.research_iterations
        < configurable.max_researcher_iterations
    ):
        if step == SupervisorStep.SUPERVISOR:
            await supervisor(
                state=supervisor_state,
                kernel=kernel,
                configurable=configurable,
                thread=thread,
            )
        elif step == SupervisorStep.SUPERVISOR_TOOLS:
            await supervisor_tools_stream(
                supervisor_state, kernel, configurable, thread
            )

        step = supervisor_state.next_step

    # logger.info(f"supervisor_state: {supervisor_state.model_dump_json(indent=2)}")
    state.notes = supervisor_state.notes
    state.next_step = DeepResearcherAgentStep.FINAL_REPORT_GENERATION
    logger.info(f"research_supervisor complete with notes:\n {json.dumps(state.notes, indent=2, ensure_ascii=False)}")


plugin_name = "researcher"
clarify_completed_tool_name = "clarity_completed"


@kernel_function(
    name=clarify_completed_tool_name,
    description="Notify the user that you will start research after the user has provided the necessary information.",
)
async def _clarity_completed(
    verification: Annotated[
        str,
        "Verification message that we will start research after the user has provided the necessary information.",
    ],
):
    logger.info(f"clarity_completed: {verification}")


async def clarify_with_user_stream(
    state: DeepResearcherAgentState,
    kernel: Kernel,
    configurable: DeepResearcherAgentConfig,
    thread: AgentThread,
) -> AsyncIterable[AgentResponseItem[StreamingChatMessageContent]]:
    """
    Clarify with the user if they need to be asked a clarifying question.
    """
    if not configurable.allow_clarification:
        state.next_step = DeepResearcherAgentStep.WRITE_RESEARCH_BRIEF
        return

    messages = state.messages
    model = kernel.get_service(
        service_id=configurable.clarify_model, type=ChatCompletionClientBase
    )
    settings = model.instantiate_prompt_execution_settings(
        model=configurable.clarify_model,
        max_tokens=configurable.clarify_model_max_tokens,
    )
    settings.function_choice_behavior = FunctionChoiceBehavior.Auto(
        auto_invoke=False,
        auto_invoke_kernel_functions=False,
        filters={
            "included_functions": [plugin_name + "-" + clarify_completed_tool_name],
            "included_plugins": [plugin_name],
        },
    )
    clarify_with_user_instructions = configurable.clarify_with_user_instructions.format(
        messages=get_buffer_string(messages), date=get_today_str()
    )
    chat_history = ChatHistory(
        messages=[
            ChatMessageContent(
                role=AuthorRole.USER, content=clarify_with_user_instructions
            )
        ]
    )

    all_messages: list[StreamingChatMessageContent] = []
    function_call_returned = False
    async for response in model.get_streaming_chat_message_content(
        chat_history, settings, kernel=kernel
    ):
        if response is None:
            continue

        all_messages.append(response)
        if not function_call_returned and any(
            isinstance(item, FunctionCallContent) for item in response.items
        ):
            function_call_returned = True
        role = response.role
        if (
            role == AuthorRole.ASSISTANT
            and (response.items or response.metadata.get("usage"))
            and not any(
                isinstance(item, (FunctionCallContent, FunctionResultContent))
                for item in response.items
            )
        ):
            yield AgentResponseItem(message=response, thread=thread)

    full_completion: StreamingChatMessageContent = reduce(
        lambda x, y: x + y, all_messages
    )
    # logger.info(f"full_completion = \n{full_completion}")
    if not function_call_returned:
        state.next_step = DeepResearcherAgentStep.END
        state.messages.append(
            ChatMessageContent(
                role=AuthorRole.ASSISTANT,
                content=full_completion.content,
                metadata=full_completion.metadata,
            )
        )
        return

    function_calls = [
        item for item in full_completion.items if isinstance(item, FunctionCallContent)
    ]
    logger.info(f"clarify_with_user_stream function_calls = \n{function_calls}")
    if len(function_calls) > 1:
        raise Exception("Expected only one function call, got multiple")
    if function_calls[0].function_name == clarify_completed_tool_name:
        args = function_calls[0].parse_arguments()
        if args is None:
            raise Exception(
                "Expected the clarify_completed tool to be called, got something else"
            )
        state.messages.append(
            ChatMessageContent(role=AuthorRole.ASSISTANT, content=args["verification"])
        )
        state.next_step = DeepResearcherAgentStep.WRITE_RESEARCH_BRIEF
    else:
        raise Exception(
            "Expected the clarify_completed tool to be called, got something else"
        )


async def write_research_brief_stream(
    state: DeepResearcherAgentState,
    kernel: Kernel,
    configurable: DeepResearcherAgentConfig,
    thread: AgentThread,
) -> AsyncIterable[AgentResponseItem[StreamingChatMessageContent]]:
    research_model = kernel.get_service(
        service_id=configurable.research_model, type=ChatCompletionClientBase
    )
    settings = research_model.instantiate_prompt_execution_settings(
        model=configurable.research_model,
        max_tokens=configurable.research_model_max_tokens,
    )
    chat_history = ChatHistory(
        messages=[
            ChatMessageContent(
                role=AuthorRole.USER,
                content=configurable.transform_messages_into_research_topic_prompt.format(
                    messages=get_buffer_string(state.messages), date=get_today_str()
                ),
            )
        ]
    )
    all_messages: list[StreamingChatMessageContent] = []
    async for response in research_model.get_streaming_chat_message_content(
        chat_history, settings
    ):
        if response is None:
            continue
        all_messages.append(response)
        yield AgentResponseItem(message=response, thread=thread)

    full_completion: StreamingChatMessageContent = reduce(
        lambda x, y: x + y, all_messages
    )
    # logger.info(
    #     f"write_research_brief_stream full_completion = \n{full_completion.model_dump_json(indent=2, exclude_none=True)}"
    # )
    logger.debug(f"write_research_brief_stream research_brief = \n{full_completion.content}")

    supervisor_messages = [
        ChatMessageContent(
            role=AuthorRole.SYSTEM,
            content=configurable.lead_researcher_prompt.format(
                date=get_today_str(),
                max_concurrent_research_units=configurable.max_concurrent_research_units,
            ),
        ),
        ChatMessageContent(role=AuthorRole.USER, content=full_completion.content),
    ]
    state.supervisor_messages = supervisor_messages
    state.research_brief = full_completion.content
    state.next_step = DeepResearcherAgentStep.RESEARCH_SUPERVISOR


async def final_report_generation_stream(
    state: DeepResearcherAgentState,
    kernel: Kernel,
    configurable: DeepResearcherAgentConfig,
    thread: AgentThread,
) -> AsyncIterable[AgentResponseItem[StreamingChatMessageContent]]:
    notes = state.notes if state.notes else []
    findings = "\n".join(notes)
    max_retries = 3
    current_retry = 0
    final_report_generation_prompt = configurable.final_report_generation_prompt
    final_report_prompt = final_report_generation_prompt.format(
        research_brief=state.research_brief,
        messages=get_buffer_string(state.messages if state.messages else []),
        findings=findings,
        date=get_today_str(),
    )
    final_report_model = kernel.get_service(
        service_id=configurable.final_report_model, type=ChatCompletionClientBase
    )
    settings = final_report_model.instantiate_prompt_execution_settings(
        model=configurable.final_report_model,
        max_tokens=configurable.final_report_model_max_tokens,
    )
    chat_history = ChatHistory(
        messages=[ChatMessageContent(role=AuthorRole.USER, content=final_report_prompt)]
    )

    while current_retry <= max_retries:
        try:
            all_messages: list[StreamingChatMessageContent] = []
            async for response in final_report_model.get_streaming_chat_message_content(
                chat_history, settings
            ):
                if response is None:
                    continue
                all_messages.append(response)
                yield AgentResponseItem(message=response, thread=thread)

            final_report = reduce(lambda x, y: x + y, all_messages)
            state.final_report = final_report.content
            state.messages = state.messages + [
                ChatMessageContent(
                    role=AuthorRole.ASSISTANT, content=state.final_report
                )
            ]
            state.next_step = DeepResearcherAgentStep.END
            return
        except Exception as e:
            if is_token_limit_exceeded(e, configurable.final_report_model):
                if current_retry == 0:
                    model_token_limit = get_model_token_limit(
                        configurable.final_report_model
                    )
                    if not model_token_limit:
                        state.final_report = f"Error generating final report: Token limit exceeded, however, we could not determine the model's maximum context length. Please update the model map in deep_researcher/utils.py with this information. {e}"
                        state.notes = []
                        state.next_step = DeepResearcherAgentStep.END
                        return
                    # If we have a model token limit, then we can reduce the findings to 4x the model's max tokens.
                    findings_token_limit = model_token_limit * 4
                else:
                    findings_token_limit = int(findings_token_limit * 0.9)
                print("Reducing the chars to", findings_token_limit)
                findings = findings[:findings_token_limit]
                current_retry += 1
            else:
                # If not a token limit exceeded error, then we just throw an error.
                state.next_step = DeepResearcherAgentStep.END
                state.final_report = f"Error generating final report: {e}"

    state.final_report = f"Error generating final report: Maximum retries exceeded"
    state.messages = state.messages + [
        ChatMessageContent(role=AuthorRole.ASSISTANT, content=final_report)
    ]
    state.next_step = DeepResearcherAgentStep.END


class DeepResearcherAgent(DeclarativeSpecMixin, Agent):
    config: DeepResearcherAgentConfig | None = None

    @classmethod
    def _get_kernel(cls, config: DeepResearcherAgentConfig) -> Kernel:
        kernel = Kernel()
        kernel.add_service(
            service=OpenAIChatCompletion(
                ai_model_id=os.getenv("OPENAI_MODEL_NAME"),
                service_id=config.research_model,
                async_client=AsyncOpenAI(
                    api_key=os.getenv("OPENAI_API_KEY"),
                    base_url=os.getenv("OPENAI_BASE_URL"),
                ),
            ),
        )
        kernel.add_function(
            plugin_name=plugin_name,
            function_name=clarify_completed_tool_name,
            function=KernelFunction.from_method(method=_clarity_completed),
        )
        kernel.add_function(
            plugin_name=plugin_name,
            function_name=research_complete_tool_name,
            function=KernelFunction.from_method(method=_research_complete),
        )
        kernel.add_function(
            plugin_name=plugin_name,
            function_name=conduct_research_tool_name,
            function=KernelFunction.from_method(method=_conduct_research),
        )
        kernel.add_function(
            plugin_name=plugin_name,
            function_name=web_search_tool_name,
            function=KernelFunction.from_method(method=_web_search_wrapper),
        )
        return kernel

    def __init__(self, config: DeepResearcherAgentConfig, kernel: Kernel | None = None):
        kernel = kernel or DeepResearcherAgent._get_kernel(config)
        super().__init__(kernel=kernel)
        self.config = config

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
        **kwargs,
    ) -> AsyncIterable[AgentResponseItem[ChatMessageContent]]:
        state = DeepResearcherAgentState(
            messages=messages, research_brief="", supervisor_messages=[]
        )

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
        **kwargs,
    ) -> AsyncIterable[AgentResponseItem[StreamingChatMessageContent]]:
        if thread is None:
            thread = ChatHistoryAgentThread()

        if isinstance(messages, (str, ChatMessageContent)):
            messages = [messages]

        normalized_messages = [
            (
                ChatMessageContent(role=AuthorRole.USER, content=msg)
                if isinstance(msg, str)
                else msg
            )
            for msg in messages
        ]

        state = DeepResearcherAgentState(
            next_step=DeepResearcherAgentStep.CLARIFY_WITH_USER,
            messages=normalized_messages,
            research_brief="",
            supervisor_messages=[],
            research_iterations=0,
        )
        step = state.next_step
        while step != DeepResearcherAgentStep.END:
            if step == DeepResearcherAgentStep.CLARIFY_WITH_USER:
                async for response in clarify_with_user_stream(
                    state, self.kernel, self.config, thread
                ):
                    yield response
            elif step == DeepResearcherAgentStep.WRITE_RESEARCH_BRIEF:
                async for response in write_research_brief_stream(
                    state, self.kernel, self.config, thread
                ):
                    yield response
            elif step == DeepResearcherAgentStep.RESEARCH_SUPERVISOR:
                await research_supervisor(state, self.kernel, self.config, thread)
            elif step == DeepResearcherAgentStep.FINAL_REPORT_GENERATION:
                async for response in final_report_generation_stream(
                    state, self.kernel, self.config, thread
                ):
                    yield response

            step = state.next_step

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
    ) -> "DeepResearcherAgent":
        # Returns the normalized spec fields and a kernel configured with plugins, if present.
        fields, kernel = cls._normalize_spec_fields(
            data, kernel=kernel, plugins=plugins, **kwargs
        )
        return cls(**fields, kernel=kernel)

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


async def main():
    import os
    import dotenv

    dotenv.load_dotenv()

    config = DeepResearcherAgentConfig()
    config.research_model = "openai:gpt-4.1"
    config.compression_model = "openai:gpt-4.1"
    agent = DeepResearcherAgent(config)
    last_message_id = None
    async for response in agent.invoke_stream(messages=["中国的首都在哪里?"]):
        # if last_message_id != response.message.id:
        #     last_message_id = response.message.id
        print(response.content, end="", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
