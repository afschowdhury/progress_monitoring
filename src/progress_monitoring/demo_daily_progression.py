#!/usr/bin/env python3
"""
Demo script for daily progression analysis.
This script analyzes all day folders in the img_data directory and generates reports for each day.
"""
import json
import os
from datetime import datetime
from config import AnalysisConfig
from analyzer import ConstructionSiteAnalyzer


def main():
    """Run daily progression analysis demo."""
    print("=== Construction Site Daily Progression Analysis Demo ===\n")
    
    # Setup configuration
    config = AnalysisConfig()
    
    # Path to the img_data folder containing day folders
    img_data_path = "video_sampler/img_data"
    
    # Check if path exists
    if not os.path.exists(img_data_path):
        print(f"Error: Image data path '{img_data_path}' not found.")
        print("Please ensure the img_data folder with day1, day2, etc. exists.")
        return
    
    # Initialize analyzer
    analyzer = ConstructionSiteAnalyzer(config)
    
    # Set project start date (optional - will default to current date if not provided)
    project_start_date = "2025-01-01"  # You can change this to your actual project start date
    
    print(f"Analyzing day folders in: {img_data_path}")
    print(f"Project start date: {project_start_date}")
    print("-" * 50)
    
    # Run daily progression analysis
    results = analyzer.analyze_daily_progression(img_data_path, project_start_date)
    
    # Display results
    if results["status"] == "success":
        print(f"✅ Analysis completed successfully!")
        print(f"📅 Total days analyzed: {results['total_days_analyzed']}")
        print(f"🏗️ Project start date: {results['project_start_date']}")
        print("\n" + "=" * 60)
        
        # Display summary for each day
        for day_key, day_report in results["daily_reports"].items():
            day_num = day_report["day_number"]
            date = day_report["analysis_date"]
            images = day_report["images_processed"]
            
            print(f"\n📊 DAY {day_num} SUMMARY ({date})")
            print("-" * 40)
            print(f"Images processed: {images}")
            
            if day_report.get("progress_report"):
                progress = day_report["progress_report"]
                print(f"Current phase: {progress.get('current_phase', 'Unknown')}")
                print(f"Overall progress: {progress.get('overall_progress_percentage', 0)}%")
                print(f"Daily progress: {progress.get('daily_progress_percentage', 0)}%")
                
                if progress.get('key_accomplishments'):
                    print("Key accomplishments:")
                    for acc in progress['key_accomplishments'][:3]:  # Show top 3
                        print(f"  • {acc}")
            
            # Show first 200 characters of analysis
            description = day_report.get("daily_description", "")
            if description:
                print(f"\nAnalysis preview: {description[:200]}...")
        
        # Display final project state
        print("\n" + "=" * 60)
        print("🎯 FINAL PROJECT STATE")
        print("-" * 40)
        final_state = results["final_memory_state"]
        print(f"Current phase: {final_state.get('current_phase', 'Unknown')}")
        print(f"Overall progress: {final_state.get('overall_progress_percentage', 0)}%")
        print(f"Total days: {final_state.get('total_days_analyzed', 0)}")
        
        if final_state.get('key_milestones'):
            print(f"Key milestones: {len(final_state['key_milestones'])}")
            for milestone in final_state['key_milestones'][-3:]:  # Show last 3
                print(f"  • {milestone.get('description', 'N/A')} ({milestone.get('progress_percentage', 0)}%)")
        
        # Save detailed results to file
        output_file = f"daily_progression_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Detailed results saved to: {output_file}")
        print("\n✨ Daily progression analysis complete!")
        
    else:
        print(f"❌ Analysis failed: {results.get('error', 'Unknown error')}")


if __name__ == "__main__":
    main() 