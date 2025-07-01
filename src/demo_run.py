"""
Construction Progress Monitoring Demo

This notebook demonstrates how to use the construction progress monitoring package
to analyze construction site images with AI vision models.
"""

import os
import json
from pathlib import Path
import progress_monitoring as pm
import os
from dotenv import load_dotenv

load_dotenv()

from icecream import ic
ic.configureOutput(includeContext=True, prefix="DEBUG -")

GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WINDOWS_PATH_PREFIX = "/home/achowd6/CODES/crc/progress-monitoring/src/progress_monitoring/video_sampler/img_data"
MAC_PATH_PREFIX = "/Users/afschowdhury/Code Local/crc/progress-monitoring/progress_monitoring/src/progress_monitoring/video_sampler/img_data"
PROVIDER = "gemini"  # or "openai"







from progress_monitoring import ConstructionSiteAnalyzer, AnalysisConfig, ModelProvider
import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")

config = AnalysisConfig(
    # model_provider=ModelProvider.GEMINI,
    # api_key=GEMINI_API_KEY,
    # model_name="gemini-2.0-flash",
    ### OPENAI 
    model_provider=ModelProvider.OPENAI,
    api_key=OPENAI_API_KEY,
    model_name="gpt-4.1-nano",
    memory_file_path="demo_memory.txt"
)

def get_images_folder(os_name, day_number):
    if os_name == "win":
        return f"{WINDOWS_PATH_PREFIX}/day{day_number}"
    elif os_name == "mac":
        return f"{MAC_PATH_PREFIX}/day{day_number}"
    else:
        raise ValueError(f"Unsupported OS: {os_name}")



analyzer = ConstructionSiteAnalyzer(config)


day_report = analyzer.analyze_single_day(get_images_folder('win', 1), 1,5)

ic(day_report)
