"""
Configuration settings for the LangGraph agent.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class AgentConfig(BaseSettings):
    """Configuration for the LangGraph agent."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="allow")

    # vLLM/LLM Configuration
    vllm_base_url: str = "http://localhost:8000/v1"
    vllm_api_key: str = "dummy-key"
    llm_model: str = "Qwen/Qwen2.5-72B-Instruct-AWQ"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 2000
    llm_timeout: int = 120

    # Agent Configuration
    max_iterations: int = 100
    max_tool_retries: int = 3
    enable_reflection: bool = True
    reflection_frequency: int = 5  # Reflect every N iterations

    # TheAgentCompany Environment
    server_hostname: str = "localhost"
    gitlab_url: Optional[str] = None
    rocketchat_url: Optional[str] = None
    owncloud_url: Optional[str] = None
    plane_url: Optional[str] = None

    # Logging
    log_level: str = "INFO"
    enable_trajectory_logging: bool = True

    def get_service_urls(self) -> dict[str, str]:
        """Get service URLs with defaults."""
        return {
            "gitlab": self.gitlab_url or f"http://{self.server_hostname}:8929",
            "rocketchat": self.rocketchat_url or f"http://{self.server_hostname}:3000",
            "owncloud": self.owncloud_url or f"http://{self.server_hostname}:8092",
            "plane": self.plane_url or f"http://{self.server_hostname}:8091",
        }


# Global config instance
config = AgentConfig()
