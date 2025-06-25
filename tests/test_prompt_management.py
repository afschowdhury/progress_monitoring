"""
Tests for the prompt management system.
"""
import tempfile
import os
from pathlib import Path
import pytest

from progress_monitoring.prompts import PromptManager, PromptConfig, PromptType


class TestPromptManagement:
    """Test cases for prompt management functionality."""
    
    def test_prompt_manager_initialization(self):
        """Test that PromptManager initializes correctly."""
        prompt_manager = PromptManager()
        assert prompt_manager is not None
        assert hasattr(prompt_manager, '_prompts')
    
    def test_load_prompts_from_toml(self):
        """Test loading prompts from TOML files."""
        # Create a temporary directory with a test TOML file
        with tempfile.TemporaryDirectory() as temp_dir:
            toml_content = """
[test_prompt]
type = "analysis"
model_name = "gemini-2.5-pro"
temperature = 0.7
max_tokens = 2000
description = "Test prompt for unit testing"

template = '''
You are analyzing construction images for ${analysis_date}.
Current phase: ${current_phase}
Progress: ${overall_progress_percentage}%

Please provide analysis.
'''

variables = { analysis_date = "Today", current_phase = "Unknown", overall_progress_percentage = 0 }
"""
            
            # Write the TOML file
            toml_file = Path(temp_dir) / "test.toml"
            with open(toml_file, 'w') as f:
                f.write(toml_content)
            
            # Load prompts
            prompt_manager = PromptManager(temp_dir)
            
            # Check that the prompt was loaded
            assert "test_prompt" in prompt_manager.list_prompts()
            
            # Check prompt configuration
            prompt_config = prompt_manager.get_prompt("test_prompt")
            assert prompt_config is not None
            assert prompt_config.name == "test_prompt"
            assert prompt_config.prompt_type == PromptType.ANALYSIS
            assert prompt_config.model_name == "gemini-2.5-pro"
            assert prompt_config.temperature == 0.7
            assert prompt_config.max_tokens == 2000
            assert prompt_config.description == "Test prompt for unit testing"
    
    def test_prompt_rendering(self):
        """Test prompt template rendering with variables."""
        with tempfile.TemporaryDirectory() as temp_dir:
            toml_content = """
[render_test]
type = "analysis"
model_name = "gemini-2.5-pro"
temperature = 0.7
description = "Test prompt rendering"

template = '''
Analysis date: ${analysis_date}
Phase: ${current_phase}
Progress: ${overall_progress_percentage}%
Context: ${historical_context}
'''

variables = { analysis_date = "Default Date", current_phase = "Default Phase", overall_progress_percentage = 0, historical_context = "Default Context" }
"""
            
            toml_file = Path(temp_dir) / "render_test.toml"
            with open(toml_file, 'w') as f:
                f.write(toml_content)
            
            prompt_manager = PromptManager(temp_dir)
            
            # Test rendering with custom variables
            variables = {
                "analysis_date": "2025-01-15",
                "current_phase": "Foundation Work",
                "overall_progress_percentage": 25,
                "historical_context": "Previous excavation completed"
            }
            
            rendered = prompt_manager.render_prompt("render_test", variables)
            assert rendered is not None
            assert "Analysis date: 2025-01-15" in rendered
            assert "Phase: Foundation Work" in rendered
            assert "Progress: 25%" in rendered
            assert "Context: Previous excavation completed" in rendered
    
    def test_prompt_rendering_with_defaults(self):
        """Test prompt rendering with default variables."""
        with tempfile.TemporaryDirectory() as temp_dir:
            toml_content = """
[default_test]
type = "analysis"
model_name = "gemini-2.5-pro"
temperature = 0.7
description = "Test default variables"

template = '''
Analysis date: ${analysis_date}
Phase: ${current_phase}
Progress: ${overall_progress_percentage}%
'''

variables = { analysis_date = "Default Date", current_phase = "Default Phase", overall_progress_percentage = 0 }
"""
            
            toml_file = Path(temp_dir) / "default_test.toml"
            with open(toml_file, 'w') as f:
                f.write(toml_content)
            
            prompt_manager = PromptManager(temp_dir)
            
            # Test rendering with no variables (should use defaults)
            rendered = prompt_manager.render_prompt("default_test", {})
            assert rendered is not None
            assert "Analysis date: Default Date" in rendered
            assert "Phase: Default Phase" in rendered
            assert "Progress: 0%" in rendered
    
    def test_prompt_not_found(self):
        """Test handling of non-existent prompts."""
        prompt_manager = PromptManager()
        
        # Test getting non-existent prompt
        prompt_config = prompt_manager.get_prompt("non_existent_prompt")
        assert prompt_config is None
        
        # Test rendering non-existent prompt
        rendered = prompt_manager.render_prompt("non_existent_prompt", {})
        assert rendered is None
    
    def test_prompt_info(self):
        """Test getting prompt information."""
        with tempfile.TemporaryDirectory() as temp_dir:
            toml_content = """
[info_test]
type = "analysis"
model_name = "gemini-2.5-pro"
temperature = 0.8
max_tokens = 3000
description = "Test prompt for info retrieval"

template = "Test template"
variables = { test_var = "test_value" }
"""
            
            toml_file = Path(temp_dir) / "info_test.toml"
            with open(toml_file, 'w') as f:
                f.write(toml_content)
            
            prompt_manager = PromptManager(temp_dir)
            
            info = prompt_manager.get_prompt_info("info_test")
            assert info is not None
            assert info["name"] == "info_test"
            assert info["type"] == "analysis"
            assert info["model_name"] == "gemini-2.5-pro"
            assert info["temperature"] == 0.8
            assert info["max_tokens"] == 3000
            assert info["description"] == "Test prompt for info retrieval"
            assert "test_var" in info["variables"]
    
    def test_prompts_by_type(self):
        """Test getting prompts by type."""
        with tempfile.TemporaryDirectory() as temp_dir:
            toml_content = """
[analysis_prompt]
type = "analysis"
model_name = "gemini-2.5-pro"
temperature = 0.7
template = "Analysis template"
variables = {}

[safety_prompt]
type = "safety_review"
model_name = "gemini-2.5-pro"
temperature = 0.3
template = "Safety template"
variables = {}

[quality_prompt]
type = "quality_assessment"
model_name = "gemini-2.5-pro"
temperature = 0.5
template = "Quality template"
variables = {}
"""
            
            toml_file = Path(temp_dir) / "types_test.toml"
            with open(toml_file, 'w') as f:
                f.write(toml_content)
            
            prompt_manager = PromptManager(temp_dir)
            
            # Test getting prompts by type
            analysis_prompts = prompt_manager.get_prompts_by_type(PromptType.ANALYSIS)
            assert len(analysis_prompts) == 1
            assert analysis_prompts[0].name == "analysis_prompt"
            
            safety_prompts = prompt_manager.get_prompts_by_type(PromptType.SAFETY_REVIEW)
            assert len(safety_prompts) == 1
            assert safety_prompts[0].name == "safety_prompt"
            
            quality_prompts = prompt_manager.get_prompts_by_type(PromptType.QUALITY_ASSESSMENT)
            assert len(quality_prompts) == 1
            assert quality_prompts[0].name == "quality_prompt"


if __name__ == "__main__":
    pytest.main([__file__]) 