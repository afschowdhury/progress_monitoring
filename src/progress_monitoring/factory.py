"""
Factory functions for creating construction site analyzers.
"""
from typing import Dict, Any, Optional

from .config import AnalysisConfig, ModelProvider, PromptSettings
from .analyzer import ConstructionSiteAnalyzer


def create_gemini_analyzer(api_key: str, model_name: str = "gemini-2.5-pro", 
                          memory_file: str = "construction_memory.txt",
                          prompts_dir: Optional[str] = None,
                          custom_prompts: Optional[Dict[str, str]] = None) -> ConstructionSiteAnalyzer:
    """Create analyzer configured for Gemini."""
    prompt_settings = PromptSettings(
        prompts_dir=prompts_dir,
        default_analysis_prompt="construction_analysis",
        default_progress_prompt="progress_assessment",
        custom_prompts=custom_prompts or {}
    )
    
    config = AnalysisConfig(
        model_provider=ModelProvider.GEMINI,
        model_name=model_name,
        api_key=api_key,
        memory_file_path=memory_file,
        prompt_settings=prompt_settings
    )
    return ConstructionSiteAnalyzer(config)


def create_openai_analyzer(api_key: str, model_name: str = "gpt-4o", 
                          memory_file: str = "construction_memory.txt",
                          prompts_dir: Optional[str] = None,
                          custom_prompts: Optional[Dict[str, str]] = None) -> ConstructionSiteAnalyzer:
    """Create analyzer configured for OpenAI."""
    prompt_settings = PromptSettings(
        prompts_dir=prompts_dir,
        default_analysis_prompt="construction_analysis",
        default_progress_prompt="progress_assessment",
        custom_prompts=custom_prompts or {}
    )
    
    config = AnalysisConfig(
        model_provider=ModelProvider.OPENAI,
        model_name=model_name,
        api_key=api_key,
        memory_file_path=memory_file,
        prompt_settings=prompt_settings
    )
    return ConstructionSiteAnalyzer(config)


def create_analyzer_with_custom_prompts(provider: str, api_key: str, 
                                      prompts_dir: str,
                                      model_name: str = None,
                                      memory_file: str = "construction_memory.txt",
                                      custom_prompts: Optional[Dict[str, str]] = None) -> ConstructionSiteAnalyzer:
    """
    Create analyzer with custom prompt configurations.
    
    Args:
        provider: "gemini" or "openai"
        api_key: API key for the provider
        prompts_dir: Directory containing custom prompt TOML files
        model_name: Optional model name (uses defaults if None)
        memory_file: Path to memory file
        custom_prompts: Optional dictionary of custom prompt overrides
    """
    if provider.lower() == "gemini":
        model_name = model_name or "gemini-2.5-pro"
        return create_gemini_analyzer(api_key, model_name, memory_file, prompts_dir, custom_prompts)
    elif provider.lower() == "openai":
        model_name = model_name or "gpt-4o"
        return create_openai_analyzer(api_key, model_name, memory_file, prompts_dir, custom_prompts)
    else:
        raise ValueError(f"Unsupported provider: {provider}")


def analyze_construction_progress(provider: str, api_key: str, folder_path: str,
                                model_name: str = None, memory_file: str = "construction_memory.txt",
                                prompts_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Analyze construction progress with specified provider.
    
    Args:
        provider: "gemini" or "openai"
        api_key: API key for the provider
        folder_path: Path to images folder
        model_name: Optional model name (uses defaults if None)
        memory_file: Path to memory file
        prompts_dir: Optional directory containing custom prompt TOML files
    """
    if provider.lower() == "gemini":
        model_name = model_name or "gemini-2.5-pro"
        analyzer = create_gemini_analyzer(api_key, model_name, memory_file, prompts_dir)
    elif provider.lower() == "openai":
        model_name = model_name or "gpt-4o"
        analyzer = create_openai_analyzer(api_key, model_name, memory_file, prompts_dir)
    else:
        raise ValueError(f"Unsupported provider: {provider}")
    
    return analyzer.analyze_construction_site(folder_path) 