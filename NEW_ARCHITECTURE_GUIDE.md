# New Architecture Guide

## Overview

The progress monitoring system has been redesigned with a modular architecture that separates concerns for better maintainability and scalability.

## Architecture Components

### 1. ImageAnalyzer
- **Purpose**: Analyzes images in folders and provides detailed descriptions
- **Responsibilities**: 
  - Process construction site images
  - Generate detailed daily analysis reports
  - Handle parallel processing for large image sets
  - Provide context-aware analysis using project information

### 2. ProgressReportGenerator
- **Purpose**: Generates structured progress reports from analysis content
- **Responsibilities**:
  - Create structured progress reports using LLM providers
  - Combine analysis content with memory metadata
  - Generate comprehensive daily progression reports
  - Provide JSON-structured output for further processing

### 3. Enhanced MemoryManager
- **Purpose**: Advanced memory management with vector database support
- **Features**:
  - Stores progress reports, analysis reports, dates, and image folder paths
  - Uses Qdrant vector database for semantic search
  - Generates embeddings for searchable content
  - Provides fallback to JSON storage when Qdrant is unavailable
  - Automatic summary generation for analysis and progress reports

## Installation & Setup

### 1. Install Dependencies

```bash
# Install the package with new dependencies
pip install -e .

# Or install specific dependencies
pip install qdrant-client sentence-transformers icecream
```

### 2. Set Up Qdrant (Optional but Recommended)

#### Option A: Docker (Recommended)
```bash
# Run Qdrant locally
docker run -p 6333:6333 qdrant/qdrant
```

#### Option B: Python Installation
```bash
pip install qdrant-client[local]
```

### 3. Environment Setup

Create a `.env` file with your API keys:
```env
GEMINI_API_KEY=your_gemini_key_here
# OR
OPENAI_API_KEY=your_openai_key_here
```

## Usage Examples

### Basic Usage with Individual Components

```python
from progress_monitoring import create_complete_system

# Create all components
image_analyzer, progress_generator, memory_manager = create_complete_system(
    provider="gemini",  # or "openai"
    api_key="your-api-key",
    memory_file="project_memory.json"
)

# 1. Analyze images
analysis_result = image_analyzer.analyze_images_in_folder(
    image_folder_path="path/to/images",
    project_context=memory_manager.get_project_memory()
)

# 2. Generate progress report
progress_report = progress_generator.generate_progress_report(
    analysis_content=analysis_result["analysis_text"],
    memory_metadata=memory_manager.get_project_memory(),
    date="2025-01-24",
    image_folder_path="path/to/images"
)

# 3. Store in enhanced memory
record_id = memory_manager.store_progress_report(
    date="2025-01-24",
    image_folder_path="path/to/images",
    analysis_content=analysis_result["analysis_text"],
    progress_report=progress_report["progress_data"]
)
```

### Convenience Function

```python
from progress_monitoring import analyze_construction_progress

# All-in-one analysis
result = analyze_construction_progress(
    provider="gemini",
    api_key="your-api-key",
    folder_path="path/to/images",
    memory_file="project_memory.json"
)
```

### Daily Progression Analysis

```python
# Analyze multiple days
daily_analyses = image_analyzer.analyze_daily_progression(
    img_data_path="path/to/day_folders",  # Contains day1/, day2/, etc.
    project_context=memory_manager.get_project_memory()
)

# Generate comprehensive progression report
progression_report = progress_generator.generate_daily_progression_report(
    daily_analyses=daily_analyses["daily_analyses"],
    memory_metadata=memory_manager.get_project_memory()
)
```

### Semantic Search

```python
# Search for similar reports
similar_reports = memory_manager.search_similar_reports(
    query="foundation work concrete pouring",
    limit=5,
    record_type="progress_report"  # or "analysis_report"
)

# Get recent reports
recent_reports = memory_manager.get_recent_reports(
    days=7,
    record_type="progress_report"
)
```

## Memory Structure

The enhanced memory system stores:

### Progress Reports
- Date and day number
- Image folder path
- Full analysis content
- Structured progress data
- Generated summaries
- Embeddings for semantic search

### Analysis Reports
- Date and day number
- Image folder path
- Analysis content
- Number of images processed
- Generated summaries
- Embeddings for semantic search

### Project Memory
- Project start date
- Total days analyzed
- Daily reports (legacy compatibility)
- Key milestones
- Current phase and progress
- Vector database statistics
- Recent summaries

## Benefits of New Architecture

### 1. Separation of Concerns
- **ImageAnalyzer**: Focus solely on image analysis
- **ProgressReportGenerator**: Handle structured report generation
- **MemoryManager**: Manage data storage and retrieval

### 2. Enhanced Search Capabilities
- Semantic search using vector embeddings
- Find similar reports across project history
- Filter by report type and date ranges

### 3. Scalability
- Vector database can handle large amounts of historical data
- Efficient similarity search and retrieval
- Automatic summarization reduces storage overhead

### 4. Flexibility
- Components can be used independently
- Easy to swap LLM providers
- Fallback options when external services unavailable

### 5. Backward Compatibility
- Legacy methods still available
- Existing code continues to work
- Gradual migration path

## Migration from Old Architecture

### Old Way
```python
from progress_monitoring import ConstructionSiteAnalyzer, AnalysisConfig

analyzer = ConstructionSiteAnalyzer(config)
result = analyzer.analyze_construction_site(folder_path)
```

### New Way
```python
from progress_monitoring import create_complete_system

image_analyzer, progress_generator, memory_manager = create_complete_system(
    provider="gemini", api_key="key"
)

# More granular control and better separation
analysis = image_analyzer.analyze_images_in_folder(folder_path)
report = progress_generator.generate_progress_report(...)
memory_manager.store_progress_report(...)
```

## Troubleshooting

### Qdrant Connection Issues
- Ensure Qdrant is running on localhost:6333
- Check Docker container status: `docker ps`
- System falls back to JSON storage if Qdrant unavailable

### Embedding Model Issues
- First run downloads the embedding model (~90MB)
- Requires internet connection for initial setup
- Model is cached locally after first download

### Memory Usage
- Vector embeddings use additional memory
- Adjust batch sizes for large image sets
- Monitor system resources during processing

## Example Files

- `examples/new_architecture_example.py` - Comprehensive usage examples
- `examples/basic_usage.py` - Legacy compatibility examples

## Next Steps

1. Run the example: `python examples/new_architecture_example.py`
2. Set up Qdrant for enhanced search capabilities
3. Migrate existing workflows to use new components
4. Explore semantic search and historical analysis features 