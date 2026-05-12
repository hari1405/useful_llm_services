"""Decision Council — stress-test your decisions before the room does."""

from .council import CouncilSession, DecisionCouncil, PersonaResponse
from .personas import DEFAULT_PERSONAS, Persona, build_custom_persona, get_persona
from .providers import (
    ALL_PROVIDERS,
    DEFAULT_MODELS,
    LLMProvider,
    AnthropicProvider,
    OpenAIProvider,
    GeminiProvider,
    CustomProvider,
    CompletionResult,
    PROVIDER_ANTHROPIC,
    PROVIDER_OPENAI,
    PROVIDER_GEMINI,
    PROVIDER_CUSTOM,
    get_provider,
    env_var_for_provider,
)

__version__ = "0.2.0"
__all__ = [
    # Core
    "DecisionCouncil",
    "CouncilSession",
    "PersonaResponse",
    "Persona",
    "DEFAULT_PERSONAS",
    "get_persona",
    "build_custom_persona",
    # Provider API — abstract
    "LLMProvider",
    "CompletionResult",
    "get_provider",
    "ALL_PROVIDERS",
    "DEFAULT_MODELS",
    # Provider names (constants)
    "PROVIDER_ANTHROPIC",
    "PROVIDER_OPENAI",
    "PROVIDER_GEMINI",
    "PROVIDER_CUSTOM",
    # Provider classes (for subclassing / direct use)
    "AnthropicProvider",
    "OpenAIProvider",
    "GeminiProvider",
    "CustomProvider",
    # Provider utilities
    "env_var_for_provider",
]
