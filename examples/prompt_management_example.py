"""
Example demonstrating the new prompt management system.

This example shows how to:
1. Use custom prompt TOML files
2. Create analyzers with custom prompt configurations
3. List and inspect available prompts
4. Override default prompts
"""

import os
import tempfile
from pathlib import Path

from progress_monitoring import (
    create_analyzer_with_custom_prompts,
    PromptManager,
    PromptConfig,
    PromptType
)


def create_example_prompt_files():
    """Create example TOML prompt files for demonstration."""
    
    # Create a temporary directory for our example prompts
    temp_dir = tempfile.mkdtemp(prefix="example_prompts_")
    
    # Example 1: Custom analysis prompt
    analysis_prompt = f"""[custom_analysis]
type = "analysis"
model_name = "gemini-2.5-pro"
temperature = 0.8
max_tokens = 3000
description = "Custom analysis prompt with higher temperature for more creative responses"

template = '''
You are a senior construction project manager with 20+ years of experience analyzing construction site images taken on ${analysis_date}.

PROJECT CONTEXT:
- Current phase: ${current_phase}
- Days analyzed: ${total_days_analyzed}
- Overall progress: ${overall_progress_percentage}%
- Project start: ${project_start_date}

${historical_context}

Please provide a detailed analysis focusing on:

1. **Work Progress**: What specific construction activities were completed today?
2. **Quality Assessment**: How does the work quality compare to industry standards?
3. **Safety Review**: Any safety concerns or positive safety practices observed?
4. **Resource Utilization**: How efficiently are equipment and personnel being used?
5. **Schedule Impact**: How does today's work affect the overall project timeline?
6. **Risk Assessment**: Any potential issues or delays that could impact the project?

Provide specific, actionable insights with recommendations for project management.
'''

variables = {{ current_phase = "Unknown", total_days_analyzed = 0, overall_progress_percentage = 0, project_start_date = "Unknown", analysis_date = "Today", historical_context = "" }}
"""
    
    # Example 2: Specialized safety prompt
    safety_prompt = f"""[safety_focus]
type = "safety_review"
model_name = "gemini-2.5-pro"
temperature = 0.2
max_tokens = 2000
description = "Focused safety analysis with low temperature for consistent results"

template = '''
You are a certified construction safety inspector conducting a safety assessment.

ANALYSIS DATE: ${analysis_date}
SITE: ${site_context}

Conduct a comprehensive safety evaluation based on the provided images:

SAFETY EVALUATION CHECKLIST:
1. **PPE Compliance**: Are workers wearing appropriate personal protective equipment?
2. **Site Hazards**: Identify any visible safety hazards or dangerous conditions
3. **Equipment Safety**: Is equipment being operated safely and properly maintained?
4. **Site Organization**: Is the work area organized to minimize safety risks?
5. **Emergency Access**: Are emergency exits and access routes clear and accessible?
6. **Weather Conditions**: How do current weather conditions affect safety?
7. **Compliance Issues**: Any obvious violations of safety regulations or protocols?

For each category, provide:
- Risk Level: Low/Medium/High/Critical
- Specific observations
- Immediate actions required (if any)
- Recommendations for improvement

Format your response as a structured safety report.
'''

variables = {{ analysis_date = "Today", site_context = "Construction site" }}
"""
    
    # Write the prompt files
    with open(os.path.join(temp_dir, "custom_analysis.toml"), "w") as f:
        f.write(analysis_prompt)
    
    with open(os.path.join(temp_dir, "safety_focus.toml"), "w") as f:
        f.write(safety_prompt)
    
    return temp_dir


def demonstrate_prompt_management():
    """Demonstrate the prompt management features."""
    
    print("=== Prompt Management Example ===\n")
    
    # Create example prompt files
    prompts_dir = create_example_prompt_files()
    print(f"Created example prompts in: {prompts_dir}\n")
    
    # Initialize prompt manager
    prompt_manager = PromptManager(prompts_dir)
    
    # List available prompts
    print("Available prompts:")
    print("=" * 50)
    for prompt_name in prompt_manager.list_prompts():
        info = prompt_manager.get_prompt_info(prompt_name)
        if info:
            print(f"\n{info['name']}:")
            print(f"  Type: {info['type']}")
            print(f"  Model: {info['model_name']}")
            print(f"  Temperature: {info['temperature']}")
            print(f"  Max Tokens: {info['max_tokens']}")
            print(f"  Description: {info['description']}")
    
    # Demonstrate prompt rendering
    print("\n" + "=" * 50)
    print("Prompt Rendering Example:")
    print("=" * 50)
    
    variables = {
        "analysis_date": "2025-01-15",
        "current_phase": "Foundation Work",
        "total_days_analyzed": 5,
        "overall_progress_percentage": 15,
        "project_start_date": "2025-01-10",
        "historical_context": "Previous days focused on site preparation and excavation."
    }
    
    rendered_prompt = prompt_manager.render_prompt("custom_analysis", variables)
    if rendered_prompt:
        print("Rendered 'custom_analysis' prompt:")
        print("-" * 30)
        print(rendered_prompt[:500] + "..." if len(rendered_prompt) > 500 else rendered_prompt)
    
    # Demonstrate creating analyzer with custom prompts
    print("\n" + "=" * 50)
    print("Creating Analyzer with Custom Prompts:")
    print("=" * 50)
    
    # Note: This is a demonstration - you would need actual API keys to run analysis
    try:
        analyzer = create_analyzer_with_custom_prompts(
            provider="gemini",
            api_key="your-api-key-here",  # Replace with actual API key
            prompts_dir=prompts_dir,
            model_name="gemini-2.5-pro"
        )
        print("✓ Successfully created analyzer with custom prompts")
        print(f"  Default analysis prompt: {analyzer.config.prompt_settings.default_analysis_prompt}")
        print(f"  Prompts directory: {analyzer.config.prompt_settings.prompts_dir}")
        
    except Exception as e:
        print(f"✗ Could not create analyzer (expected without API key): {e}")
    
    # Clean up
    import shutil
    shutil.rmtree(prompts_dir)
    print(f"\nCleaned up temporary directory: {prompts_dir}")


def demonstrate_prompt_types():
    """Demonstrate different prompt types."""
    
    print("\n=== Prompt Types Example ===\n")
    
    # Create a prompt manager with built-in prompts
    prompt_manager = PromptManager()
    
    # Show prompts by type
    for prompt_type in PromptType:
        prompts = prompt_manager.get_prompts_by_type(prompt_type)
        if prompts:
            print(f"{prompt_type.value.upper()} prompts:")
            for prompt in prompts:
                print(f"  - {prompt.name}: {prompt.description}")
            print()


if __name__ == "__main__":
    demonstrate_prompt_management()
    demonstrate_prompt_types()
    
    print("\n=== Usage Tips ===")
    print("1. Create TOML files in a directory for your custom prompts")
    print("2. Use the --prompts-dir argument with CLI to use custom prompts")
    print("3. Use create_analyzer_with_custom_prompts() for programmatic access")
    print("4. Use PromptManager to inspect and manage prompts")
    print("5. Templates support variable substitution using ${variable_name} syntax") 