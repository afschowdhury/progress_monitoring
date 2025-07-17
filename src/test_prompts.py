#!/usr/bin/env python3
"""
Quick test to verify prompt templates are loading correctly.
"""

from progress_monitoring.prompts import PromptManager

def test_prompts():
    """Test that all required prompts are available."""
    print("Testing prompt templates...")
    
    # Initialize prompt manager
    prompt_manager = PromptManager("progress_monitoring/prompts/templates")
    
    # Test prompts that ImageAnalyzer needs
    required_prompts = [
        "image_analysis_gemini",
        "image_analysis_openai", 
        "daily_comparison_analysis",
        "daily_comparison_analysis_openai",
        "progress_assessment",
        "progress_assessment_openai"
    ]
    
    for prompt_name in required_prompts:
        try:
            # Test with dummy variables
            test_vars = {
                "project_context": "Test context",
                "previous_day_summary": "Test summary",
                "day_number": 1,
                "total_days": 5,
                "current_phase": "Foundation",
                "overall_progress_percentage": 25,
                "project_start_date": "2025-01-01",
                "previous_day_summary": "Previous day work",
                "analysis_text": "Test analysis",
                "total_days_analyzed": 1,
                "previous_progress": 20
            }
            
            result = prompt_manager.render_prompt(prompt_name, test_vars)
            if result:
                print(f"✅ {prompt_name}: OK")
            else:
                print(f"❌ {prompt_name}: Failed to render")
                
        except Exception as e:
            print(f"❌ {prompt_name}: Error - {e}")
    
    print("\nPrompt test completed!")

if __name__ == "__main__":
    test_prompts() 