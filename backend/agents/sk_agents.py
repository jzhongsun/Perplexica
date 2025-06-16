import logging

from typing import Any, Dict, List
from fastapi import FastAPI
from semantic_kernel.agents import Agent, ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
import os
from a2a.server.apps import A2AStarletteApplication
from a2a.types import AgentCard, AgentCapabilities, AgentProvider, AgentSkill
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore, InMemoryPushNotifier
import httpx
from .sk_helper import SemanticKernelAgentExecutor
import yaml

logger = logging.getLogger(__name__)


def create_sk_agent(agent_card: AgentCard, agent_config: Dict[str, Any] = {}) -> Agent:
    chat_completion = OpenAIChatCompletion(
        api_key=os.getenv("OPENAI_API_KEY"),
        ai_model_id=os.getenv("OPENAI_MODEL_NAME"),
    )
    agent = ChatCompletionAgent(
        name=agent_card.name,
        description=agent_card.description,
        service=chat_completion,
    )
    return agent


def setup_sk_agent(app: FastAPI, agent_config: Dict[str, Any]):
    logger.info(f"Setting up agent {agent_config}")

    agent_card_config = agent_config["agent_card"]
    agent_card_skills_config: List[Dict[str, Any]] = (
        agent_card_config["skills"] if "skills" in agent_card_config else []
    )
    agent_card = AgentCard(
        name=agent_card_config["name"],
        description=agent_card_config["description"],
        version=agent_card_config["version"],
        url=agent_card_config["url"],
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
        ],
        capabilities=AgentCapabilities(
            streaming=True,
        ),
        defaultInputModes=["text"],
        defaultOutputModes=["text", "json"],
        provider=(
            AgentProvider(
                name=agent_card_config["provider"]["name"],
                version=agent_card_config["provider"]["version"],
            )
            if "provider" in agent_card_config
            else None
        ),
    )
    httpx_client = httpx.AsyncClient()
    request_handler = DefaultRequestHandler(
        agent_executor=SemanticKernelAgentExecutor(agent_card, create_sk_agent),
        task_store=InMemoryTaskStore(),
        push_notifier=InMemoryPushNotifier(httpx_client),
    )
    a2a_app = A2AStarletteApplication(
        agent_card=agent_card, http_handler=request_handler
    )
    app.mount("/" + agent_card.name, app=a2a_app.build(), name=agent_card.name)


def setup_sk_agents(app: FastAPI):
    with open("./agents.yaml", "r") as f:
        agents_config = yaml.safe_load(f)
        for agent_config in agents_config["agents"]:
            setup_sk_agent(app, agent_config)
