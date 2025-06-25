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
DAY_1_IMAGES_FOLDER = "/Users/afschowdhury/Code Local/crc/progress-monitoring/progress_monitoring/src/progress_monitoring/video_sampler/img_data/day1"  # Path to your construction site images
PROVIDER = "gemini"  # or "openai"
DAY_2_IMAGES_FOLDER = "/Users/afschowdhury/Code Local/crc/progress-monitoring/progress_monitoring/src/progress_monitoring/video_sampler/img_data/day2"  # Path to your construction site images
DAY_3_IMAGES_FOLDER = "/Users/afschowdhury/Code Local/crc/progress-monitoring/progress_monitoring/src/progress_monitoring/video_sampler/img_data/day3"  # Path to your construction site images
DAY_4_IMAGES_FOLDER = "/Users/afschowdhury/Code Local/crc/progress-monitoring/progress_monitoring/src/progress_monitoring/video_sampler/img_data/day4"  # Path to your construction site images
DAY_5_IMAGES_FOLDER = "/Users/afschowdhury/Code Local/crc/progress-monitoring/progress_monitoring/src/progress_monitoring/video_sampler/img_data/day5"  # Path to your construction site images

# Create sample images folder if it doesn't exist
Path(DAY_1_IMAGES_FOLDER).mkdir(exist_ok=True)

print(f"Using provider: {PROVIDER}")
print(f"Images folder: {DAY_1_IMAGES_FOLDER}")

from progress_monitoring import ConstructionSiteAnalyzer, AnalysisConfig, ModelProvider
import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")

config = AnalysisConfig(
    model_provider=ModelProvider.GEMINI,
    api_key=GEMINI_API_KEY,
    model_name="gemini-2.0-flash",
    ### OPENAI 
    # model_provider=ModelProvider.OPENAI,
    # api_key=OPENAI_API_KEY,
    # model_name="gpt-4o",
    memory_file_path="demo_memory.txt"
)

analyzer = ConstructionSiteAnalyzer(config)


day_report = analyzer.analyze_single_day(DAY_3_IMAGES_FOLDER, 3,5)

ic(day_report)

