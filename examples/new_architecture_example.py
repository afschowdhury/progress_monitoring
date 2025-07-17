"""
Example demonstrating the new architecture with ImageAnalyzer and ProgressReportGenerator.

This example shows how to:
1. Use ImageAnalyzer to analyze construction images
2. Use ProgressReportGenerator to create structured reports
3. Use enhanced MemoryManager with Qdrant for vector storage
"""
import os
from dotenv import load_dotenv

from progress_monitoring import (
    ImageAnalyzer,
    ProgressReportGenerator, 
    MemoryManager,
    create_complete_system,
    analyze_construction_progress
)

def main():
    """Demonstrate the new architecture."""
    # Load environment variables
    load_dotenv()
    
    # Get API key (adjust for your provider)
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Please set GEMINI_API_KEY or OPENAI_API_KEY in your environment")
        return
    
    # Determine provider based on available key
    provider = "gemini" if os.getenv("GEMINI_API_KEY") else "openai"
    
    print(f"Using {provider} provider")
    
    # Example 1: Using individual components
    print("\n=== Example 1: Using Individual Components ===")
    
    # Create all components
    image_analyzer, progress_generator, memory_manager = create_complete_system(
        provider=provider,
        api_key=api_key,
        memory_file="new_architecture_memory.json"
    )
    
    # Path to your image folder (adjust as needed)
    image_folder = "src/progress_monitoring/video_sampler/img_data/day1"
    
    if os.path.exists(image_folder):
        # Get project context from memory
        project_memory = memory_manager.get_project_memory()
        print(f"Project memory loaded: {project_memory.get('total_records', 0)} records")
        
        # Step 1: Analyze images
        print("\nStep 1: Analyzing images...")
        analysis_result = image_analyzer.analyze_images_in_folder(
            image_folder_path=image_folder,
            project_context=project_memory
        )
        
        if analysis_result["status"] == "success":
            print(f"✓ Analyzed {analysis_result['images_processed']} images")
            print(f"Analysis preview: {analysis_result['analysis_text'][:200]}...")
            
            # Step 2: Generate progress report
            print("\nStep 2: Generating progress report...")
            from datetime import datetime
            date = datetime.now().strftime("%Y-%m-%d")
            
            progress_report = progress_generator.generate_progress_report(
                analysis_content=analysis_result["analysis_text"],
                memory_metadata=project_memory,
                date=date,
                image_folder_path=image_folder,
                day_number=1
            )
            
            if progress_report["status"] == "success":
                print("✓ Progress report generated successfully")
                progress_data = progress_report["progress_data"]
                print(f"Current phase: {progress_data.get('current_phase', 'Unknown')}")
                print(f"Overall progress: {progress_data.get('overall_progress_percentage', 0)}%")
                print(f"Key accomplishments: {len(progress_data.get('key_accomplishments', []))}")
                
                # Step 3: Store in memory with embeddings
                print("\nStep 3: Storing in enhanced memory...")
                record_id = memory_manager.store_progress_report(
                    date=date,
                    image_folder_path=image_folder,
                    analysis_content=analysis_result["analysis_text"],
                    progress_report=progress_data,
                    day_number=1
                )
                print(f"✓ Stored with ID: {record_id}")
                
                # Step 4: Demonstrate search functionality
                print("\nStep 4: Demonstrating vector search...")
                search_results = memory_manager.search_similar_reports(
                    query="construction progress foundation",
                    limit=3
                )
                print(f"✓ Found {len(search_results)} similar reports")
                
                for i, result in enumerate(search_results[:2]):
                    print(f"  Result {i+1}: {result.get('date', 'Unknown date')} - "
                          f"Score: {result.get('similarity_score', 'N/A')}")
            else:
                print(f"✗ Progress report generation failed: {progress_report.get('error')}")
        else:
            print(f"✗ Image analysis failed: {analysis_result.get('error')}")
    else:
        print(f"Image folder not found: {image_folder}")
    
    # Example 2: Using convenience function
    print("\n=== Example 2: Using Convenience Function ===")
    
    if os.path.exists(image_folder):
        complete_result = analyze_construction_progress(
            provider=provider,
            api_key=api_key,
            folder_path=image_folder,
            memory_file="new_architecture_memory.json"
        )
        
        if complete_result["status"] == "success":
            print("✓ Complete analysis finished successfully")
            print(f"Analysis date: {complete_result['date']}")
            print(f"Memory updated: {complete_result['memory_updated']}")
        else:
            print(f"✗ Complete analysis failed: {complete_result.get('error')}")
    
    # Example 3: Daily progression analysis
    print("\n=== Example 3: Daily Progression Analysis ===")
    
    img_data_path = "src/progress_monitoring/video_sampler/img_data"
    if os.path.exists(img_data_path):
        # Analyze multiple days
        daily_analyses = image_analyzer.analyze_daily_progression(
            img_data_path=img_data_path,
            project_context=project_memory
        )
        
        if daily_analyses["status"] == "success":
            print(f"✓ Analyzed {daily_analyses['total_days_analyzed']} days")
            
            # Generate progression report
            progression_report = progress_generator.generate_daily_progression_report(
                daily_analyses=daily_analyses["daily_analyses"],
                memory_metadata=project_memory
            )
            
            if progression_report["status"] == "success":
                print("✓ Daily progression report generated")
                summary = progression_report["overall_summary"]
                print(f"Final progress: {summary.get('final_progress_percentage', 0)}%")
                print(f"Progress trend: {summary.get('progress_trend', 'Unknown')}")
        else:
            print(f"✗ Daily progression analysis failed: {daily_analyses.get('error')}")
    
    print("\n=== Architecture Summary ===")
    print("✓ ImageAnalyzer: Focuses solely on image analysis")
    print("✓ ProgressReportGenerator: Creates structured progress reports using LLM")
    print("✓ Enhanced MemoryManager: Uses Qdrant for vector storage and semantic search")
    print("✓ All components work together seamlessly")


if __name__ == "__main__":
    main() 