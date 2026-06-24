import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class OrchestratorConfig:
    public_base_url: str
    ollama_base_url: str


def require_env(name: str) -> str:
    value = os.environ.get(name)

    if not value:
        raise RuntimeError(f'Missing required environment variable: {name}')

    return value


def load_config() -> OrchestratorConfig:
    return OrchestratorConfig(
        public_base_url=require_env('ORCHESTRATOR_PUBLIC_BASE_URL'),
        ollama_base_url=require_env('ORCHESTRATOR_OLLAMA_BASE_URL'),
    )
