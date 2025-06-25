"""
Configuration module for construction progress monitoring.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ModelProvider(Enum):
    """Supported AI model providers."""
    GEMINI = "gemini"
    OPENAI = "openai"


@dataclass
class PromptSettings:
    """Settings for prompt management."""
    prompts_dir: Optional[str] = None
    default_analysis_prompt: str = "construction_analysis"
    default_progress_prompt: str = "progress_assessment"
    enable_prompt_override: bool = False
    custom_prompts: dict = field(default_factory=dict)


@dataclass
class AnalysisConfig:
    """Configuration for construction site analysis."""
    model_provider: ModelProvider
    model_name: str
    api_key: str
    memory_file_path: str = "construction_memory.txt"
    max_images_per_request: int = 20
    max_file_size_mb: int = 15
    enable_detailed_logging: bool = True
    prompt_settings: PromptSettings = field(default_factory=PromptSettings) 