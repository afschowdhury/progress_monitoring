# Setup Guide for Progress Monitoring

## Installation

1. **Install the package in development mode:**
   ```bash
   pip install -e .
   ```

2. **Set up environment variables:**
   ```bash
   cp env.example .env
   # Edit .env and add your API keys
   ```

3. **Verify installation:**
   ```bash
   python src/progress_monitoring/test_import.py
   ```

## Running the Demo Notebook

The demo notebook (`src/progress_monitoring/demo_run.ipynb`) should now work correctly after installing the package in development mode.

### Common Issues and Solutions

**Error: `ModuleNotFoundError: No module named 'progress_monitoring'`**

**Solution:** Install the package in development mode:
```bash
pip install -e .
```

**Error: `No API key found`**

**Solution:** Create a `.env` file with your API keys:
```bash
cp env.example .env
# Edit .env and add: GOOGLE_API_KEY=your_actual_api_key_here
```

## Project Structure

```
progress_monitoring/
├── src/
│   └── progress_monitoring/     # Main package
│       ├── __init__.py
│       ├── factory.py           # Main factory functions
│       ├── analyzer.py          # Core analysis logic
│       ├── config.py            # Configuration classes
│       ├── demo_run.ipynb       # Demo notebook
│       └── test_import.py       # Import test script
├── pyproject.toml               # Package configuration
├── env.example                  # Environment variables template
└── README.md
```

## Usage

```python
from progress_monitoring.factory import analyze_construction_progress

result = analyze_construction_progress(
    provider="gemini",
    api_key="your_api_key",
    folder_path="./path/to/images",
    model_name="gemini-2.5-flash",
    memory_file="my_project_memory.txt",
    prompts_dir="prompts"
) 