"""
Construction Progress Monitoring Demo - Single Day Analysis

This script demonstrates single day analysis using the new architecture:
- ImageAnalyzer for image analysis
- ProgressReportGenerator for structured reports  
- Enhanced MemoryManager with Qdrant support
"""

import os
import platform
from datetime import datetime
from dotenv import load_dotenv
from icecream import ic

# Import new architecture components
from progress_monitoring import (
    ImageAnalyzer, 
    ProgressReportGenerator, 
    MemoryManager,
    create_complete_system
)

# Configure debugging
ic.configureOutput(includeContext=True, prefix="DEBUG -")
load_dotenv()

# API Keys
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Path configurations
WINDOWS_PATH_PREFIX = "/home/achowd6/CODES/crc/progress-monitoring/src/progress_monitoring/video_sampler/img_data"
MAC_PATH_PREFIX = "/Users/afschowdhury/Code Local/crc/progress-monitoring/progress_monitoring/src/progress_monitoring/video_sampler/img_data"

# Configuration
PROVIDER = "openai"  # or "gemini"
MEMORY_FILE = "demo_memory.json"

def get_images_folder(os_name, day_number):
    """Get the appropriate image folder path based on OS."""
    if os_name == "win":
        return f"{WINDOWS_PATH_PREFIX}/day{day_number}"
    elif os_name == "mac":
        return f"{MAC_PATH_PREFIX}/day{day_number}"
    else:
        raise ValueError(f"Unsupported OS: {os_name}")

def analyze_single_day_new_architecture(day_number, total_days=5, provider="openai"):
    """
    Analyze a single day using the new architecture.
    Similar to the old analyzer.analyze_single_day() but with separated components.
    
    Args:
        day_number: Day number to analyze
        total_days: Total days in the project
        provider: AI provider to use ("openai" or "gemini")
        
    Returns:
        Complete day report with analysis and progress data
    """
    print(f"=== Analyzing Day {day_number} using New Architecture ({provider}) ===")
    
    # Get API key based on provider
    api_key = OPENAI_API_KEY if provider == "openai" else GEMINI_API_KEY
    if not api_key:
        print(f"Please set {provider.upper()}_API_KEY in your environment")
        return None
    
    # Create all components using factory function
    image_analyzer, progress_generator, memory_manager = create_complete_system(
        provider=provider,
        api_key=api_key,
        memory_file=MEMORY_FILE
    )
    
    print(f"✓ Created components using {provider} provider")
    
    # Auto-detect OS and get image folder
    os_name = "mac" if platform.system() == "Darwin" else "win"
    image_folder = get_images_folder(os_name, day_number)
    
    print(f"✓ Using image folder: {image_folder}")
    
    if not os.path.exists(image_folder):
        print(f"✗ Image folder not found: {image_folder}")
        return {
            "day_number": day_number,
            "error": f"Image folder not found: {image_folder}",
            "status": "failed"
        }
    
    # Get project context from memory
    project_memory = memory_manager.get_project_memory()
    print(f"✓ Loaded project memory: {project_memory.get('total_records', 0)} records")
    
    # Set project context for day analysis
    project_context = {
        "current_phase": project_memory.get("current_phase", "Construction Phase"),
        "overall_progress_percentage": project_memory.get("overall_progress_percentage", 0),
        "project_start_date": project_memory.get("project_start_date", datetime.now().strftime("%Y-%m-%d")),
        "total_days_analyzed": project_memory.get("total_days_analyzed", 0)
    }
    
    # Get previous day summary for context
    previous_day_summary = ""
    if day_number > 1:
        previous_reports = memory_manager.get_recent_reports(days=1, record_type="analysis_report")
        if previous_reports:
            previous_day_summary = previous_reports[0].get("analysis_summary", "")
    
    try:
        # Step 1: Analyze images using ImageAnalyzer
        print(f"Analyzing images in day{day_number}...")
        analysis_result = image_analyzer.analyze_images_in_folder(
            image_folder_path=image_folder,
            project_context=project_context,
            previous_day_summary=previous_day_summary
        )
        
        if analysis_result["status"] != "success":
            return {
                "day_number": day_number,
                "analysis_date": datetime.now().strftime("%Y-%m-%d"),
                "error": analysis_result.get("error"),
                "status": "failed"
            }
        
        print(f"✓ Successfully analyzed {analysis_result['images_processed']} images")
        
        # Step 2: Generate progress report using ProgressReportGenerator
        print(f"Generating progress report...")
        date = datetime.now().strftime("%Y-%m-%d")
        
        progress_report = progress_generator.generate_progress_report(
            analysis_content=analysis_result["analysis_text"],
            memory_metadata=project_memory,
            date=date,
            image_folder_path=image_folder,
            day_number=day_number
        )
        
        if progress_report["status"] != "success":
            return {
                "day_number": day_number,
                "analysis_date": date,
                "images_processed": analysis_result['images_processed'],
                "daily_description": analysis_result["analysis_text"],
                "progress_report_error": progress_report.get("error"),
                "status": "partial_success"
            }
        
        # Step 3: Store in enhanced memory
        print(f"Storing in memory...")
        
        # Prepare config information
        config_info = {
            "provider": provider,
            "model_name": image_analyzer.config.model_name,
            "analysis_prompt_used": "image_analysis_gemini" if provider == "gemini" else "image_analysis_openai",
            "progress_prompt_used": progress_generator.config.prompt_settings.default_progress_prompt,
            "temperature": getattr(image_analyzer.config, 'temperature', 0.7),
            "max_tokens": getattr(image_analyzer.config, 'max_tokens', 4000),
            "generation_timestamp": datetime.now().isoformat()
        }
        
        # Store analysis report
        analysis_record_id = memory_manager.store_analysis_report(
            date=date,
            image_folder_path=image_folder,
            analysis_content=analysis_result["analysis_text"],
            images_count=analysis_result['images_processed'],
            day_number=day_number,
            config_info=config_info
        )
        
        # Store progress report
        progress_record_id = memory_manager.store_progress_report(
            date=date,
            image_folder_path=image_folder,
            analysis_content=analysis_result["analysis_text"],
            progress_report=progress_report["progress_data"],
            day_number=day_number,
            config_info=config_info
        )
        
        print(f"✓ Stored analysis (ID: {analysis_record_id[:8]}...) and progress (ID: {progress_record_id[:8]}...)")
        
        # Create comprehensive day report (similar to old format but enhanced)
        day_report = {
            "day_number": day_number,
            "analysis_date": date,
            "model_used": f"{provider}/{progress_report.get('model_used', 'unknown')}",
            "images_processed": analysis_result['images_processed'],
            "daily_description": analysis_result["analysis_text"],
            "progress_report": progress_report["progress_data"],
            "memory_records": {
                "analysis_record_id": analysis_record_id,
                "progress_record_id": progress_record_id
            },
            "updated_memory": {
                "project_start_date": project_context["project_start_date"],
                "total_days_analyzed": day_number,
                "current_phase": progress_report["progress_data"].get("current_phase", "Unknown"),
                "overall_progress_percentage": progress_report["progress_data"].get("overall_progress_percentage", 0)
            },
            "status": "success"
        }
        
        print(f"✓ Day {day_number} analysis completed successfully!")
        return day_report
        
    except Exception as e:
        print(f"✗ Analysis failed for day {day_number}: {e}")
        return {
            "day_number": day_number,
            "analysis_date": datetime.now().strftime("%Y-%m-%d"),
            "error": str(e),
            "status": "failed"
        }

def main():
    """Main function - analyze a single day like the original approach."""
    print("Construction Progress Monitoring - Single Day Analysis")
    print("=" * 60)
    
    # Configuration - you can change these
    day_number = 2
    total_days = 5
    provider = "gemini"
    
    # Analyze the day with specified provider
    day_report = analyze_single_day_new_architecture(day_number, total_days, provider)
    
    # Display results (similar to the original ic(day_report))
    ic(day_report)
    
    if day_report and day_report.get("status") == "success":
        print(f"\n=== Day {day_number} Summary ({provider}) ===")
        progress_data = day_report["progress_report"]
        print(f"Current Phase: {progress_data.get('current_phase', 'Unknown')}")
        print(f"Overall Progress: {progress_data.get('overall_progress_percentage', 0)}%")
        print(f"Daily Progress: {progress_data.get('daily_progress_percentage', 0)}%")
        print(f"Images Processed: {day_report['images_processed']}")
        print(f"Key Accomplishments: {len(progress_data.get('key_accomplishments', []))}")
        print(f"Identified Issues: {len(progress_data.get('identified_issues', []))}")
        
        # Show first few accomplishments
        accomplishments = progress_data.get('key_accomplishments', [])
        if accomplishments:
            print(f"\nTop Accomplishments:")
            for i, acc in enumerate(accomplishments[:3]):
                print(f"  {i+1}. {acc}")
    
    print("\n" + "=" * 60)
    print("Analysis completed!")

if __name__ == "__main__":
    main()
