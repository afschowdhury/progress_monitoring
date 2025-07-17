"""
Factory functions for creating image analyzers and progress report generators.
"""
from typing import Dict, Any, Optional, Tuple

from .config import AnalysisConfig, ModelProvider, PromptSettings
from .analyzer import ImageAnalyzer
from .progress_report_generator import ProgressReportGenerator
from .memory_manager import MemoryManager


def create_gemini_components(api_key: str, model_name: str = "gemini-2.5-pro", 
                            memory_file: str = "construction_memory.txt",
                            prompts_dir: Optional[str] = None,
                            custom_prompts: Optional[Dict[str, str]] = None) -> Tuple[ImageAnalyzer, ProgressReportGenerator, MemoryManager]:
    """Create image analyzer, progress generator, and memory manager configured for Gemini."""
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
    
    image_analyzer = ImageAnalyzer(config)
    progress_generator = ProgressReportGenerator(config)
    memory_manager = MemoryManager(memory_file)
    
    return image_analyzer, progress_generator, memory_manager


def create_openai_components(api_key: str, model_name: str = "gpt-4o", 
                            memory_file: str = "construction_memory.txt",
                            prompts_dir: Optional[str] = None,
                            custom_prompts: Optional[Dict[str, str]] = None) -> Tuple[ImageAnalyzer, ProgressReportGenerator, MemoryManager]:
    """Create image analyzer, progress generator, and memory manager configured for OpenAI."""
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
    
    image_analyzer = ImageAnalyzer(config)
    progress_generator = ProgressReportGenerator(config)
    memory_manager = MemoryManager(memory_file)
    
    return image_analyzer, progress_generator, memory_manager


def create_gemini_analyzer(api_key: str, model_name: str = "gemini-2.5-pro", 
                          memory_file: str = "construction_memory.txt",
                          prompts_dir: Optional[str] = None,
                          custom_prompts: Optional[Dict[str, str]] = None) -> ImageAnalyzer:
    """Create image analyzer configured for Gemini (legacy compatibility)."""
    image_analyzer, _, _ = create_gemini_components(api_key, model_name, memory_file, prompts_dir, custom_prompts)
    return image_analyzer


def create_openai_analyzer(api_key: str, model_name: str = "gpt-4o", 
                          memory_file: str = "construction_memory.txt",
                          prompts_dir: Optional[str] = None,
                          custom_prompts: Optional[Dict[str, str]] = None) -> ImageAnalyzer:
    """Create image analyzer configured for OpenAI (legacy compatibility)."""
    image_analyzer, _, _ = create_openai_components(api_key, model_name, memory_file, prompts_dir, custom_prompts)
    return image_analyzer


def create_analyzer_with_custom_prompts(provider: str, api_key: str, 
                                      prompts_dir: str,
                                      model_name: str = None,
                                      memory_file: str = "construction_memory.txt",
                                      custom_prompts: Optional[Dict[str, str]] = None) -> ImageAnalyzer:
    """
    Create image analyzer with custom prompt configurations (legacy compatibility).
    
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


def create_complete_system(provider: str, api_key: str,
                          model_name: str = None, memory_file: str = "construction_memory.txt",
                          prompts_dir: Optional[str] = None,
                          custom_prompts: Optional[Dict[str, str]] = None) -> Tuple[ImageAnalyzer, ProgressReportGenerator, MemoryManager]:
    """
    Create complete system with image analyzer, progress generator, and memory manager.
    
    Args:
        provider: "gemini" or "openai"
        api_key: API key for the provider
        model_name: Optional model name (uses defaults if None)
        memory_file: Path to memory file
        prompts_dir: Optional directory containing custom prompt TOML files
        custom_prompts: Optional dictionary of custom prompt overrides
        
    Returns:
        Tuple of (ImageAnalyzer, ProgressReportGenerator, MemoryManager)
    """
    if provider.lower() == "gemini":
        model_name = model_name or "gemini-2.5-pro"
        return create_gemini_components(api_key, model_name, memory_file, prompts_dir, custom_prompts)
    elif provider.lower() == "openai":
        model_name = model_name or "gpt-4o"
        return create_openai_components(api_key, model_name, memory_file, prompts_dir, custom_prompts)
    else:
        raise ValueError(f"Unsupported provider: {provider}")


def analyze_construction_progress(provider: str, api_key: str, folder_path: str,
                                model_name: str = None, memory_file: str = "construction_memory.txt",
                                prompts_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Analyze construction progress with specified provider (convenience function).
    
    Args:
        provider: "gemini" or "openai"
        api_key: API key for the provider
        folder_path: Path to images folder
        model_name: Optional model name (uses defaults if None)
        memory_file: Path to memory file
        prompts_dir: Optional directory containing custom prompt TOML files
        
    Returns:
        Complete analysis and progress report
    """
    # Create complete system
    image_analyzer, progress_generator, memory_manager = create_complete_system(
        provider, api_key, model_name, memory_file, prompts_dir
    )
    
    # Get project context from memory
    project_memory = memory_manager.get_project_memory()
    
    # Analyze images
    analysis_result = image_analyzer.analyze_images_in_folder(
        folder_path, 
        project_context=project_memory
    )
    
    if analysis_result.get("status") != "success":
        return analysis_result
    
    # Generate progress report
    from datetime import datetime
    date = datetime.now().strftime("%Y-%m-%d")
    
    progress_report = progress_generator.generate_progress_report(
        analysis_content=analysis_result["analysis_text"],
        memory_metadata=project_memory,
        date=date,
        image_folder_path=folder_path
    )
    
    # Store in memory
    if progress_report.get("status") == "success":
        memory_manager.store_progress_report(
            date=date,
            image_folder_path=folder_path,
            analysis_content=analysis_result["analysis_text"],
            progress_report=progress_report["progress_data"]
        )
    
    return {
        "analysis_result": analysis_result,
        "progress_report": progress_report,
        "memory_updated": True,
        "date": date,
        "status": "success"
    } 