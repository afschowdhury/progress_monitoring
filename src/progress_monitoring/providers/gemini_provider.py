"""
Google Gemini AI provider implementation.
"""
import logging
from typing import List, Dict, Any

from .base import AIProvider
from ..config import AnalysisConfig


class GeminiProvider(AIProvider):
    """Google Gemini AI provider implementation."""
    
    def __init__(self, config: AnalysisConfig):
        super().__init__(config)
        try:
            from google import genai
            from google.genai import types
            self.genai = genai
            self.types = types
            self.client = genai.Client(api_key=config.api_key)
        except ImportError:
            raise ImportError("Please install google-genai: pip install google-genai")
    
    def analyze_images(self, images: List[Dict[str, Any]], prompt: str) -> str:
        """Analyze images using Gemini."""
        try:
            # Prepare image parts for Gemini
            image_parts = []
            
            for img_data in images:
                if img_data['method'] == 'file_upload':
                    # Upload file using Gemini File API
                    uploaded_file = self.client.files.upload(file=img_data['path'])
                    image_parts.append(uploaded_file)
                else:
                    # Use inline data
                    image_part = self.types.Part.from_bytes(
                        data=img_data['data'],
                        mime_type=img_data['mime_type']
                    )
                    image_parts.append(image_part)
            
            # Prepare content for API
            contents = [prompt] + image_parts
            
            # Call Gemini API
            response = self.client.models.generate_content(
                model=self.config.model_name,
                contents=contents,
            )
            
            return response.text
            
        except Exception as e:
            self.logger.error(f"Gemini analysis failed: {e}")
            raise
    
    def generate_structured_response(self, prompt: str) -> str:
        """Generate structured response using Gemini."""
        try:
            response = self.client.models.generate_content(
                model=self.config.model_name,
                contents=[prompt],
            )
            return response.text
        except Exception as e:
            self.logger.error(f"Gemini structured response failed: {e}")
            raise 