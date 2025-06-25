#!/usr/bin/env python3
"""
Basic usage example for construction progress monitoring.

This example shows how to use the package to analyze construction site images.
"""
import os
import json
from pathlib import Path

# Import the package
from progress_monitoring import (
    analyze_construction_progress,
    create_gemini_analyzer,
    create_openai_analyzer,
    AnalysisConfig,
    ModelProvider
)


def example_with_factory_function():
    """Example using the convenience factory function."""
    print("=== Example 1: Using Factory Function ===")
    
    # You'll need to set these environment variables or replace with your actual keys
    gemini_api_key = os.getenv("GEMINI_API_KEY", "your-gemini-api-key")
    openai_api_key = os.getenv("OPENAI_API_KEY", "your-openai-api-key")
    
    # Path to your construction site images
    images_folder = "path/to/your/construction/images"
    
    # Example with Gemini
    try:
        result = analyze_construction_progress(
            provider="gemini",
            api_key=gemini_api_key,
            folder_path=images_folder,
            model_name="gemini-2.5-pro"
        )
        
        print(f"Analysis completed: {result['status']}")
        print(f"Images processed: {result['images_processed']}")
        print(f"Current phase: {result['progress_report']['current_phase']}")
        
    except Exception as e:
        print(f"Gemini analysis failed: {e}")
    
    # Example with OpenAI
    try:
        result = analyze_construction_progress(
            provider="openai",
            api_key=openai_api_key,
            folder_path=images_folder,
            model_name="gpt-4o"
        )
        
        print(f"Analysis completed: {result['status']}")
        print(f"Images processed: {result['images_processed']}")
        print(f"Current phase: {result['progress_report']['current_phase']}")
        
    except Exception as e:
        print(f"OpenAI analysis failed: {e}")


def example_with_direct_analyzer():
    """Example using the analyzer directly with custom configuration."""
    print("\n=== Example 2: Using Analyzer Directly ===")
    
    # Create custom configuration
    config = AnalysisConfig(
        model_provider=ModelProvider.GEMINI,
        model_name="gemini-2.5-pro",
        api_key=os.getenv("GEMINI_API_KEY", "your-gemini-api-key"),
        memory_file_path="my_project_memory.json",
        max_images_per_request=15,
        max_file_size_mb=10,
        enable_detailed_logging=True
    )
    
    # Create analyzer
    from progress_monitoring import ConstructionSiteAnalyzer
    analyzer = ConstructionSiteAnalyzer(config)
    
    # Analyze construction site
    images_folder = "path/to/your/construction/images"
    
    try:
        result = analyzer.analyze_construction_site(images_folder)
        
        print(f"Analysis completed: {result['status']}")
        print(f"Model used: {result['model_used']}")
        print(f"Images processed: {result['images_processed']}")
        
        # Print detailed results
        progress = result['progress_report']
        print(f"\nProgress Report:")
        print(f"  Current Phase: {progress['current_phase']}")
        print(f"  Overall Progress: {progress['overall_progress_percentage']}%")
        print(f"  Daily Progress: {progress['daily_progress_percentage']}%")
        print(f"  Timeline Status: {progress['estimated_timeline_status']}")
        
        # Print accomplishments
        if progress['key_accomplishments']:
            print(f"\nKey Accomplishments:")
            for acc in progress['key_accomplishments']:
                print(f"  • {acc}")
        
        # Print issues
        if progress['identified_issues']:
            print(f"\nIdentified Issues:")
            for issue in progress['identified_issues']:
                print(f"  • {issue}")
        
        # Save results to file
        with open("analysis_results.json", "w") as f:
            json.dump(result, f, indent=2)
        print(f"\nFull results saved to: analysis_results.json")
        
    except Exception as e:
        print(f"Analysis failed: {e}")


def example_memory_management():
    """Example showing memory management features."""
    print("\n=== Example 3: Memory Management ===")
    
    from progress_monitoring import MemoryManager
    
    # Create memory manager
    memory_manager = MemoryManager("project_memory.json")
    
    # Read existing memory
    memory_data = memory_manager.read_memory()
    print(f"Project start date: {memory_data['project_start_date']}")
    print(f"Total days analyzed: {memory_data['total_days_analyzed']}")
    print(f"Current phase: {memory_data['current_phase']}")
    print(f"Overall progress: {memory_data['overall_progress_percentage']}%")
    
    # Show recent milestones
    if memory_data['key_milestones']:
        print(f"\nRecent milestones:")
        for milestone in memory_data['key_milestones'][-3:]:
            print(f"  • {milestone['date']}: {milestone['description']} ({milestone['progress_percentage']}%)")


def example_image_processing():
    """Example showing image processing features."""
    print("\n=== Example 4: Image Processing ===")
    
    from progress_monitoring import ImageProcessor, AnalysisConfig
    
    # Create image processor
    config = AnalysisConfig(
        model_provider=ModelProvider.GEMINI,
        model_name="gemini-2.5-pro",
        api_key="dummy-key",
        max_images_per_request=10,
        max_file_size_mb=5
    )
    
    image_processor = ImageProcessor(config)
    
    # Get image files from folder
    images_folder = "path/to/your/construction/images"
    
    try:
        image_files = image_processor.get_image_files(images_folder)
        print(f"Found {len(image_files)} image files:")
        for img_file in image_files[:5]:  # Show first 5
            print(f"  • {Path(img_file).name}")
        
        if len(image_files) > 5:
            print(f"  ... and {len(image_files) - 5} more")
        
        # Prepare images for analysis
        prepared_images = image_processor.prepare_images(image_files)
        print(f"\nPrepared {len(prepared_images)} images for analysis")
        
    except Exception as e:
        print(f"Image processing failed: {e}")


if __name__ == "__main__":
    print("Construction Progress Monitoring - Usage Examples")
    print("=" * 50)
    
    # Note: These examples require actual API keys and image folders
    # Uncomment the examples you want to run
    
    # example_with_factory_function()
    # example_with_direct_analyzer()
    # example_memory_management()
    # example_image_processing()
    
    print("\nTo run these examples:")
    print("1. Set your API keys as environment variables:")
    print("   export GEMINI_API_KEY='your-gemini-api-key'")
    print("   export OPENAI_API_KEY='your-openai-api-key'")
    print("2. Update the image folder paths in the examples")
    print("3. Uncomment the example functions you want to run")
    print("4. Run: python examples/basic_usage.py") 