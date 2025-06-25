"""
Prompt manager for loading and managing prompt configurations.
"""
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from string import Template

try:
    import tomllib
except ImportError:
    import tomli as tomllib

from .config import PromptConfig, PromptType


class PromptManager:
    """Manages prompt configurations loaded from TOML files."""
    
    def __init__(self, prompts_dir: Optional[str] = None):
        """
        Initialize the prompt manager.
        
        Args:
            prompts_dir: Directory containing prompt TOML files. 
                        Defaults to 'prompts' subdirectory of current module.
        """
        if prompts_dir is None:
            # Default to prompts directory relative to this module
            current_dir = Path(__file__).parent
            prompts_dir = current_dir / "templates"
        
        self.prompts_dir = Path(prompts_dir)
        self.logger = logging.getLogger(self.__class__.__name__)
        self._prompts: Dict[str, PromptConfig] = {}
        self._load_prompts()
    
    def _load_prompts(self) -> None:
        """Load all prompt configurations from TOML files."""
        if not self.prompts_dir.exists():
            self.logger.warning(f"Prompts directory does not exist: {self.prompts_dir}")
            return
        
        for toml_file in self.prompts_dir.glob("*.toml"):
            try:
                self._load_prompt_file(toml_file)
            except Exception as e:
                self.logger.error(f"Failed to load prompt file {toml_file}: {e}")
    
    def _load_prompt_file(self, file_path: Path) -> None:
        """Load a single prompt configuration from a TOML file."""
        with open(file_path, 'rb') as f:
            data = tomllib.load(f)
        
        # Each TOML file can contain multiple prompts
        for prompt_name, prompt_data in data.items():
            if prompt_name == "metadata":
                continue  # Skip metadata section
            
            try:
                prompt_config = PromptConfig(
                    name=prompt_name,
                    prompt_type=prompt_data.get("type", "analysis"),
                    template=prompt_data["template"],
                    model_name=prompt_data.get("model_name", "gemini-2.5-pro"),
                    temperature=prompt_data.get("temperature", 0.7),
                    max_tokens=prompt_data.get("max_tokens"),
                    top_p=prompt_data.get("top_p", 1.0),
                    frequency_penalty=prompt_data.get("frequency_penalty", 0.0),
                    presence_penalty=prompt_data.get("presence_penalty", 0.0),
                    system_message=prompt_data.get("system_message"),
                    variables=prompt_data.get("variables", {}),
                    description=prompt_data.get("description", "")
                )
                
                self._prompts[prompt_name] = prompt_config
                self.logger.info(f"Loaded prompt: {prompt_name}")
                
            except KeyError as e:
                self.logger.error(f"Missing required field in prompt {prompt_name}: {e}")
            except Exception as e:
                self.logger.error(f"Failed to parse prompt {prompt_name}: {e}")
    
    def get_prompt(self, name: str) -> Optional[PromptConfig]:
        """Get a prompt configuration by name."""
        return self._prompts.get(name)
    
    def get_prompts_by_type(self, prompt_type: PromptType) -> List[PromptConfig]:
        """Get all prompts of a specific type."""
        return [p for p in self._prompts.values() if p.prompt_type == prompt_type]
    
    def render_prompt(self, name: str, variables: Dict[str, Any]) -> Optional[str]:
        """
        Render a prompt template with the given variables.
        
        Args:
            name: Name of the prompt to render
            variables: Variables to substitute in the template
            
        Returns:
            Rendered prompt string or None if prompt not found
        """
        prompt_config = self.get_prompt(name)
        if not prompt_config:
            self.logger.error(f"Prompt not found: {name}")
            return None
        
        try:
            # Combine default variables with provided variables
            all_variables = {**prompt_config.variables, **variables}
            
            # Use string.Template for safe variable substitution
            template = Template(prompt_config.template)
            return template.safe_substitute(all_variables)
            
        except Exception as e:
            self.logger.error(f"Failed to render prompt {name}: {e}")
            return None
    
    def list_prompts(self) -> List[str]:
        """List all available prompt names."""
        return list(self._prompts.keys())
    
    def get_prompt_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a prompt."""
        prompt_config = self.get_prompt(name)
        if not prompt_config:
            return None
        
        return {
            "name": prompt_config.name,
            "type": prompt_config.prompt_type.value,
            "model_name": prompt_config.model_name,
            "temperature": prompt_config.temperature,
            "max_tokens": prompt_config.max_tokens,
            "description": prompt_config.description,
            "variables": prompt_config.variables
        } 