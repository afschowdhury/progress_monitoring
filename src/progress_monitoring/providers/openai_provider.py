"""
OpenAI provider implementation.
"""
import base64
import logging
from typing import List, Dict, Any

from .base import AIProvider
from ..config import AnalysisConfig


class OpenAIProvider(AIProvider):
    """OpenAI provider implementation."""
    
    def __init__(self, config: AnalysisConfig):
        super().__init__(config)
        try:
            import openai
            self.client = openai.OpenAI(api_key=config.api_key)
        except ImportError:
            raise ImportError("Please install openai: pip install openai")
    
    def analyze_images(self, images: List[Dict[str, Any]], prompt: str) -> str:
        """Analyze images using OpenAI GPT-4 Vision."""
        try:
            # Prepare messages for OpenAI
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt}
                    ]
                }
            ]
            
            # Add images to message content
            for img_data in images:
                if img_data['method'] == 'base64':
                    image_content = {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{img_data['mime_type']};base64,{img_data['base64_data']}"
                        }
                    }
                    messages[0]["content"].append(image_content)
                else:
                    # For file uploads, we need to convert to base64
                    with open(img_data['path'], 'rb') as f:
                        image_bytes = f.read()
                    base64_image = base64.b64encode(image_bytes).decode('utf-8')
                    image_content = {
                        "type": "image_url", 
                        "image_url": {
                            "url": f"data:{img_data['mime_type']};base64,{base64_image}"
                        }
                    }
                    messages[0]["content"].append(image_content)
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.config.model_name,
                messages=messages,
                max_tokens=4000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            self.logger.error(f"OpenAI analysis failed: {e}")
            raise
    
    def generate_structured_response(self, prompt: str) -> str:
        """Generate structured response using OpenAI."""
        try:
            response = self.client.chat.completions.create(
                model=self.config.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000
            )
            return response.choices[0].message.content
        except Exception as e:
            self.logger.error(f"OpenAI structured response failed: {e}")
            raise 