import asyncio
from collections.abc import AsyncIterable, Awaitable, Callable
from functools import reduce
import logging.config
import os
import json
from agents.sk_trading_prompts import *
from agents.sk_trading_core import *
from agents.utils import (
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
    Any,
    override,
    Annotated,
    Any,
)

from semantic_kernel.connectors.ai.chat_completion_client_base import (
    ChatCompletionClientBase,
)
from semantic_kernel.connectors.ai.function_choice_behavior import (
    FunctionChoiceBehavior,
)
from semantic_kernel.contents import (
    ChatMessageContent,
    AuthorRole,
    FunctionCallContent,
    FunctionResultContent,
    TextContent,
    StreamingChatMessageContent,
    ChatHistory,
)

from semantic_kernel.utils.telemetry.agent_diagnostics.decorators import (
    trace_agent_get_response,
    trace_agent_invocation,
)
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.kernel import Kernel, KernelPlugin, KernelArguments
from semantic_kernel.functions import kernel_function, KernelFunction
from openai import AsyncOpenAI

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


class FinancialTradingAgentConfig(BaseModel):
    # Model Configuration
    deep_think_model: str = Field(default="openai:gpt-4.1", metadata={})
    deep_think_model_config: dict[str, Any] = Field(default={}, metadata={})
    quick_think_model: str = Field(default="openai:gpt-4.1", metadata={})
    quick_think_model_config: dict[str, Any] = Field(default={}, metadata={})
    max_debate_rounds: int = Field(default=1, metadata={})
    max_risk_discuss_rounds: int = Field(default=1, metadata={})
    max_recur_limit: int = Field(default=100, metadata={})
    selected_analysts: list[str] = Field(
        default=["market", "social", "news", "fundamentals"], metadata={}
    )
    max_concurrent_analysts_tool_calls: int = Field(default=1, metadata={})

    class Config:
        arbitrary_types_allowed = True


async def safe_invoke_function(
    kernel: Kernel,
    function_name: str,
    arguments: dict[str, Any],
    semaphore: asyncio.Semaphore,
):
    async with semaphore:
        function = kernel.get_function(function_name)
        try:
            return function.invoke(arguments)
        except Exception as e:
            logger.error(f"Error invoking function {function_name}: {e}")
            return None


async def async_invoke_analyst_component(
    analyst_name: str,
    state: FinancialTradingAgentState,
    kernel: Kernel,
    model_service_id: str,
    model_name: str,
    model_config: dict[str, Any],
    system_prompt: str,
    shall_continue_func: Callable[
        [FinancialTradingAgentState, ChatMessageContent], bool
    ],
    included_functions: list[str],
    included_plugins: list[str],
    function_call_semaphore: asyncio.Semaphore,
    thread: AgentThread,
    response_stream_queue: asyncio.Queue[
        AgentResponseItem[StreamingChatMessageContent]
    ],
) -> tuple[str, str, list[ChatMessageContent]]:
    model = kernel.get_service(
        service_id=model_service_id, type=ChatCompletionClientBase
    )
    settings = model.instantiate_prompt_execution_settings(
        model=model_name,
        **model_config,
    )
    function_choice_behavior = FunctionChoiceBehavior.Auto(
        auto_invoke=False,
        auto_invoke_kernel_functions=False,
        filters={
            "included_functions": included_functions,
            "included_plugins": included_plugins,
        },
    )
    settings.function_choice_behavior = function_choice_behavior
    messages = [
        ChatMessageContent(role=AuthorRole.SYSTEM, content=system_prompt),
    ] + state.messages
    chat_history = ChatHistory(messages=messages)
    while True:
        response: ChatMessageContent | None = await model.get_chat_message_content(
            chat_history, settings, kernel=kernel
        )
        if response is None:
            continue
        chat_history.add_message(message=response)
        response_stream_queue.put_nowait(
            AgentResponseItem(message=response, thread=thread)
        )
        function_call_contents: list[FunctionCallContent] = []
        report = ""
        for item in response.items:
            if isinstance(item, FunctionCallContent):
                function_call_content = item
                function_call_contents.append(function_call_content)

        if function_call_contents and len(function_call_contents) > 0:
            coroutines = []
            for function_call_content in function_call_contents:
                function_name = function_call_content.function_name
                arguments = function_call_content.parse_arguments()
                coroutines.append(
                    safe_invoke_function(
                        kernel, function_name, arguments, function_call_semaphore
                    )
                )

            results = await asyncio.gather(*coroutines)
            for result, function_call_content in zip(results, function_call_contents):
                function_result_content = (
                    FunctionResultContent.from_function_call_content_and_result(
                        function_call_content, result
                    )
                )
                function_result_message_content = (
                    function_result_content.to_chat_message_content()
                )
                chat_history.add_message(message=function_result_message_content)
                response_stream_queue.put_nowait(
                    AgentResponseItem(
                        message=function_result_message_content, thread=thread
                    )
                )
        else:
            report = response.content

        if not shall_continue_func(state, response):
            logger.info(f"Analyst {analyst_name} has finished its work")
            return analyst_name, report, chat_history.messages
        else:
            logger.info(f"Analyst {analyst_name} is continuing its work")
            continue


async def invoke_analysts_stream(
    conditional_logic: FinancialTradingConditionalLogic,
    state: FinancialTradingAgentState,
    kernel: Kernel,
    configurable: FinancialTradingAgentConfig,
    thread: AgentThread,
) -> AsyncIterable[AgentResponseItem[StreamingChatMessageContent]]:
    """
    Analysts discuss the company of interest and the trade date.
    """
    selected_analysts = configurable.selected_analysts
    analysts_pack = {
        "market": {
            "system_prompt": market_analyst_system_prompt.format(
                system_message=market_analyst_system_message,
                tool_names=[],
                current_date=get_today_str(),
                ticker=state.company_of_interest,
            ),
            "report": "",
            "service_id": "",
            "model_name": "",
            "model_config": {
                "max_tokens": 8000,
            },
            "shall_continue_func": conditional_logic.should_continue_market,
            "included_functions": [],
            "included_plugins": [],
        },
        "social": {
            "system_prompt": social_analyst_system_prompt.format(
                system_message=social_analyst_system_message,
                tool_names=[],
                current_date=get_today_str(),
                ticker=state.company_of_interest,
            ),
            "report": "",
            "service_id": "",
            "model_name": "",
            "model_config": {
                "max_tokens": 8000,
            },
            "shall_continue_func": conditional_logic.should_continue_social,
            "included_functions": [],
            "included_plugins": [],
        },
        "news": {
            "system_prompt": news_analyst_system_prompt.format(
                system_message=news_analyst_system_message,
                tool_names=[],
                current_date=get_today_str(),
                ticker=state.company_of_interest,
            ),
            "report": "",
            "service_id": "",
            "model_name": "",
            "model_config": {
                "max_tokens": 8000,
            },
            "shall_continue_func": conditional_logic.should_continue_news,
            "included_functions": [],
            "included_plugins": [],
        },
        "fundamentals": {
            "system_prompt": fundamentals_analyst_system_prompt.format(
                system_message=fundamentals_analyst_system_message,
                tool_names=[],
                current_date=get_today_str(),
                ticker=state.company_of_interest,
            ),
            "report": "",
            "service_id": "",
            "model_name": "",
            "model_config": {
                "max_tokens": 8000,
            },
            "shall_continue_func": conditional_logic.should_continue_fundamentals,
            "included_functions": [],
            "included_plugins": [],
        },
    }
    response_stream_queue = asyncio.Queue()
    function_call_semaphore = asyncio.Semaphore(
        configurable.max_concurrent_analysts_tool_calls
    )
    coroutines = []
    for analyst in selected_analysts:
        coroutines.append(
            async_invoke_analyst_component(
                analyst_name=analyst,
                state=state,
                kernel=kernel,
                model_service_id=analysts_pack[analyst]["service_id"],
                model_name=analysts_pack[analyst]["model_name"],
                model_config=analysts_pack[analyst]["model_config"],
                system_prompt=analysts_pack[analyst]["system_prompt"],
                shall_continue_func=analysts_pack[analyst]["shall_continue_func"],
                included_functions=analysts_pack[analyst]["included_functions"],
                included_plugins=analysts_pack[analyst]["included_plugins"],
                function_call_semaphore=function_call_semaphore,
                thread=thread,
                response_stream_queue=response_stream_queue,
            )
        )

    async def run_coroutines():
        try:
            results = await asyncio.gather(*coroutines)
            # Signal completion by putting a sentinel value
            await response_stream_queue.put(None)
            return results
        except Exception as e:
            logger.error(f"Error in run_coroutines: {e}")
            await response_stream_queue.put(None)
            raise

    # Start background task
    background_task = asyncio.create_task(run_coroutines())

    # Consume messages from queue until completion
    while True:
        try:
            # Use get() instead of get_nowait() to properly wait for messages
            response = await response_stream_queue.get()
            if response is None:
                # Sentinel value indicates completion
                break
            yield response
        except asyncio.CancelledError:
            # If cancelled, cancel the background task too
            background_task.cancel()
            raise
        except Exception as e:
            logger.error(f"Error consuming from queue: {e}")
            break

    # Wait for background task to complete and get results
    try:
        results = await background_task
    except asyncio.CancelledError:
        logger.info("Background task was cancelled")
        return
    except Exception as e:
        logger.error(f"Background task failed: {e}")
        return

    # Process results
    for analyst_name, report, messages in results:
        if analyst_name == "market":
            state.market_report = report
        elif analyst_name == "social":
            state.sentiment_report = report
        elif analyst_name == "news":
            state.news_report = report
        elif analyst_name == "fundamentals":
            state.fundamentals_report = report
        else:
            logger.error(f"Unknown analyst name: {analyst_name}")

    state.next_step = FinancialTradingAgentStep.RESEARCHERS
    # state.messages = state.messages + [msg for _, _, msgs in results for msg in msgs]


async def invoke_researchers_stream(
    conditional_logic: FinancialTradingConditionalLogic,
    bull_memory: FinancialSituationMemory,
    bear_memory: FinancialSituationMemory,
    invest_judge_memory: FinancialSituationMemory,
    state: FinancialTradingAgentState,
    kernel: Kernel,
    configurable: FinancialTradingAgentConfig,
    thread: AgentThread,
) -> AsyncIterable[AgentResponseItem[StreamingChatMessageContent]]:
    deep_think_model = kernel.get_service(
        service_id=configurable.deep_think_model, type=ChatCompletionClientBase
    )
    bull_model = deep_think_model
    bear_model = deep_think_model
    invest_judge_model = deep_think_model

    settings = deep_think_model.instantiate_prompt_execution_settings(
        model=configurable.deep_think_model,
        **configurable.deep_think_model_config,
    )
    bull_model_settings = deep_think_model.instantiate_prompt_execution_settings(
        model=configurable.deep_think_model,
        **configurable.deep_think_model_config,
    )
    bear_model_settings = deep_think_model.instantiate_prompt_execution_settings(
        model=configurable.deep_think_model,
        **configurable.deep_think_model_config,
    )
    invest_judge_model_settings = (
        deep_think_model.instantiate_prompt_execution_settings(
            model=configurable.deep_think_model,
            **configurable.deep_think_model_config,
        )
    )

    debate_state = FinancialTradingInvestDebateState(
        bull_history="",
        bear_history="",
        history="",
        current_response="",
        judge_decision="",
        count=0,
    )
    market_research_report = state.market_report
    sentiment_report = state.sentiment_report
    news_report = state.news_report
    fundamentals_report = state.fundamentals_report
    curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}"

    past_bull_memories = bull_memory.get_memories(curr_situation, n_matches=2)
    past_bear_memories = bear_memory.get_memories(curr_situation, n_matches=2)
    past_bull_memory_str = ""
    for i, rec in enumerate(past_bull_memories, 1):
        past_bull_memory_str += rec["recommendation"] + "\n\n"
    past_bear_memory_str = ""
    for i, rec in enumerate(past_bear_memories, 1):
        past_bear_memory_str += rec["recommendation"] + "\n\n"

    for i in range(configurable.max_debate_rounds):
        # Bull Researcher
        bull_prompt = bull_researcher_system_prompt.format(
            market_research_report=market_research_report,
            sentiment_report=sentiment_report,
            news_report=news_report,
            fundamentals_report=fundamentals_report,
            history=debate_state.history,
            current_response=debate_state.current_response,
            past_memory_str=past_bull_memory_str,
        )
        response = await bull_model.get_chat_message_content(
            ChatHistory(
                messages=[ChatMessageContent(role=AuthorRole.USER, content=bull_prompt)]
            ),
            bull_model_settings,
            kernel=kernel,
        )
        if response is None:
            continue

        yield AgentResponseItem(message=response, thread=thread)
        argument = f"Bull Analyst: {response.content}"
        debate_state.bull_history += argument
        debate_state.history += argument
        debate_state.current_response = argument

        # Bear Researcher
        bear_prompt = bear_researcher_system_prompt.format(
            market_research_report=market_research_report,
            sentiment_report=sentiment_report,
            news_report=news_report,
            fundamentals_report=fundamentals_report,
            history=debate_state.history,
            current_response=debate_state.current_response,
            past_memory_str=past_bear_memory_str,
        )
        response = await bear_model.get_chat_message_content(
            ChatHistory(
                messages=[ChatMessageContent(role=AuthorRole.USER, content=bear_prompt)]
            ),
            bear_model_settings,
            kernel=kernel,
        )
        if response is None:
            continue

        yield AgentResponseItem(message=response, thread=thread)
        argument = f"Bear Analyst: {response.content}"
        debate_state.bear_history += argument
        debate_state.history += argument
        debate_state.current_response = argument

        debate_state.count += 1
        if not conditional_logic.should_continue_debate(state, debate_state):
            break

    past_memories = invest_judge_memory.get_memories(curr_situation, n_matches=2)

    past_memory_str = ""
    for i, rec in enumerate(past_memories, 1):
        past_memory_str += rec["recommendation"] + "\n\n"

    research_manager_prompt = researcher_manager_system_prompt.format(
        history=debate_state.history,
        past_memory_str=past_memory_str,
    )
    response = await invest_judge_model.get_chat_message_content(
        ChatHistory(
            messages=[
                ChatMessageContent(
                    role=AuthorRole.USER, content=research_manager_prompt
                )
            ]
        ),
        invest_judge_model_settings,
        kernel=kernel,
    )
    if response is None:
        raise Exception("Invest Judge Model returned None")

    yield AgentResponseItem(message=response, thread=thread)
    debate_state.judge_decision = response.content
    debate_state.current_response = response.content

    state.investment_debate_state = debate_state
    state.analyst_investment_plan = response.content
    state.next_step = FinancialTradingAgentStep.TRADER


async def invoke_trader_stream(
    trader_memory: FinancialSituationMemory,
    state: FinancialTradingAgentState,
    kernel: Kernel,
    configurable: FinancialTradingAgentConfig,
    thread: AgentThread,
) -> AsyncIterable[AgentResponseItem[StreamingChatMessageContent]]:
    company_name = state.company_of_interest
    analyst_investment_plan = state.analyst_investment_plan
    market_research_report = state.market_report
    sentiment_report = state.sentiment_report
    news_report = state.news_report
    fundamentals_report = state.fundamentals_report

    curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}"
    past_memories = trader_memory.get_memories(curr_situation, n_matches=2)

    past_memory_str = ""
    if past_memories:
        for i, rec in enumerate(past_memories, 1):
            past_memory_str += rec["recommendation"] + "\n\n"
    else:
        past_memory_str = "No past memories found."

    trader_system_message = trader_system_prompt.format(
        company_name=company_name,
        investment_plan=analyst_investment_plan,
        past_memory_str=past_memory_str,
    )
    trader_user_message = trader_user_prompt.format(
        company_name=company_name,
        investment_plan=analyst_investment_plan,
        past_memory_str=past_memory_str,
    )

    trader_model = kernel.get_service(
        service_id=configurable.deep_think_model, type=ChatCompletionClientBase
    )
    trader_model_settings = trader_model.instantiate_prompt_execution_settings(
        model=configurable.deep_think_model,
        **configurable.deep_think_model_config,
    )

    response = await trader_model.get_chat_message_content(
        ChatHistory(
            messages=[
                ChatMessageContent(
                    role=AuthorRole.SYSTEM, content=trader_system_message
                ),
                ChatMessageContent(role=AuthorRole.USER, content=trader_user_message),
            ]
        ),
        trader_model_settings,
        kernel=kernel,
    )
    if response is None:
        raise Exception("Trader Model returned None")

    yield AgentResponseItem(message=response, thread=thread)
    state.messages = state.messages + [response]
    state.trader_investment_plan = response.content
    state.next_step = FinancialTradingAgentStep.RISK_ANALYSIS


async def invoke_risk_analysis_stream(
    conditional_logic: FinancialTradingConditionalLogic,
    risk_manager_memory: FinancialSituationMemory,
    state: FinancialTradingAgentState,
    kernel: Kernel,
    configurable: FinancialTradingAgentConfig,
    thread: AgentThread,
) -> AsyncIterable[AgentResponseItem[StreamingChatMessageContent]]:
    market_research_report = state.market_report
    sentiment_report = state.sentiment_report
    news_report = state.news_report
    fundamentals_report = state.fundamentals_report
    trader_decision = state.trader_investment_plan

    risk_debate_state = FinancialTradingRiskDebateState(
        risky_history="",
        safe_history="",
        neutral_history="",
        history="",
        latest_speaker="",
        current_risky_response="",
        current_safe_response="",
        current_neutral_response="",
        judge_decision="",
        count=0,
    )
    state.risk_debate_state = risk_debate_state

    risky_model = kernel.get_service(
        service_id=configurable.deep_think_model, type=ChatCompletionClientBase
    )
    risky_model_settings = risky_model.instantiate_prompt_execution_settings(
        model=configurable.deep_think_model,
        **configurable.deep_think_model_config,
    )
    safe_model = kernel.get_service(
        service_id=configurable.deep_think_model, type=ChatCompletionClientBase
    )
    safe_model_settings = safe_model.instantiate_prompt_execution_settings(
        model=configurable.deep_think_model,
        **configurable.deep_think_model_config,
    )
    neutral_model = kernel.get_service(
        service_id=configurable.deep_think_model, type=ChatCompletionClientBase
    )
    neutral_model_settings = neutral_model.instantiate_prompt_execution_settings(
        model=configurable.deep_think_model,
        **configurable.deep_think_model_config,
    )
    risk_judge_model = kernel.get_service(
        service_id=configurable.deep_think_model, type=ChatCompletionClientBase
    )
    risk_judge_model_settings = risk_judge_model.instantiate_prompt_execution_settings(
        model=configurable.deep_think_model,
        **configurable.deep_think_model_config,
    )

    while True:
        # Risky Debator
        risky_prompt = risky_debator_user_prompt.format(
            market_research_report=market_research_report,
            sentiment_report=sentiment_report,
            news_report=news_report,
            fundamentals_report=fundamentals_report,
            trader_decision=trader_decision,
            history=risk_debate_state.history,
            current_risky_response=risk_debate_state.current_risky_response,
            current_safe_response=risk_debate_state.current_safe_response,
            current_neutral_response=risk_debate_state.current_neutral_response,
        )
        response = await risky_model.get_chat_message_content(
            ChatHistory(
                messages=[
                    ChatMessageContent(role=AuthorRole.USER, content=risky_prompt)
                ]
            ),
            risky_model_settings,
            kernel=kernel,
        )
        if response is None:
            continue

        yield AgentResponseItem(message=response, thread=thread)
        argument = f"Risky Analyst: {response.content}"
        risk_debate_state.risky_history += argument
        risk_debate_state.history += argument
        risk_debate_state.current_risky_response = argument
        risk_debate_state.latest_speaker = "Risky Analyst"
        risk_debate_state.count += 1
        if not conditional_logic.should_continue_risk_analysis(
            state, risk_debate_state
        ):
            break

        # Safe Debator
        safe_prompt = safe_debator_user_prompt.format(
            market_research_report=market_research_report,
            sentiment_report=sentiment_report,
            news_report=news_report,
            fundamentals_report=fundamentals_report,
            trader_decision=trader_decision,
            history=risk_debate_state.history,
            current_risky_response=risk_debate_state.current_risky_response,
            current_safe_response=risk_debate_state.current_safe_response,
            current_neutral_response=risk_debate_state.current_neutral_response,
        )
        response = await safe_model.get_chat_message_content(
            ChatHistory(
                messages=[ChatMessageContent(role=AuthorRole.USER, content=safe_prompt)]
            ),
            safe_model_settings,
            kernel=kernel,
        )
        if response is None:
            continue

        yield AgentResponseItem(message=response, thread=thread)
        argument = f"Safe Analyst: {response.content}"
        risk_debate_state.safe_history += argument
        risk_debate_state.history += argument
        risk_debate_state.current_safe_response = argument
        risk_debate_state.latest_speaker = "Safe Analyst"
        risk_debate_state.count += 1
        if not conditional_logic.should_continue_risk_analysis(
            state, risk_debate_state
        ):
            break

        # Neutral Debator
        neutral_prompt = neutral_debator_user_prompt.format(
            market_research_report=market_research_report,
            sentiment_report=sentiment_report,
            news_report=news_report,
            fundamentals_report=fundamentals_report,
            trader_decision=trader_decision,
            history=risk_debate_state.history,
            current_risky_response=risk_debate_state.current_risky_response,
            current_safe_response=risk_debate_state.current_safe_response,
            current_neutral_response=risk_debate_state.current_neutral_response,
        )
        response = await neutral_model.get_chat_message_content(
            ChatHistory(
                messages=[
                    ChatMessageContent(role=AuthorRole.USER, content=neutral_prompt)
                ]
            ),
            neutral_model_settings,
            kernel=kernel,
        )
        if response is None:
            continue

        yield AgentResponseItem(message=response, thread=thread)
        argument = f"Neutral Analyst: {response.content}"
        risk_debate_state.neutral_history += argument
        risk_debate_state.history += argument
        risk_debate_state.current_neutral_response = argument
        risk_debate_state.latest_speaker = "Neutral Analyst"

        risk_debate_state.count += 1
        if not conditional_logic.should_continue_risk_analysis(
            state, risk_debate_state
        ):
            break

    curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}"
    past_memories = risk_manager_memory.get_memories(curr_situation, n_matches=2)
    past_memory_str = ""
    if past_memories:
        for i, rec in enumerate(past_memories, 1):
            past_memory_str += rec["recommendation"] + "\n\n"
    else:
        past_memory_str = "No past memories found."

    risk_judge_prompt = risk_judge_user_prompt.format(
        history=risk_debate_state.history,
        trader_plan=trader_decision,
        past_memory_str=past_memory_str,
    )
    response = await risk_judge_model.get_chat_message_content(
        ChatHistory(
            messages=[
                ChatMessageContent(role=AuthorRole.USER, content=risk_judge_prompt)
            ]
        ),
        risk_judge_model_settings,
        kernel=kernel,
    )
    if response is None:
        raise Exception("Risk Judge Model returned None")

    yield AgentResponseItem(message=response, thread=thread)
    risk_debate_state.judge_decision = response.content

    state.risk_debate_state = risk_debate_state
    state.final_trade_decision = risk_debate_state.judge_decision
    state.next_step = FinancialTradingAgentStep.END


class FinancialTradingAgent(DeclarativeSpecMixin, Agent):
    config: FinancialTradingAgentConfig | None = None

    @classmethod
    def _get_kernel(cls, config: FinancialTradingAgentConfig) -> Kernel:
        kernel = Kernel()
        kernel.add_service(
            service=OpenAIChatCompletion(
                ai_model_id=os.getenv("OPENAI_MODEL_NAME"),
                service_id=config.deep_think_model,
                async_client=AsyncOpenAI(
                    api_key=os.getenv("OPENAI_API_KEY"),
                    base_url=os.getenv("OPENAI_BASE_URL"),
                ),
            ),
        )
        # kernel.add_function(
        #     plugin_name=plugin_name,
        #     function_name=clarify_completed_tool_name,
        #     function=KernelFunction.from_method(method=_clarity_completed),
        # )
        return kernel

    def __init__(
        self, config: FinancialTradingAgentConfig, kernel: Kernel | None = None
    ):
        kernel = kernel or FinancialTradingAgent._get_kernel(config)
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
        state = FinancialTradingAgentState(
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

        # Initialize memories
        bull_memory = FinancialSituationMemory("bull_memory", self.config)
        bear_memory = FinancialSituationMemory("bear_memory", self.config)
        trader_memory = FinancialSituationMemory("trader_memory", self.config)
        invest_judge_memory = FinancialSituationMemory(
            "invest_judge_memory", self.config
        )
        risk_manager_memory = FinancialSituationMemory(
            "risk_manager_memory", self.config
        )
        # Initialize components
        conditional_logic = FinancialTradingConditionalLogic(
            max_debate_rounds=self.config.max_debate_rounds,
            max_risk_discuss_rounds=self.config.max_risk_discuss_rounds,
        )
        # reflector = FinancialTradingReflector()
        # signal_processor = FinancialTradingSignalProcessor(self.kernel)
        # self.propagator = FinancialTradingPropagator(self.kernel)
        # reflector = FinancialTradingReflector(self.kernel)
        # signal_processor = FinancialTradingSignalProcessor(self.kernel)

        state = FinancialTradingAgentState(
            next_step=FinancialTradingAgentStep.ANALYSTS,
            messages=normalized_messages,
            research_brief="",
            supervisor_messages=[],
            research_iterations=0,
        )
        step = state.next_step
        seq = 0
        self.log_state(state, seq)
        while step != FinancialTradingAgentStep.END:
            if step == FinancialTradingAgentStep.ANALYSTS:
                async for response in invoke_analysts_stream(
                    conditional_logic, state, self.kernel, self.config, thread
                ):
                    yield response
            elif step == FinancialTradingAgentStep.RESEARCHERS:
                async for response in invoke_researchers_stream(
                    conditional_logic,
                    bull_memory,
                    bear_memory,
                    invest_judge_memory,
                    state,
                    self.kernel,
                    self.config,
                    thread,
                ):
                    yield response
            elif step == FinancialTradingAgentStep.TRADER:
                async for response in invoke_trader_stream(
                    trader_memory, state, self.kernel, self.config, thread
                ):
                    yield response
            elif step == FinancialTradingAgentStep.RISK_ANALYSIS:
                async for response in invoke_risk_analysis_stream(
                    conditional_logic,
                    risk_manager_memory,
                    state,
                    self.kernel,
                    self.config,
                    thread,
                ):
                    yield response

            step = state.next_step
            seq += 1
            self.log_state(state, seq)

    def log_state(self, state: FinancialTradingAgentState, seq: int):
        os.makedirs("trading_logs", exist_ok=True)
        with open(f"trading_logs/state_{seq}.json", "w") as f:
            json.dump(state.model_dump(mode="json"), f, indent=2, ensure_ascii=False)

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
    ) -> "FinancialTradingAgent":
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

    config = FinancialTradingAgentConfig()
    config.deep_think_model = "openai:gpt-4.1"
    config.quick_think_model = "openai:gpt-4.1"
    agent = FinancialTradingAgent(config)
    last_message_id = None
    async for response in agent.invoke_stream(
        messages=[
            f'```json\n{{"company_of_interest": "AAPL", "trade_date": "2025-01-01"}}\n```'
        ]
    ):
        # if last_message_id != response.message.id:
        #     last_message_id = response.message.id
        print(response.content, end="", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
