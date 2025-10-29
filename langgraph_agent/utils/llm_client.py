"""
LLM client utilities for vLLM integration.
"""

from langchain_openai import ChatOpenAI
from typing import Optional
from ..config import config


def get_llm_client(
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> ChatOpenAI:
    """
    Create an LLM client connected to vLLM or fallback.

    Args:
        model: Model name (defaults to config.llm_model)
        temperature: Sampling temperature (defaults to config.llm_temperature)
        max_tokens: Maximum tokens to generate (defaults to config.llm_max_tokens)

    Returns:
        ChatOpenAI: Configured LLM client
    """
    return ChatOpenAI(
        base_url=config.vllm_base_url,
        api_key=config.vllm_api_key,
        model=model or config.llm_model,
        temperature=temperature if temperature is not None else config.llm_temperature,
        max_tokens=max_tokens or config.llm_max_tokens,
        timeout=config.llm_timeout,
        max_retries=config.max_tool_retries,
    )


def get_structured_llm(schema: type, **kwargs) -> ChatOpenAI:
    """
    Create an LLM client with structured output.

    Args:
        schema: Pydantic model for structured output
        **kwargs: Additional arguments for get_llm_client

    Returns:
        ChatOpenAI with structured output binding
    """
    llm = get_llm_client(**kwargs)
    return llm.with_structured_output(schema)
