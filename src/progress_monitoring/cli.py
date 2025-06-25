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


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze construction site progress using AI vision models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze with Gemini
  python -m progress_monitoring.cli --provider gemini --api-key YOUR_KEY --folder ./images
  
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
    
    # Validate required arguments for analysis
    if not args.provider or not args.api_key or not args.folder:
        parser.error("--provider, --api-key, and --folder are required for analysis")
    
    # Validate folder exists
    if not os.path.exists(args.folder):
        print(f"Error: Folder '{args.folder}' does not exist", file=sys.stderr)
        sys.exit(1)
    
    # Set up logging if verbose
    if args.verbose:
        import logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    try:
        print(f"Analyzing construction site images in: {args.folder}")
        print(f"Using provider: {args.provider}")
        if args.prompts_dir:
            print(f"Using custom prompts from: {args.prompts_dir}")
        
        # Run analysis
        result = analyze_construction_progress(
            provider=args.provider,
            api_key=args.api_key,
            folder_path=args.folder,
            model_name=args.model,
            memory_file=args.memory_file,
            prompts_dir=args.prompts_dir
        )
        
        # Handle output
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
        
        # Print full analysis if not saving to file
        elif args.verbose:
            print(f"\nFull Analysis:")
            print("-" * 30)
            print(result.get('daily_description', 'No analysis available'))
        
    except KeyboardInterrupt:
        print("\nAnalysis interrupted by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main() 