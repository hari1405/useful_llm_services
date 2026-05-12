"""
LLM Provider abstraction for Decision Council.

Supports:
  - Anthropic (Claude models) — via anthropic SDK
  - OpenAI (GPT models)       — via openai SDK
  - Gemini                    — via official google-genai SDK
  - Custom                    — any OpenAI-compatible base URL

Usage:
    provider = get_provider("anthropic", api_key="sk-ant-...")
    text, tokens = provider.complete(system="...", user="...", model="...", max_tokens=1024)
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


# ── Provider names ─────────────────────────────────────────────────────────────

PROVIDER_ANTHROPIC = "anthropic"
PROVIDER_OPENAI    = "openai"
PROVIDER_GEMINI    = "gemini"
PROVIDER_CUSTOM    = "custom"

ALL_PROVIDERS = [PROVIDER_ANTHROPIC, PROVIDER_OPENAI, PROVIDER_GEMINI, PROVIDER_CUSTOM]

# Default models per provider
DEFAULT_MODELS = {
    PROVIDER_ANTHROPIC: "claude-haiku-4-5-20251001",
    PROVIDER_OPENAI:    "gpt-4o-mini",
    PROVIDER_GEMINI:    "gemini-3.1-flash-lite",
    PROVIDER_CUSTOM:    "gpt-4o-mini",
}

# ── Result type ────────────────────────────────────────────────────────────────

@dataclass
class CompletionResult:
    text: str
    tokens_used: int


# ── Base class ─────────────────────────────────────────────────────────────────

class LLMProvider(ABC):
    """Abstract base for all LLM providers."""

    name: str  # subclasses set this

    @abstractmethod
    def complete(
        self,
        *,
        system: str,
        user: str,
        model: str,
        max_tokens: int = 1024,
    ) -> CompletionResult:
        """
        Send a completion request and return (text, tokens_used).
        All providers must implement this method.
        """
        ...

    def default_model(self) -> str:
        return DEFAULT_MODELS.get(self.name, "gpt-4o-mini")


# ── Anthropic ──────────────────────────────────────────────────────────────────

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


# ── OpenAI ─────────────────────────────────────────────────────────────────────

class OpenAIProvider(LLMProvider):
    """Uses the OpenAI SDK (Chat Completions API)."""

    name = PROVIDER_OPENAI

    def __init__(self, api_key: str, base_url: Optional[str] = None):
        import openai as _openai
        kwargs = {"api_key": api_key}
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


# ── Gemini (via official google-genai SDK) ─────────────────────────────────────

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


# ── Custom (any OpenAI-compatible endpoint) ────────────────────────────────────

class CustomProvider(LLMProvider):
    """
    Connects to any OpenAI-compatible API endpoint.
    Requires CUSTOM_BASE_URL and CUSTOM_API_KEY environment variables
    (or passed directly).
    """

    name = PROVIDER_CUSTOM

    def __init__(self, api_key: str, base_url: str):
        import openai as _openai
        self.client = _openai.OpenAI(
            api_key=api_key,
            base_url=base_url,
        )

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


# ── Factory ────────────────────────────────────────────────────────────────────

def get_provider(
    provider_name: str,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> LLMProvider:
    """
    Instantiate the correct provider from a name string.

    Env var fallbacks:
      anthropic → ANTHROPIC_API_KEY
      openai    → OPENAI_API_KEY
      gemini    → GOOGLE_API_KEY
      custom    → CUSTOM_API_KEY + CUSTOM_BASE_URL

    Args:
        provider_name: one of "anthropic", "openai", "gemini", "custom"
        api_key:       override the env var (optional)
        base_url:      required for "custom", ignored for others
    """
    name = provider_name.lower().strip()

    if name == PROVIDER_ANTHROPIC:
        key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        if not key:
            raise ValueError(
                "Anthropic API key required.\n"
                "Set ANTHROPIC_API_KEY or pass --api-key.\n"
                "Get yours at: https://console.anthropic.com/"
            )
        return AnthropicProvider(api_key=key)

    elif name == PROVIDER_OPENAI:
        key = api_key or os.environ.get("OPENAI_API_KEY", "")
        if not key:
            raise ValueError(
                "OpenAI API key required.\n"
                "Set OPENAI_API_KEY or pass --api-key.\n"
                "Get yours at: https://platform.openai.com/api-keys"
            )
        return OpenAIProvider(api_key=key)

    elif name == PROVIDER_GEMINI:
        key = api_key or os.environ.get("GOOGLE_API_KEY", "")
        if not key:
            raise ValueError(
                "Google API key required.\n"
                "Set GOOGLE_API_KEY or pass --api-key.\n"
                "Get yours at: https://aistudio.google.com/app/apikey"
            )
        return GeminiProvider(api_key=key)

    elif name == PROVIDER_CUSTOM:
        key = api_key or os.environ.get("CUSTOM_API_KEY", "")
        url = base_url or os.environ.get("CUSTOM_BASE_URL", "")
        if not key:
            raise ValueError(
                "Custom provider API key required.\n"
                "Set CUSTOM_API_KEY or pass --api-key."
            )
        if not url:
            raise ValueError(
                "Custom provider base URL required.\n"
                "Set CUSTOM_BASE_URL or pass --base-url."
            )
        return CustomProvider(api_key=key, base_url=url)

    else:
        raise ValueError(
            f"Unknown provider: '{provider_name}'.\n"
            f"Choose from: {', '.join(ALL_PROVIDERS)}"
        )


def env_var_for_provider(provider_name: str) -> str:
    """Return the expected env var name for a given provider."""
    mapping = {
        PROVIDER_ANTHROPIC: "ANTHROPIC_API_KEY",
        PROVIDER_OPENAI:    "OPENAI_API_KEY",
        PROVIDER_GEMINI:    "GOOGLE_API_KEY",
        PROVIDER_CUSTOM:    "CUSTOM_API_KEY",
    }
    return mapping.get(provider_name.lower(), "API_KEY")
