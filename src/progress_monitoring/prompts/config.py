"""
Prompt configuration classes for construction progress monitoring.
"""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from enum import Enum


class PromptType(Enum):
    """Types of prompts available in the system."""
    ANALYSIS = "analysis"
    PROGRESS_ASSESSMENT = "progress_assessment"
    SAFETY_REVIEW = "safety_review"
    QUALITY_ASSESSMENT = "quality_assessment"
    TIMELINE_ANALYSIS = "timeline_analysis"


@dataclass
class PromptConfig:
    """Configuration for a specific prompt."""
    name: str
    prompt_type: PromptType
    template: str
    model_name: str
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    system_message: Optional[str] = None
    variables: Dict[str, Any] = field(default_factory=dict)
    description: str = ""
    
    def __post_init__(self):
        """Convert string to enum if needed."""
        if isinstance(self.prompt_type, str):
            self.prompt_type = PromptType(self.prompt_type) 