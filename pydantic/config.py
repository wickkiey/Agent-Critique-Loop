"""Runtime configuration for the pydantic-ai critique loop."""

from pydantic import BaseModel


class Config(BaseModel):
    model_name: str = "qwen3:8b"
    base_url: str = "http://localhost:11434/v1"
    api_key: str = "ollama"  # Ollama ignores the key but the OpenAI SDK requires one
    max_iterations: int = 3
    agreement_threshold: float = 0.8
    timeout_seconds: float = 120.0
    token_budget: int = 8000
