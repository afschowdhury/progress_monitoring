"""
Basic import tests to verify the modular structure works correctly.
"""
import pytest


def test_package_imports():
    """Test that all main package components can be imported."""
    from progress_monitoring import (
        AnalysisConfig,
        ModelProvider,
        ConstructionSiteAnalyzer,
        ImageProcessor,
        MemoryManager,
        AIProvider,
        GeminiProvider,
        OpenAIProvider,
        create_gemini_analyzer,
        create_openai_analyzer,
        analyze_construction_progress
    )
    
    # Verify classes can be instantiated (with dummy data)
    config = AnalysisConfig(
        model_provider=ModelProvider.GEMINI,
        model_name="test-model",
        api_key="dummy-key"
    )
    
    assert config.model_provider == ModelProvider.GEMINI
    assert config.model_name == "test-model"
    assert config.api_key == "dummy-key"


def test_provider_imports():
    """Test that provider modules can be imported."""
    from progress_monitoring.providers import (
        AIProvider,
        GeminiProvider,
        OpenAIProvider,
        create_ai_provider
    )
    
    # Test that abstract base class exists
    assert AIProvider.__name__ == "AIProvider"
    
    # Test that concrete implementations exist
    assert GeminiProvider.__name__ == "GeminiProvider"
    assert OpenAIProvider.__name__ == "OpenAIProvider"


def test_config_enum():
    """Test that ModelProvider enum works correctly."""
    from progress_monitoring import ModelProvider
    
    assert ModelProvider.GEMINI.value == "gemini"
    assert ModelProvider.OPENAI.value == "openai"
    
    # Test enum comparison
    assert ModelProvider.GEMINI == ModelProvider.GEMINI
    assert ModelProvider.GEMINI != ModelProvider.OPENAI


def test_factory_functions():
    """Test that factory functions can be called (with dummy data)."""
    from progress_monitoring import create_gemini_analyzer, create_openai_analyzer
    
    # These should raise ImportError due to missing dependencies, not AttributeError
    with pytest.raises(ImportError):
        create_gemini_analyzer("dummy-key")
    
    with pytest.raises(ImportError):
        create_openai_analyzer("dummy-key")


def test_memory_manager():
    """Test that MemoryManager can be instantiated and basic operations work."""
    from progress_monitoring import MemoryManager
    import tempfile
    import os
    
    # Create temporary file for testing
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_file = f.name
    
    try:
        memory_manager = MemoryManager(temp_file)
        
        # Test reading default memory
        memory_data = memory_manager.read_memory()
        assert "project_start_date" in memory_data
        assert "total_days_analyzed" in memory_data
        assert "daily_reports" in memory_data
        assert "key_milestones" in memory_data
        assert "current_phase" in memory_data
        assert "overall_progress_percentage" in memory_data
        
        # Test writing memory
        test_data = {"test": "data"}
        memory_manager.write_memory(test_data)
        
        # Verify file was created
        assert os.path.exists(temp_file)
        
    finally:
        # Clean up
        if os.path.exists(temp_file):
            os.unlink(temp_file)


def test_image_processor():
    """Test that ImageProcessor can be instantiated."""
    from progress_monitoring import ImageProcessor, AnalysisConfig, ModelProvider
    
    config = AnalysisConfig(
        model_provider=ModelProvider.GEMINI,
        model_name="test-model",
        api_key="dummy-key"
    )
    
    processor = ImageProcessor(config)
    
    # Test that supported formats are defined
    assert processor.supported_formats
    assert '.jpg' in processor.supported_formats
    assert '.png' in processor.supported_formats
    
    # Test MIME type mapping
    assert processor._get_mime_type("test.jpg") == "image/jpeg"
    assert processor._get_mime_type("test.png") == "image/png"
    assert processor._get_mime_type("test.unknown") == "image/jpeg"  # default 