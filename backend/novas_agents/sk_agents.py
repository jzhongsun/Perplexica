import json
import logging

from typing import Any, Callable, Dict, List
from fastapi import FastAPI
from semantic_kernel.agents import Agent, ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
import os
from a2a.server.apps import A2AStarletteApplication
from a2a.types import AgentCard, AgentCapabilities, AgentProvider, AgentSkill
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from .sk_helper import SemanticKernelAgentExecutor
import yaml

logger = logging.getLogger(__name__)

PUBLIC_HOST_URL = os.getenv("PUBLIC_HOST_URL", "http://localhost:10010")

def create_sk_chat_completion_agent(agent_name: str, agent_card: AgentCard, agent_config: Dict[str, Any] = {}) -> Agent:
    chat_completion = OpenAIChatCompletion(
        api_key=os.getenv("OPENAI_API_KEY"),
        ai_model_id=os.getenv("OPENAI_MODEL_NAME"),
    )
    agent = ChatCompletionAgent(
        id=agent_name,
        name=agent_card.name,
        description=agent_card.description,
        service=chat_completion,
    )
    return agent

def setup_sk_agent_from_card(app: FastAPI, 
                             agent_name: str,
                             agent_card: AgentCard, 
                             agent_config: Dict[str, Any],
                             agent_builder: Callable[[AgentCard, Dict[str, Any]], Agent]):
    agent_card.url = PUBLIC_HOST_URL + "/" + agent_name + "/"
    request_handler = DefaultRequestHandler(
        agent_executor=SemanticKernelAgentExecutor(agent_name, agent_card, agent_config, agent_builder),
        task_store=InMemoryTaskStore(),
    )
    a2a_app = A2AStarletteApplication(
        agent_card=agent_card, http_handler=request_handler
    )
    app.mount("/" + agent_name, app=a2a_app.build(), name=agent_name)

def create_sk_agent_meta_search(agent_name: str, agent_card: AgentCard, agent_config: Dict[str, Any] = {}) -> Agent:
    from .sk_search_agent import MetaSearchAgent, MetaSearchAgentConfig
    config = MetaSearchAgentConfig(
        search_web=agent_config.get("search_web", True),
        rerank=agent_config.get("rerank", True),
        rerank_threshold=agent_config.get("rerank_threshold", 0.3),
        summarizer=agent_config.get("summarizer", False),
        query_generator_prompt=agent_config.get("query_generator_prompt", ""),
        response_prompt=agent_config.get("response_prompt", ""),
        active_engines=agent_config.get("active_engines", []),
    )
    return MetaSearchAgent(
        id=agent_name,
        # name=agent_card.name,
        # description=agent_card.description,
        config=config
    )

def create_sk_agent_stock_symbol_research(agent_name: str, agent_card: AgentCard, agent_config: Dict[str, Any] = {}) -> Agent:
    from .sk_trading_agent import FinancialTradingAgent, FinancialTradingAgentConfig
    config = FinancialTradingAgentConfig(
        deep_think_model=agent_config.get("deep_think_model", "openai:gpt-4.1"),
        quick_think_model=agent_config.get("quick_think_model", "openai:gpt-4.1"),
        mcp_server_url=agent_config.get("mcp_server_url", "http://localhost:9000/trading/sse"),
        max_debate_rounds=agent_config.get("max_debate_rounds", 1),
        max_risk_discuss_rounds=agent_config.get("max_risk_discuss_rounds", 1),
        max_recur_limit=agent_config.get("max_recur_limit", 100),
        selected_analysts=agent_config.get("selected_analysts", ["market", "news", "fundamentals"]),
        analyst_functions=agent_config.get("analyst_functions", {}),
        max_concurrent_analysts_tool_calls=agent_config.get("max_concurrent_analysts_tool_calls", 5),
    )
    return FinancialTradingAgent(config)
def build_agent_card(agent_card_config: Dict[str, Any]) -> AgentCard:
    agent_card_skills_config: List[Dict[str, Any]] = (
        agent_card_config["skills"] if "skills" in agent_card_config else []
    )
    agent_card = AgentCard(
        name=agent_card_config["name"],
        description=agent_card_config["description"],
        version=agent_card_config["version"],
        url=agent_card_config["url"] if "url" in agent_card_config else PUBLIC_HOST_URL + "/" + agent_card_config["name"],
        skills=[
            AgentSkill(
                id=skill_config["id"],
                name=skill_config["name"],
                description=skill_config["description"],
                tags=skill_config["tags"] if "tags" in skill_config else [],
                examples=(
                    skill_config["examples"] if "examples" in skill_config else None
                ),
            )
            for skill_config in agent_card_skills_config
        ] if "skills" in agent_card_config and agent_card_skills_config is not None and len(agent_card_skills_config) > 0 else [],
        capabilities=AgentCapabilities(
            streaming=True,
        ),
        defaultInputModes=["text"],
        defaultOutputModes=["text", "json"],
        provider=(
            AgentProvider(
                organization=agent_card_config["provider"]["organization"] if "organization" in agent_card_config["provider"] else "Unknown",
                url=agent_card_config["provider"]["url"] if "url" in agent_card_config["provider"] else None,
            )
            if "provider" in agent_card_config
            else None
        ),
    )
    return agent_card

def setup_sk_agent_from_config(app: FastAPI, agent_name: str, agent_config: Dict[str, Any], agent_builder: Callable[[AgentCard, Dict[str, Any]], Agent]):
    logger.info(f"Setting up agent {agent_name} \n {json.dumps(agent_config, indent=2, ensure_ascii=False)}")
    
    agent_card_config = agent_config["agent_card"]
    agent_card = build_agent_card(agent_card_config)
    logger.info(f"Building agent card: {agent_card}")
    
    inner_agent_config = agent_config["agent_config"] if "agent_config" in agent_config else {}
    setup_sk_agent_from_card(app, agent_name, agent_card, inner_agent_config, agent_builder)

def setup_sk_agents(app: FastAPI):
    # from configuration file, create a list of agents
    with open("./sk_agents.yaml", "r") as f:
        agents_config = yaml.safe_load(f)
        if "chat_completion_agents" in agents_config:
            for agent_name, agent_config in agents_config["chat_completion_agents"].items():
                setup_sk_agent_from_config(app, agent_name, agent_config, create_sk_chat_completion_agent)
        if "meta_search_agents" in agents_config:
            for agent_name, agent_config in agents_config["meta_search_agents"].items():
                setup_sk_agent_from_config(app, agent_name, agent_config, create_sk_agent_meta_search)
        if "trading_agents" in agents_config:
            for agent_name, agent_config in agents_config["trading_agents"].items():
                setup_sk_agent_from_config(app, agent_name, agent_config, create_sk_agent_stock_symbol_research)
    
