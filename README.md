# Construction Progress Monitoring

An AI-powered tool for analyzing construction site progress using computer vision and large language models. This tool can analyze daily construction site images to track progress, identify milestones, and generate comprehensive reports.

## Features

- **Multi-Model Support**: Works with Google Gemini and OpenAI GPT-4 Vision
- **Image Processing**: Automatically processes and prepares images for AI analysis
- **Progress Tracking**: Maintains historical data and tracks project milestones
- **Structured Reports**: Generates detailed progress reports with key metrics
- **Memory Management**: Persistent storage of project history and progress data
- **Flexible Configuration**: Customizable settings for different project needs
- **CLI Interface**: Easy-to-use command-line interface
- **Modular Design**: Reusable components for integration into larger systems
- **Prompt Management**: Configurable prompts with TOML files for customization
- **Specialized Analysis**: Support for safety, quality, and timeline-focused prompts

## Installation

### Prerequisites

- Python 3.12 or higher
- API keys for either Google Gemini or OpenAI

### Install the Package

```bash
# Clone the repository
git clone <repository-url>
cd progress-monitoring

# Install using pip
pip install -e .

# Or install using poetry
poetry install
```

### Install Dependencies

```bash
pip install google-genai openai python-dotenv
```

## Quick Start

### 1. Set up API Keys

Set your API keys as environment variables:

```bash
export GEMINI_API_KEY="your-gemini-api-key"
export OPENAI_API_KEY="your-openai-api-key"
```

### 2. Prepare Your Images

Organize your construction site images in a folder structure like:

```
construction_images/
├── day1/
│   ├── image1.jpg
│   ├── image2.jpg
│   └── ...
├── day2/
│   ├── image1.jpg
│   └── ...
└── ...
```

### 3. Run Analysis

#### Using the CLI

```bash
# Analyze with Gemini
python -m progress_monitoring.cli \
    --provider gemini \
    --api-key $GEMINI_API_KEY \
    --folder ./construction_images \
    --output results.json

# Analyze with OpenAI
python -m progress_monitoring.cli \
    --provider openai \
    --api-key $OPENAI_API_KEY \
    --folder ./construction_images \
    --model gpt-4o \
    --verbose

# Use custom prompts
python -m progress_monitoring.cli \
    --provider gemini \
    --api-key $GEMINI_API_KEY \
    --folder ./construction_images \
    --prompts-dir ./custom_prompts

# List available prompts
python -m progress_monitoring.cli --list-prompts --prompts-dir ./custom_prompts
```

#### Using Python

```python
from progress_monitoring import analyze_construction_progress

# Analyze with Gemini
result = analyze_construction_progress(
    provider="gemini",
    api_key="your-gemini-api-key",
    folder_path="./construction_images",
    model_name="gemini-2.5-pro"
)

print(f"Current Phase: {result['progress_report']['current_phase']}")
print(f"Overall Progress: {result['progress_report']['overall_progress_percentage']}%")
```

## Prompt Management

The system now supports configurable prompts using TOML files, allowing you to customize the AI analysis behavior for different use cases.

### Creating Custom Prompts

Create TOML files in a directory with your custom prompts:

```toml
# custom_analysis.toml
[custom_analysis]
type = "analysis"
model_name = "gemini-2.5-pro"
temperature = 0.8
max_tokens = 3000
description = "Custom analysis prompt with higher temperature"

template = """
You are a senior construction project manager analyzing images taken on ${analysis_date}.

PROJECT CONTEXT:
- Current phase: ${current_phase}
- Days analyzed: ${total_days_analyzed}
- Overall progress: ${overall_progress_percentage}%

${historical_context}

Please provide a detailed analysis focusing on:
1. Work Progress: What construction activities were completed?
2. Quality Assessment: How does work quality compare to standards?
3. Safety Review: Any safety concerns or positive practices?
4. Resource Utilization: How efficiently are resources being used?

Provide specific, actionable insights with recommendations.
"""

variables = { current_phase = "Unknown", total_days_analyzed = 0, overall_progress_percentage = 0, analysis_date = "Today", historical_context = "" }
```

### Using Custom Prompts

```python
from progress_monitoring import create_analyzer_with_custom_prompts

# Create analyzer with custom prompts
analyzer = create_analyzer_with_custom_prompts(
    provider="gemini",
    api_key="your-api-key",
    prompts_dir="./custom_prompts",
    model_name="gemini-2.5-pro"
)

# Run analysis with custom prompts
result = analyzer.analyze_construction_site("./construction_images")
```

### Prompt Types

The system supports different types of prompts:

- **analysis**: Main construction site analysis
- **progress_assessment**: Structured progress reporting
- **safety_review**: Focused safety assessment
- **quality_assessment**: Quality control analysis
- **timeline_analysis**: Schedule and timeline analysis

### Prompt Configuration Options

Each prompt can be configured with:

- `model_name`: AI model to use
- `temperature`: Creativity level (0.0-1.0)
- `max_tokens`: Maximum response length
- `top_p`: Nucleus sampling parameter
- `frequency_penalty`: Penalty for repetitive content
- `presence_penalty`: Penalty for new topics
- `system_message`: Optional system message
- `variables`: Default template variables

## Usage Examples

### Basic Analysis

```python
from progress_monitoring import analyze_construction_progress

result = analyze_construction_progress(
    provider="gemini",
    api_key="your-api-key",
    folder_path="./images"
)

if result['status'] == 'success':
    progress = result['progress_report']
    print(f"Phase: {progress['current_phase']}")
    print(f"Progress: {progress['overall_progress_percentage']}%")
    print(f"Accomplishments: {progress['key_accomplishments']}")
```

### Custom Configuration with Prompts

```python
from progress_monitoring import (
    ConstructionSiteAnalyzer,
    AnalysisConfig,
    ModelProvider,
    PromptSettings
)

# Configure prompt settings
prompt_settings = PromptSettings(
    prompts_dir="./custom_prompts",
    default_analysis_prompt="custom_analysis",
    default_progress_prompt="progress_assessment"
)

config = AnalysisConfig(
    model_provider=ModelProvider.GEMINI,
    model_name="gemini-2.5-pro",
    api_key="your-api-key",
    memory_file_path="my_project_memory.json",
    max_images_per_request=15,
    max_file_size_mb=10,
    enable_detailed_logging=True,
    prompt_settings=prompt_settings
)

analyzer = ConstructionSiteAnalyzer(config)
result = analyzer.analyze_construction_site("./construction_images")
```

### Prompt Management

```python
from progress_monitoring import PromptManager

# Initialize prompt manager
prompt_manager = PromptManager("./custom_prompts")

# List available prompts
for prompt_name in prompt_manager.list_prompts():
    info = prompt_manager.get_prompt_info(prompt_name)
    print(f"{info['name']}: {info['description']}")

# Render a prompt with variables
variables = {
    "analysis_date": "2025-01-15",
    "current_phase": "Foundation Work",
    "total_days_analyzed": 5,
    "overall_progress_percentage": 15
}

rendered_prompt = prompt_manager.render_prompt("custom_analysis", variables)
print(rendered_prompt)
```

### Memory Management

```python
from progress_monitoring import MemoryManager

# Read project memory
memory_manager = MemoryManager("project_memory.json")
memory_data = memory_manager.read_memory()

print(f"Project start: {memory_data['project_start_date']}")
print(f"Days analyzed: {memory_data['total_days_analyzed']}")
print(f"Current phase: {memory_data['current_phase']}")
print(f"Overall progress: {memory_data['overall_progress_percentage']}%")
```

## Project Structure

```
progress_monitoring/
├── src/progress_monitoring/
│   ├── __init__.py              # Main package exports
│   ├── config.py                # Configuration classes
│   ├── analyzer.py              # Main analyzer class
│   ├── factory.py               # Factory functions
│   ├── cli.py                   # Command-line interface
│   ├── image_processor.py       # Image processing utilities
│   ├── memory_manager.py        # Memory management
│   ├── prompts/                 # Prompt management system
│   │   ├── __init__.py
│   │   ├── config.py            # Prompt configuration classes
│   │   ├── manager.py           # Prompt manager
│   │   └── templates/           # Default prompt templates
│   │       ├── analysis.toml
│   │       ├── progress_assessment.toml
│   │       └── specialized.toml
│   └── providers/               # AI provider implementations
│       ├── __init__.py
│       ├── base.py              # Abstract base class
│       ├── gemini_provider.py   # Google Gemini implementation
│       ├── openai_provider.py   # OpenAI implementation
│       └── factory.py           # Provider factory
├── examples/
│   ├── __init__.py
│   ├── basic_usage.py           # Basic usage examples
│   └── prompt_management_example.py  # Prompt management examples
├── tests/                       # Test files
├── pyproject.toml              # Project configuration
└── README.md                   # This file
```

## Configuration

### AnalysisConfig

The main configuration class with the following options:

- `model_provider`: AI provider (GEMINI or OPENAI)
- `model_name`: Specific model to use
- `api_key`: API key for the provider
- `memory_file_path`: Path to memory file
- `max_images_per_request`: Maximum images per analysis
- `max_file_size_mb`: Maximum file size for inline processing
- `enable_detailed_logging`: Enable verbose logging
- `prompt_settings`: Prompt management configuration

### PromptSettings

Configuration for prompt management:

- `prompts_dir`: Directory containing custom prompt TOML files
- `default_analysis_prompt`: Name of default analysis prompt
- `default_progress_prompt`: Name of default progress prompt
- `enable_prompt_override`: Allow prompt overrides
- `custom_prompts`: Dictionary of custom prompt overrides

### Supported Image Formats

- JPEG (.jpg, .jpeg)
- PNG (.png)
- WebP (.webp)
- HEIC (.heic, .heif)

## Output Format

The analysis returns a structured dictionary with:

```python
{
    "analysis_date": "2024-01-15",
    "model_used": "gemini/gemini-2.5-pro",
    "images_processed": 6,
    "daily_description": "Detailed analysis text...",
    "progress_report": {
        "current_phase": "Foundation Work",
        "overall_progress_percentage": 25,
        "daily_progress_percentage": 5,
        "key_accomplishments": ["Concrete poured", "Rebar installed"],
        "identified_issues": ["Weather delay"],
        "next_phase_indicators": ["Foundation curing"],
        "estimated_timeline_status": "On Schedule",
        "critical_path_items": ["Foundation completion"]
    },
    "updated_memory": {
        "project_start_date": "2024-01-10",
        "total_days_analyzed": 5,
        "current_phase": "Foundation Work",
        "overall_progress_percentage": 25,
        "recent_milestones": [...]
    },
    "status": "success"
}
```

## API Reference

### Main Functions

- `analyze_construction_progress()`: Convenience function for quick analysis
- `create_gemini_analyzer()`: Create Gemini-based analyzer
- `create_openai_analyzer()`: Create OpenAI-based analyzer

### Main Classes

- `ConstructionSiteAnalyzer`: Main analysis orchestrator
- `ImageProcessor`: Image file processing and preparation
- `MemoryManager`: Project memory and historical data management
- `AnalysisConfig`: Configuration management

### Provider Classes

- `AIProvider`: Abstract base class for AI providers
- `GeminiProvider`: Google Gemini implementation
- `OpenAIProvider`: OpenAI implementation

## Development

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black src/ tests/
flake8 src/ tests/
```

### Type Checking

```bash
mypy src/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:

1. Check the examples in the `examples/` directory
2. Review the CLI help: `python -m progress_monitoring.cli --help`
3. Open an issue on GitHub

## Roadmap

- [ ] Support for additional AI providers (Claude, etc.)
- [ ] Web interface for analysis results
- [ ] Integration with project management tools
- [ ] Advanced progress prediction algorithms
- [ ] Support for video analysis
- [ ] Mobile app for on-site analysis
