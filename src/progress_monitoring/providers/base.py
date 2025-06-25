"""
Abstract base class for AI model providers.
"""
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any

from ..config import AnalysisConfig


class AIProvider(ABC):
    """Abstract base class for AI model providers."""
    
    def __init__(self, config: AnalysisConfig):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        
    @abstractmethod
    def analyze_images(self, images: List[Dict[str, Any]], prompt: str) -> str:
        """Analyze images with the given prompt."""
        pass
    
    @abstractmethod
    def generate_structured_response(self, prompt: str) -> str:
        """Generate a structured response from a text prompt."""
        pass 