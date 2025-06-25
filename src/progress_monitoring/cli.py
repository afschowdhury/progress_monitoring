#!/usr/bin/env python3
"""
Command-line interface for construction progress monitoring.
"""
import argparse
import json
import os
import sys
from pathlib import Path

from .factory import analyze_construction_progress
from .prompts import PromptManager
from .config import AnalysisConfig
from .analyzer import ConstructionSiteAnalyzer


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze construction site progress using AI vision models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze single folder with Gemini
  python -m progress_monitoring.cli --provider gemini --api-key YOUR_KEY --folder ./images
  
  # Analyze daily progression (day1, day2, etc. folders)
  python -m progress_monitoring.cli --provider gemini --api-key YOUR_KEY --daily-progression ./img_data --start-date 2025-01-01
  
  # Analyze with OpenAI
  python -m progress_monitoring.cli --provider openai --api-key YOUR_KEY --folder ./images --model gpt-4o
  
  # Use custom prompts
  python -m progress_monitoring.cli --provider gemini --api-key YOUR_KEY --folder ./images --prompts-dir ./custom_prompts
  
  # List available prompts
  python -m progress_monitoring.cli --list-prompts --prompts-dir ./custom_prompts
  
  # Save results to file
  python -m progress_monitoring.cli --provider gemini --api-key YOUR_KEY --folder ./images --output results.json
        """
    )
    
    parser.add_argument(
        "--provider", 
        choices=["gemini", "openai"], 
        help="AI provider to use (gemini or openai)"
    )
    
    parser.add_argument(
        "--api-key", 
        help="API key for the selected provider"
    )
    
    parser.add_argument(
        "--folder", 
        help="Path to folder containing construction site images"
    )
    
    parser.add_argument(
        "--daily-progression",
        help="Path to folder containing day1, day2, etc. subfolders for daily progression analysis"
    )
    
    parser.add_argument(
        "--start-date",
        help="Project start date in YYYY-MM-DD format (for daily progression analysis)"
    )
    
    parser.add_argument(
        "--model",
        help="Model name (defaults to provider-specific defaults)"
    )
    
    parser.add_argument(
        "--memory-file",
        default="construction_memory.txt",
        help="Path to memory file (default: construction_memory.txt)"
    )
    
    parser.add_argument(
        "--prompts-dir",
        help="Directory containing custom prompt TOML files"
    )
    
    parser.add_argument(
        "--list-prompts",
        action="store_true",
        help="List available prompts and exit"
    )
    
    parser.add_argument(
        "--output",
        help="Output file for results (JSON format)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Handle prompt listing
    if args.list_prompts:
        try:
            prompt_manager = PromptManager(args.prompts_dir)
            prompts = prompt_manager.list_prompts()
            
            if not prompts:
                print("No prompts found.")
                return
            
            print("Available prompts:")
            print("=" * 50)
            for prompt_name in prompts:
                info = prompt_manager.get_prompt_info(prompt_name)
                if info:
                    print(f"\n{info['name']}:")
                    print(f"  Type: {info['type']}")
                    print(f"  Model: {info['model_name']}")
                    print(f"  Temperature: {info['temperature']}")
                    if info['description']:
                        print(f"  Description: {info['description']}")
        except Exception as e:
            print(f"Error listing prompts: {e}", file=sys.stderr)
            sys.exit(1)
        return
    
    # Validate required arguments
    if not args.provider or not args.api_key:
        parser.error("--provider and --api-key are required")
    
    if not args.folder and not args.daily_progression:
        parser.error("Either --folder or --daily-progression is required")
    
    if args.folder and args.daily_progression:
        parser.error("Use either --folder or --daily-progression, not both")
    
    # Validate folder exists
    folder_path = args.folder or args.daily_progression
    if not os.path.exists(folder_path):
        print(f"Error: Path '{folder_path}' does not exist", file=sys.stderr)
        sys.exit(1)
    
    # Set up logging if verbose
    if args.verbose:
        import logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    try:
        if args.daily_progression:
            # Run daily progression analysis
            print(f"Running daily progression analysis on: {args.daily_progression}")
            print(f"Using provider: {args.provider}")
            if args.start_date:
                print(f"Project start date: {args.start_date}")
            
            # Create config
            config = AnalysisConfig()
            
            # Override config with CLI args
            if args.provider == "gemini":
                config.model_provider = config.ModelProvider.GEMINI
                config.gemini_api_key = args.api_key
            else:
                config.model_provider = config.ModelProvider.OPENAI  
                config.openai_api_key = args.api_key
            
            if args.model:
                config.model_name = args.model
            
            if args.memory_file:
                config.memory_file_path = args.memory_file
                
            if args.prompts_dir:
                config.prompt_settings.prompts_dir = args.prompts_dir
            
            # Run analysis
            analyzer = ConstructionSiteAnalyzer(config)
            result = analyzer.analyze_daily_progression(args.daily_progression, args.start_date)
            
            # Handle output for daily progression
            if result.get("status") == "failed":
                print(f"Daily progression analysis failed: {result.get('error', 'Unknown error')}", file=sys.stderr)
                sys.exit(1)
            
            # Print daily progression summary
            print("\n" + "="*60)
            print("DAILY PROGRESSION ANALYSIS RESULTS")
            print("="*60)
            print(f"Total days analyzed: {result.get('total_days_analyzed')}")
            print(f"Project start date: {result.get('project_start_date')}")
            print(f"Status: {result.get('status')}")
            
            # Print summary for each day
            daily_reports = result.get('daily_reports', {})
            for day_key in sorted(daily_reports.keys(), key=lambda x: int(x.split('_')[1])):
                day_report = daily_reports[day_key]
                day_num = day_report.get('day_number')
                date = day_report.get('analysis_date')
                images = day_report.get('images_processed')
                
                print(f"\n📊 DAY {day_num} ({date})")
                print("-" * 40)
                print(f"Images processed: {images}")
                
                progress = day_report.get('progress_report', {})
                if progress:
                    print(f"Phase: {progress.get('current_phase', 'Unknown')}")
                    print(f"Overall progress: {progress.get('overall_progress_percentage', 0)}%")
                    print(f"Daily progress: {progress.get('daily_progress_percentage', 0)}%")
                    
                    accomplishments = progress.get('key_accomplishments', [])
                    if accomplishments:
                        print("Key accomplishments:")
                        for acc in accomplishments[:2]:  # Show top 2
                            print(f"  • {acc}")
            
            # Print final state
            final_state = result.get('final_memory_state', {})
            print(f"\n🎯 FINAL PROJECT STATE")
            print("-" * 40)
            print(f"Current phase: {final_state.get('current_phase', 'Unknown')}")
            print(f"Overall progress: {final_state.get('overall_progress_percentage', 0)}%")
            
        else:
            # Run single folder analysis
            print(f"Analyzing construction site images in: {args.folder}")
            print(f"Using provider: {args.provider}")
            if args.prompts_dir:
                print(f"Using custom prompts from: {args.prompts_dir}")
            
            result = analyze_construction_progress(
                provider=args.provider,
                api_key=args.api_key,
                folder_path=args.folder,
                model_name=args.model,
                memory_file=args.memory_file,
                prompts_dir=args.prompts_dir
            )
            
            # Handle output for single folder
            if result.get("status") == "failed":
                print(f"Analysis failed: {result.get('error', 'Unknown error')}", file=sys.stderr)
                sys.exit(1)
            
            # Print summary
            print("\n" + "="*50)
            print("ANALYSIS RESULTS")
            print("="*50)
            print(f"Date: {result.get('analysis_date')}")
            print(f"Model: {result.get('model_used')}")
            print(f"Images processed: {result.get('images_processed')}")
            print(f"Status: {result.get('status')}")
            
            # Print progress summary
            progress = result.get('progress_report', {})
            if progress:
                print(f"\nCurrent Phase: {progress.get('current_phase', 'Unknown')}")
                print(f"Overall Progress: {progress.get('overall_progress_percentage', 0)}%")
                print(f"Daily Progress: {progress.get('daily_progress_percentage', 0)}%")
                print(f"Timeline Status: {progress.get('estimated_timeline_status', 'Unknown')}")
            
            # Print key accomplishments
            accomplishments = progress.get('key_accomplishments', [])
            if accomplishments:
                print(f"\nKey Accomplishments:")
                for acc in accomplishments:
                    print(f"  • {acc}")
            
            # Print issues
            issues = progress.get('identified_issues', [])
            if issues:
                print(f"\nIdentified Issues:")
                for issue in issues:
                    print(f"  • {issue}")
        
        # Save to file if requested
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"\nFull results saved to: {args.output}")
        
        # Print full analysis if verbose and single folder
        elif args.verbose and args.folder:
            print(f"\nFull Analysis:")
            print("-" * 30)
            print(result.get('daily_description', 'No analysis available'))
        
    except KeyboardInterrupt:
        print("\nAnalysis interrupted by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error during analysis: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main() 