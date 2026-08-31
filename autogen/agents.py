"""Agent factory wiring AutoGen AgentChat to a local Ollama model via the OpenAI-compatible API."""

from autogen_agentchat.agents import AssistantAgent
from autogen_core.tools import FunctionTool
from autogen_ext.models.openai import OpenAIChatCompletionClient

from config import Config
from tools import file_search, web_search

# strict=True is required because structured (output_content_type) responses are auto-parsed by the OpenAI SDK
WEB_SEARCH_TOOL = FunctionTool(web_search, description="Search the web (DuckDuckGo, free) for a query.", strict=True)
FILE_SEARCH_TOOL = FunctionTool(file_search, description="Search project files for lines matching a query.", strict=True)


def build_model_client(config: Config) -> OpenAIChatCompletionClient:
    return OpenAIChatCompletionClient(
        model=config.model_name,
        base_url=config.base_url,
        api_key=config.api_key,
        # qwen3 is not in autogen's known-model registry, so capabilities must be declared explicitly.
        model_info={
            "vision": False,
            "function_calling": True,
            "json_output": True,
            "structured_output": True,
            "family": "unknown",
        },
    )


def create_agent(
    model_client: OpenAIChatCompletionClient,
    name: str,
    system_message: str,
    output_content_type: type,
    with_tools: bool = False,
) -> AssistantAgent:
    return AssistantAgent(
        name=name,
        model_client=model_client,
        system_message=system_message,
        tools=[WEB_SEARCH_TOOL, FILE_SEARCH_TOOL] if with_tools else None,
        output_content_type=output_content_type,
        reflect_on_tool_use=True,
    )
