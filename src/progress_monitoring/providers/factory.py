"""
Factory functions for creating AI providers.
"""
from ..config import AnalysisConfig, ModelProvider
from .base import AIProvider
from .gemini_provider import GeminiProvider
from .openai_provider import OpenAIProvider


def create_ai_provider(config: AnalysisConfig) -> AIProvider:
    """Create appropriate AI provider based on configuration."""
    if config.model_provider == ModelProvider.GEMINI:
        return GeminiProvider(config)
    elif config.model_provider == ModelProvider.OPENAI:
        return OpenAIProvider(config)
    else:
        raise ValueError(f"Unsupported provider: {config.model_provider}") 