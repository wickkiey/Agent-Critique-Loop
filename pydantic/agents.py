"""Agent factory wiring pydantic-ai to a local Ollama model via the OpenAI-compatible API."""

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from config import Config
from tools import knowledge_lookup


def build_model(config: Config) -> OpenAIChatModel:
    provider = OpenAIProvider(base_url=config.base_url, api_key=config.api_key)
    return OpenAIChatModel(config.model_name, provider=provider)


def create_agent(config: Config, name: str, system_prompt: str, output_type: type) -> Agent:
    return Agent(
        build_model(config),
        output_type=output_type,
        system_prompt=system_prompt,
        name=name,
        tools=[knowledge_lookup],
    )
