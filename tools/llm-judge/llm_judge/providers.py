"""
LLM Provider abstraction for llm-judge.

Supports:
  - Anthropic (Claude models) — via anthropic SDK
  - OpenAI (GPT models)       — via openai SDK
  - Gemini                    — via official google-genai SDK
  - Custom                    — any OpenAI-compatible base URL

Usage:
    provider = get_provider("gemini", api_key="AIza...")
    result = provider.complete(system="...", user="...", model="...", max_tokens=512)
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


PROVIDER_ANTHROPIC = "anthropic"
PROVIDER_OPENAI    = "openai"
PROVIDER_GEMINI    = "gemini"
PROVIDER_CUSTOM    = "custom"

ALL_PROVIDERS = [PROVIDER_ANTHROPIC, PROVIDER_OPENAI, PROVIDER_GEMINI, PROVIDER_CUSTOM]

DEFAULT_MODELS = {
    PROVIDER_ANTHROPIC: "claude-haiku-4-5-20251001",
    PROVIDER_OPENAI:    "gpt-4o-mini",
    PROVIDER_GEMINI:    "gemini-3.1-flash-lite",
    PROVIDER_CUSTOM:    "gpt-4o-mini",
}


@dataclass
class CompletionResult:
    text: str
    tokens_used: int


class LLMProvider(ABC):
    """Abstract base for all LLM providers."""

    name: str

    @abstractmethod
    def complete(
        self,
        *,
        system: str,
        user: str,
        model: str,
        max_tokens: int = 1024,
    ) -> CompletionResult:
        """Send a completion request and return text + token count."""
        ...

    def default_model(self) -> str:
        return DEFAULT_MODELS.get(self.name, "gpt-4o-mini")


class AnthropicProvider(LLMProvider):
    """Uses the official Anthropic SDK (Messages API)."""

    name = PROVIDER_ANTHROPIC

    def __init__(self, api_key: str):
        import anthropic as _anthropic
        self.client = _anthropic.Anthropic(api_key=api_key)

    def complete(self, *, system: str, user: str, model: str, max_tokens: int = 1024) -> CompletionResult:
        response = self.client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        text = response.content[0].text
        tokens = response.usage.input_tokens + response.usage.output_tokens
        return CompletionResult(text=text, tokens_used=tokens)


class OpenAIProvider(LLMProvider):
    """Uses the OpenAI SDK (Chat Completions API)."""

    name = PROVIDER_OPENAI

    def __init__(self, api_key: str, base_url: Optional[str] = None):
        import openai as _openai
        kwargs: dict = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        self.client = _openai.OpenAI(**kwargs)

    def complete(self, *, system: str, user: str, model: str, max_tokens: int = 1024) -> CompletionResult:
        response = self.client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        text = response.choices[0].message.content
        usage = response.usage
        tokens = (usage.prompt_tokens + usage.completion_tokens) if usage else 0
        return CompletionResult(text=text, tokens_used=tokens)


class GeminiProvider(LLMProvider):
    """Uses the official Google GenAI SDK. Requires GOOGLE_API_KEY."""

    name = PROVIDER_GEMINI

    def __init__(self, api_key: str):
        from google import genai as _genai
        self.client = _genai.Client(api_key=api_key)

    def complete(self, *, system: str, user: str, model: str, max_tokens: int = 1024) -> CompletionResult:
        from google.genai import types as _types
        response = self.client.models.generate_content(
            model=model,
            contents=user,
            config=_types.GenerateContentConfig(
                system_instruction=system,
                max_output_tokens=max_tokens,
            ),
        )
        text = response.text
        tokens = response.usage_metadata.total_token_count if response.usage_metadata else 0
        return CompletionResult(text=text, tokens_used=tokens)


class CustomProvider(LLMProvider):
    """Connects to any OpenAI-compatible API endpoint."""

    name = PROVIDER_CUSTOM

    def __init__(self, api_key: str, base_url: str):
        import openai as _openai
        self.client = _openai.OpenAI(api_key=api_key, base_url=base_url)

    def complete(self, *, system: str, user: str, model: str, max_tokens: int = 1024) -> CompletionResult:
        response = self.client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        text = response.choices[0].message.content
        usage = response.usage
        tokens = (usage.prompt_tokens + usage.completion_tokens) if usage else 0
        return CompletionResult(text=text, tokens_used=tokens)


def get_provider(
    provider_name: str,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> LLMProvider:
    """Instantiate the correct provider from a name string."""
    name = provider_name.lower().strip()

    if name == PROVIDER_ANTHROPIC:
        key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        if not key:
            raise ValueError(
                "Anthropic API key required.\n"
                "Set ANTHROPIC_API_KEY or pass --model-key / --judge-key.\n"
                "Get yours at: https://console.anthropic.com/"
            )
        return AnthropicProvider(api_key=key)

    elif name == PROVIDER_OPENAI:
        key = api_key or os.environ.get("OPENAI_API_KEY", "")
        if not key:
            raise ValueError(
                "OpenAI API key required.\n"
                "Set OPENAI_API_KEY or pass --model-key / --judge-key.\n"
                "Get yours at: https://platform.openai.com/api-keys"
            )
        return OpenAIProvider(api_key=key)

    elif name == PROVIDER_GEMINI:
        key = api_key or os.environ.get("GOOGLE_API_KEY", "")
        if not key:
            raise ValueError(
                "Google API key required.\n"
                "Set GOOGLE_API_KEY or pass --model-key / --judge-key.\n"
                "Get yours at: https://aistudio.google.com/app/apikey"
            )
        return GeminiProvider(api_key=key)

    elif name == PROVIDER_CUSTOM:
        key = api_key or os.environ.get("CUSTOM_API_KEY", "")
        url = base_url or os.environ.get("CUSTOM_BASE_URL", "")
        if not key:
            raise ValueError("Custom provider API key required.\nSet CUSTOM_API_KEY or pass --model-key.")
        if not url:
            raise ValueError("Custom provider base URL required.\nSet CUSTOM_BASE_URL or pass --base-url.")
        return CustomProvider(api_key=key, base_url=url)

    else:
        raise ValueError(f"Unknown provider: '{provider_name}'.\nChoose from: {', '.join(ALL_PROVIDERS)}")


def env_var_for_provider(provider_name: str) -> str:
    """Return the expected env var name for a given provider."""
    mapping = {
        PROVIDER_ANTHROPIC: "ANTHROPIC_API_KEY",
        PROVIDER_OPENAI:    "OPENAI_API_KEY",
        PROVIDER_GEMINI:    "GOOGLE_API_KEY",
        PROVIDER_CUSTOM:    "CUSTOM_API_KEY",
    }
    return mapping.get(provider_name.lower(), "API_KEY")
