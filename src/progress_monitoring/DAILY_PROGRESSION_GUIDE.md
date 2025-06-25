# Daily Progression Analysis Guide

This guide explains how to use the new daily progression analysis feature that analyzes construction progress across multiple days by comparing day-by-day changes.

## Overview

The daily progression analysis feature allows you to:
- Analyze construction images organized in day folders (day1, day2, day3, etc.)
- Generate comparative reports for each day showing progress from the previous day
- Track cumulative progress and identify trends over time
- Update project memory with comprehensive daily reports

## Folder Structure

Your image data should be organized as follows:

```
img_data/
├── day1/
│   ├── frame_1_00m00s.jpg
│   ├── frame_2_00m48s.jpg
│   └── ...
├── day2/
│   ├── frame_1_04m00s.jpg
│   ├── frame_2_04m24s.jpg
│   └── ...
├── day3/
│   └── ...
└── day5/
    └── ...
```

## Usage Methods

### 1. Using the CLI

```bash
# Basic daily progression analysis
python -m progress_monitoring.cli \
  --provider gemini \
  --api-key YOUR_GEMINI_API_KEY \
  --daily-progression ./src/progress_monitoring/video_sampler/img_data \
  --start-date 2025-01-01

# With OpenAI and custom output
python -m progress_monitoring.cli \
  --provider openai \
  --api-key YOUR_OPENAI_API_KEY \
  --daily-progression ./src/progress_monitoring/video_sampler/img_data \
  --start-date 2025-01-01 \
  --output daily_analysis_results.json \
  --verbose

# Using custom prompts
python -m progress_monitoring.cli \
  --provider gemini \
  --api-key YOUR_GEMINI_API_KEY \
  --daily-progression ./src/progress_monitoring/video_sampler/img_data \
  --start-date 2025-01-01 \
  --prompts-dir ./custom_prompts
```

### 2. Using the Demo Script

```bash
# Run the demo script (edit the script to set your API key)
cd src/progress_monitoring
python demo_daily_progression.py
```

### 3. Using Python Code

```python
from progress_monitoring.config import AnalysisConfig
from progress_monitoring.analyzer import ConstructionSiteAnalyzer

# Setup configuration
config = AnalysisConfig()
config.model_provider = config.ModelProvider.GEMINI
config.gemini_api_key = "your_api_key_here"

# Initialize analyzer
analyzer = ConstructionSiteAnalyzer(config)

# Run daily progression analysis
results = analyzer.analyze_daily_progression(
    img_data_path="./video_sampler/img_data",
    project_start_date="2025-01-01"
)

# Process results
if results["status"] == "success":
    print(f"Analyzed {results['total_days_analyzed']} days")
    for day_key, day_report in results["daily_reports"].items():
        print(f"Day {day_report['day_number']}: {day_report['analysis_date']}")
```

## Features

### Daily Comparison Analysis
- **Day-by-Day Comparison**: Each day is analyzed in context of the previous day's progress
- **Change Detection**: Identifies specific changes, additions, and modifications
- **Progress Tracking**: Measures both daily and cumulative progress
- **Trend Analysis**: Identifies patterns in construction phases and timeline

### Comprehensive Reporting
Each day generates a detailed report including:
- Daily activities and work performed
- Progress comparison with previous day
- Key changes and construction elements
- Safety observations and quality assessment
- Equipment and personnel analysis
- Timeline assessment

### Memory Management
- **Cumulative Memory**: Builds comprehensive project memory across all days
- **Milestone Tracking**: Automatically identifies and records key milestones
- **Progress Continuity**: Maintains context from previous days for better analysis

## Output Format

The daily progression analysis returns a comprehensive result with:

```json
{
  "analysis_type": "daily_progression",
  "total_days_analyzed": 5,
  "project_start_date": "2025-01-01",
  "daily_reports": {
    "day_1": {
      "day_number": 1,
      "analysis_date": "2025-01-01",
      "images_processed": 6,
      "daily_description": "Detailed analysis...",
      "progress_report": {
        "current_phase": "Foundation",
        "overall_progress_percentage": 10,
        "daily_progress_percentage": 5,
        "key_accomplishments": [...],
        "identified_issues": [...],
        "next_phase_indicators": [...],
        "estimated_timeline_status": "On Schedule",
        "critical_path_items": [...]
      },
      "status": "success"
    },
    "day_2": { ... },
    ...
  },
  "final_memory_state": {
    "project_start_date": "2025-01-01",
    "total_days_analyzed": 5,
    "current_phase": "Foundation",
    "overall_progress_percentage": 45,
    "key_milestones": [...]
  },
  "status": "success"
}
```

## Configuration

### API Keys
Set your API keys in the configuration:
- **Gemini**: Set `config.gemini_api_key`
- **OpenAI**: Set `config.openai_api_key`

### Custom Prompts
You can customize the analysis prompts by:
1. Creating custom TOML files in a prompts directory
2. Using the `daily_comparison_analysis` prompt template
3. Specifying the prompts directory in your configuration

### Memory File
The system maintains a memory file (default: `construction_memory.txt`) that stores:
- Project timeline and milestones
- Daily report summaries
- Progress tracking data
- Historical context for analysis

## Tips for Best Results

1. **Consistent Image Quality**: Ensure images are clear and well-lit
2. **Similar Viewpoints**: Try to capture similar angles across days for better comparison
3. **Adequate Coverage**: Include multiple angles and views of the construction site
4. **Chronological Order**: Ensure day folders are numbered sequentially
5. **Regular Intervals**: Analyze at consistent time intervals for better trend analysis

## Troubleshooting

### Common Issues
- **No day folders found**: Ensure folders are named `day1`, `day2`, etc.
- **No images in folders**: Check that image files are in supported formats (jpg, png, etc.)
- **API errors**: Verify your API keys are correct and have sufficient quota
- **Memory issues**: Large image sets may require adjusting memory settings

### Error Messages
- `No day folders found`: Check folder naming convention
- `No images could be prepared`: Verify image formats and file accessibility
- `Analysis failed for day X`: Check individual day folder contents and API connectivity

## Examples

See the `demo_daily_progression.py` script for a complete working example that demonstrates all features of the daily progression analysis system. 