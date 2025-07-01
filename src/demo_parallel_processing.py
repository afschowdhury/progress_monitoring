"""
Demo script for parallel processing and rate limiting with multiple images.
"""

import os
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent))

import os

from dotenv import load_dotenv

from progress_monitoring import AnalysisConfig, ConstructionSiteAnalyzer, ModelProvider
from progress_monitoring.providers.openai_provider import BatchConfig, OpenAIProvider
from progress_monitoring.utils import process_images_parallel

load_dotenv()

GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def get_images_folder(os_name, day_number):
    """Get the path to images folder based on OS."""
    if os_name == "win":
        return f"/home/achowd6/CODES/crc/progress-monitoring/src/progress_monitoring/video_sampler/img_data/day{day_number}"
    elif os_name == "mac":
        return f"/Users/afschowdhury/Code Local/crc/progress-monitoring/progress_monitoring/src/progress_monitoring/video_sampler/img_data/day{day_number}"
    else:
        raise ValueError(f"Unsupported OS: {os_name}")


def demo_basic_rate_limiting():
    """Demo basic rate limiting with OpenAI provider."""
    print("=== Demo: Basic Rate Limiting ===")

    config = AnalysisConfig(
        model_provider=ModelProvider.OPENAI,
        api_key=OPENAI_API_KEY,
        model_name="gpt-4o-mini",
        memory_file_path="demo_rate_limit_memory.txt",
        max_images_per_request=20,
    )

    analyzer = ConstructionSiteAnalyzer(config)

    # Test with a single day
    try:
        day_report = analyzer.analyze_single_day(get_images_folder("win", 3), 3, 5)
        print(f"✅ Analysis completed successfully!")
        print(f"   Images processed: {day_report.get('images_processed', 0)}")
        print(f"   Status: {day_report.get('status', 'unknown')}")

        # Show rate limit stats if available
        if hasattr(analyzer.ai_provider, "get_rate_limit_stats"):
            stats = analyzer.ai_provider.get_rate_limit_stats()
            print(f"   Rate limit stats: {stats}")

    except Exception as e:
        print(f"❌ Analysis failed: {e}")


def demo_parallel_processing():
    """Demo parallel processing with multiple image batches."""
    print("\n=== Demo: Parallel Processing ===")

    config = AnalysisConfig(
        model_provider=ModelProvider.OPENAI,
        api_key=OPENAI_API_KEY,
        model_name="gpt-4o-mini",
        memory_file_path="demo_parallel_memory.txt",
        max_images_per_request=50,  # Allow more images for parallel processing
    )

    analyzer = ConstructionSiteAnalyzer(config)

    # Test parallel processing with a day that has many images
    try:
        day_report = analyzer.analyze_single_day(get_images_folder("win", 3), 3, 5)
        print(f"✅ Parallel processing completed!")
        print(f"   Images processed: {day_report.get('images_processed', 0)}")
        print(f"   Status: {day_report.get('status', 'unknown')}")

    except Exception as e:
        print(f"❌ Parallel processing failed: {e}")


def demo_custom_batch_config():
    """Demo custom batch configuration."""
    print("\n=== Demo: Custom Batch Configuration ===")

    config = AnalysisConfig(
        model_provider=ModelProvider.OPENAI,
        api_key=OPENAI_API_KEY,
        model_name="gpt-4o-mini",
        memory_file_path="demo_custom_batch_memory.txt",
    )

    # Create analyzer
    analyzer = ConstructionSiteAnalyzer(config)

    # Customize batch configuration for OpenAI provider
    if isinstance(analyzer.ai_provider, OpenAIProvider):
        custom_batch_config = BatchConfig(
            max_images_per_batch=5,  # Smaller batches
            max_concurrent_requests=2,  # Fewer concurrent requests
            request_delay_seconds=2.0,  # Longer delay between requests
            max_retries=3,
            timeout_seconds=30,
        )
        analyzer.ai_provider.set_batch_config(custom_batch_config)
        print(f"✅ Custom batch config applied: {custom_batch_config}")

    try:
        day_report = analyzer.analyze_single_day(get_images_folder("win", 3), 3, 5)
        print(f"✅ Custom batch processing completed!")
        print(f"   Images processed: {day_report.get('images_processed', 0)}")

    except Exception as e:
        print(f"❌ Custom batch processing failed: {e}")


def demo_advanced_parallel_processor():
    """Demo the advanced parallel processor utility directly."""
    print("\n=== Demo: Advanced Parallel Processor ===")

    config = AnalysisConfig(
        model_provider=ModelProvider.OPENAI,
        api_key=OPENAI_API_KEY,
        model_name="gpt-4o-mini",
        memory_file_path="demo_advanced_parallel_memory.txt",
    )

    analyzer = ConstructionSiteAnalyzer(config)

    # Get images for processing
    image_folder = get_images_folder("win", 3)
    image_files = analyzer.image_processor.get_image_files(image_folder)
    prepared_images = analyzer.image_processor.prepare_images(image_files)

    if not prepared_images:
        print("❌ No images found for processing")
        return

    # Test prompt
    test_prompt = """
    Analyze these construction site images and provide a detailed assessment of:
    1. Current construction activities
    2. Progress made
    3. Equipment and materials present
    4. Safety observations
    5. Quality of work
    
    Provide a professional, factual analysis.
    """

    try:
        # Use the advanced parallel processor
        analysis_text = process_images_parallel(
            images=prepared_images,
            prompt=test_prompt,
            ai_provider=analyzer.ai_provider,
            config=config,
            max_workers=2,  # Conservative number of workers
            batch_size=8,  # Smaller batch size
        )

        print(f"✅ Advanced parallel processing completed!")
        print(f"   Images processed: {len(prepared_images)}")
        print(f"   Analysis length: {len(analysis_text)} characters")
        print(f"   Analysis preview: {analysis_text[:200]}...")

    except Exception as e:
        print(f"❌ Advanced parallel processing failed: {e}")


def main():
    """Run all demos."""
    print(
        "🚀 Construction Progress Monitoring - Parallel Processing & Rate Limiting Demo"
    )
    print("=" * 80)

    if not OPENAI_API_KEY:
        print("❌ OPENAI_API_KEY not found in environment variables")
        print("   Please set your OpenAI API key and try again")
        return

    # Run demos
    demo_basic_rate_limiting()
    demo_parallel_processing()
    demo_custom_batch_config()
    demo_advanced_parallel_processor()

    print("\n" + "=" * 80)
    print("✅ All demos completed!")
    print("\nKey Features Demonstrated:")
    print("• Rate limiting with exponential backoff")
    print("• Parallel processing of multiple image batches")
    print("• Customizable batch configurations")
    print("• Automatic fallback to sequential processing")
    print("• Comprehensive error handling and retry logic")


if __name__ == "__main__":
    main()
