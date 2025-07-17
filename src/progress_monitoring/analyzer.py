"""
Image analyzer that processes construction site images and provides detailed analysis.
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List

from icecream import ic

from .config import AnalysisConfig
from .image_processor import ImageProcessor
from .prompts import PromptManager
from .providers import create_ai_provider
from .utils import ParallelImageProcessor, process_images_parallel

ic.configureOutput(includeContext=True, prefix="DEBUG -")


class ImageAnalyzer:
    """Image analyzer that processes construction site images and provides detailed analysis."""

    def __init__(self, config: AnalysisConfig):
        self.config = config
        self.logger = self._setup_logging()

        # Initialize components
        self.ai_provider = create_ai_provider(config)
        self.image_processor = ImageProcessor(config)

        # Initialize prompt manager
        self.prompt_manager = PromptManager(config.prompt_settings.prompts_dir)

    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration."""
        if self.config.enable_detailed_logging:
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            )
        return logging.getLogger(self.__class__.__name__)

    def analyze_images_in_folder(
        self, 
        image_folder_path: str, 
        project_context: Dict[str, Any] = None,
        previous_day_summary: str = ""
    ) -> Dict[str, Any]:
        """
        Analyze all images in a folder and provide detailed description of what was done.
        
        Args:
            image_folder_path: Path to folder containing images
            project_context: Context about the project (phase, progress, etc.)
            previous_day_summary: Summary from previous day for comparison
            
        Returns:
            Dict containing analysis results
        """
        try:
            # Process images in the folder
            image_files = self.image_processor.get_image_files(image_folder_path)
            prepared_images = self.image_processor.prepare_images(image_files)

            if not prepared_images:
                raise ValueError(f"No images could be prepared for analysis in {image_folder_path}")

            # Create analysis prompt
            prompt = self._create_image_analysis_prompt(project_context, previous_day_summary)

            # Choose processing method based on image count
            if len(prepared_images) > 15:  # Use parallel processing for large sets
                self.logger.info(f"Using parallel processing for {len(prepared_images)} images")
                analysis_text = self._analyze_images_parallel(prepared_images, prompt)
            else:
                # Use standard processing for smaller sets
                self.logger.info(f"Analyzing {len(prepared_images)} images with {self.config.model_provider.value}")
                analysis_text = self.ai_provider.analyze_images(prepared_images, prompt)

            return {
                "folder_path": image_folder_path,
                "images_processed": len(image_files),
                "analysis_text": analysis_text,
                "status": "success",
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Image analysis failed for folder {image_folder_path}: {e}")
            return {
                "folder_path": image_folder_path,
                "error": str(e),
                "status": "failed",
                "timestamp": datetime.now().isoformat()
            }

    def analyze_daily_progression(
        self, 
        img_data_path: str, 
        project_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Analyze all day folders sequentially and generate analysis for each day.
        
        Args:
            img_data_path: Path to directory containing day folders (day1, day2, etc.)
            project_context: Context about the project
            
        Returns:
            Dict containing analysis for all days
        """
        try:
            # Get all day folders and sort them
            day_folders = []
            if os.path.exists(img_data_path):
                for item in os.listdir(img_data_path):
                    if os.path.isdir(
                        os.path.join(img_data_path, item)
                    ) and item.startswith("day"):
                        day_folders.append(item)

            day_folders.sort(key=lambda x: int(x.replace("day", "")))

            if not day_folders:
                raise ValueError(f"No day folders found in {img_data_path}")

            self.logger.info(f"Found {len(day_folders)} day folders: {day_folders}")

            all_daily_analyses = {}
            previous_day_summary = ""

            # Process each day
            for i, day_folder in enumerate(day_folders):
                day_number = i + 1
                day_path = os.path.join(img_data_path, day_folder)

                self.logger.info(f"Analyzing {day_folder} (Day {day_number})")

                # Analyze this day
                daily_analysis = self._analyze_single_day(
                    day_path,
                    day_number,
                    len(day_folders),
                    project_context,
                    previous_day_summary,
                )

                # Store the analysis
                all_daily_analyses[f"day_{day_number}"] = daily_analysis

                # Update previous day summary for next iteration
                if daily_analysis["status"] == "success":
                    analysis_text = daily_analysis["analysis_text"]
                    previous_day_summary = (
                        analysis_text[:500] + "..."
                        if len(analysis_text) > 500
                        else analysis_text
                    )

            return {
                "analysis_type": "daily_progression",
                "total_days_analyzed": len(day_folders),
                "daily_analyses": all_daily_analyses,
                "status": "success",
            }

        except Exception as e:
            self.logger.error(f"Daily progression analysis failed: {e}")
            return {
                "analysis_type": "daily_progression",
                "error": str(e),
                "status": "failed",
            }

    def _analyze_single_day(
        self,
        day_path: str,
        day_number: int,
        total_days: int,
        project_context: Dict[str, Any],
        previous_day_summary: str,
    ) -> Dict[str, Any]:
        """Analyze a single day's images."""
        try:
            # Process images for this day
            image_files = self.image_processor.get_image_files(day_path)
            prepared_images = self.image_processor.prepare_images(image_files)

            if not prepared_images:
                raise ValueError(f"No images could be prepared for analysis in {day_path}")

            # Create day-specific analysis prompt
            prompt = self._create_daily_comparison_prompt(
                project_context, day_number, total_days, previous_day_summary
            )

            # Choose processing method based on image count
            if len(prepared_images) > 15:  # Use parallel processing for large sets
                self.logger.info(f"Using parallel processing for Day {day_number} with {len(prepared_images)} images")
                analysis_text = self._analyze_images_parallel(prepared_images, prompt)
            else:
                # Use standard processing for smaller sets
                self.logger.info(f"Analyzing Day {day_number} with {self.config.model_provider.value}")
                analysis_text = self.ai_provider.analyze_images(prepared_images, prompt)

            return {
                "day_number": day_number,
                "day_path": day_path,
                "images_processed": len(image_files),
                "analysis_text": analysis_text,
                "status": "success",
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Analysis failed for day {day_number}: {e}")
            return {
                "day_number": day_number,
                "day_path": day_path,
                "error": str(e),
                "status": "failed",
                "timestamp": datetime.now().isoformat()
            }

    def _analyze_images_parallel(self, images: List[Dict[str, Any]], prompt: str) -> str:
        """Analyze images using parallel processing with rate limiting."""
        try:
            # Use the parallel processing utility
            analysis_text = process_images_parallel(
                images=images,
                prompt=prompt,
                ai_provider=self.ai_provider,
                config=self.config,
                max_workers=3,
                batch_size=10,
            )
            return analysis_text
        except Exception as e:
            self.logger.error(f"Parallel processing failed, falling back to sequential: {e}")
            # Fallback to sequential processing
            return self.ai_provider.analyze_images(images, prompt)

    def _create_image_analysis_prompt(
        self, 
        project_context: Dict[str, Any] = None, 
        previous_day_summary: str = ""
    ) -> str:
        """Create comprehensive image analysis prompt."""
        context_info = ""
        if project_context:
            context_info = f"""
PROJECT CONTEXT:
- Current phase: {project_context.get('current_phase', 'Unknown')}
- Overall progress: {project_context.get('overall_progress_percentage', 0)}%
- Project start: {project_context.get('project_start_date', 'Unknown')}
"""

        previous_context = ""
        if previous_day_summary:
            previous_context = f"""
PREVIOUS DAY SUMMARY:
{previous_day_summary}
"""

        # Try to use prompt manager first
        prompt_name = "image_analysis_gemini"
        if self.config.model_provider.value == "openai":
            prompt_name = "image_analysis_openai"

        variables = {
            "project_context": context_info,
            "previous_day_summary": previous_context,
        }

        prompt = self.prompt_manager.render_prompt(prompt_name, variables)

        if prompt is None:
            # Fallback to hardcoded prompt
            self.logger.warning(f"Image analysis prompt template '{prompt_name}' not found, using fallback")
            prompt = self._create_fallback_image_analysis_prompt(context_info, previous_context)

        return prompt

    def _create_daily_comparison_prompt(
        self,
        project_context: Dict[str, Any],
        day_number: int,
        total_days: int,
        previous_day_summary: str,
    ) -> str:
        """Create daily comparison prompt."""
        # Try to use prompt manager first
        prompt_name = "daily_comparison_analysis"
        if self.config.model_provider.value == "openai":
            prompt_name = "daily_comparison_analysis_openai"

        variables = {
            "day_number": day_number,
            "total_days": total_days,
            "current_phase": project_context.get('current_phase', 'Unknown') if project_context else 'Unknown',
            "overall_progress_percentage": project_context.get('overall_progress_percentage', 0) if project_context else 0,
            "project_start_date": project_context.get('project_start_date', 'Unknown') if project_context else 'Unknown',
            "previous_day_summary": previous_day_summary if previous_day_summary else "This is the first day of analysis.",
        }

        prompt = self.prompt_manager.render_prompt(prompt_name, variables)

        if prompt is None:
            # Fallback to hardcoded prompt
            self.logger.warning(f"Daily comparison prompt template '{prompt_name}' not found, using fallback")
            prompt = self._create_fallback_daily_prompt(project_context, day_number, total_days, previous_day_summary)

        return prompt

    def _create_fallback_image_analysis_prompt(self, context_info: str, previous_context: str) -> str:
        """Create fallback image analysis prompt."""
        return f"""
INSTRUCTIONS: Provide a direct, professional construction analysis. Do not include conversational phrases or commentary. Start immediately with factual observations using the structure below.

{context_info}
{previous_context}

REQUIRED ANALYSIS STRUCTURE:

**1. DAILY ACTIVITIES**
Document specific construction work performed today.

**2. PROGRESS ACCOMPLISHED**
List specific accomplishments and completions.

**3. KEY OBSERVATIONS**
Notable changes, installations, and issues.

**4. SAFETY ASSESSMENT**
Safety practices, violations, and concerns.

**5. EQUIPMENT & PERSONNEL**
Visible equipment, tools, and workforce details.

**6. QUALITY CONTROL**
Work quality assessment and standards compliance.

**7. WEATHER IMPACT**
How conditions affected work progress.

**8. TIMELINE STATUS**
Project schedule assessment.

**COMPARATIVE ANALYSIS**
Compare with previous progress using concrete observations and measurable indicators.

Format your response using the above headings with concise, factual content under each section.
"""

    def _create_fallback_daily_prompt(
        self,
        project_context: Dict[str, Any],
        day_number: int,
        total_days: int,
        previous_day_summary: str,
    ) -> str:
        """Create fallback daily comparison prompt."""
        current_phase = project_context.get('current_phase', 'Unknown') if project_context else 'Unknown'
        overall_progress = project_context.get('overall_progress_percentage', 0) if project_context else 0
        project_start = project_context.get('project_start_date', 'Unknown') if project_context else 'Unknown'
        
        return f"""
INSTRUCTIONS: Provide a direct, professional construction analysis for Day {day_number}. Do not include conversational phrases or commentary. Start immediately with factual observations using the structure below.

DAY {day_number} ANALYSIS

PROJECT CONTEXT:
- Day: {day_number} of {total_days}
- Current phase: {current_phase}
- Overall progress: {overall_progress}%
- Project start: {project_start}

PREVIOUS DAY SUMMARY:
{previous_day_summary if previous_day_summary else "This is the first day of analysis."}

REQUIRED ANALYSIS STRUCTURE:

**1. DAILY ACTIVITIES**
Specific construction work performed on Day {day_number}.

**2. PROGRESS COMPARISON**
Changes and progress since previous day.

**3. KEY CHANGES**
Notable modifications, additions, or installations since yesterday.

**4. CONSTRUCTION ELEMENTS**
New structural elements, materials, or installations identified.

**5. WORK QUALITY**
Quality and craftsmanship assessment of completed work.

**6. SAFETY OBSERVATIONS**
Safety practices, equipment, and concerns noted.

**7. EQUIPMENT & PERSONNEL**
Visible equipment, tools, and workforce activity.

**8. TIMELINE ASSESSMENT**
Schedule progress based on daily changes.

**COMPARATIVE ANALYSIS**
- Differences from previous day
- Work phase progression
- Delays, accelerations, or issues
- Cumulative progress impact

Format your response using the above headings with concise, factual content under each section.
"""
