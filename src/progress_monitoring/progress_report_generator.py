"""
Progress Report Generator that creates structured reports from image analysis and memory data.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from icecream import ic

from .config import AnalysisConfig
from .prompts import PromptManager
from .providers import create_ai_provider

ic.configureOutput(includeContext=True, prefix="DEBUG -")


class ProgressReportGenerator:
    """Generates structured progress reports from image analysis and project memory."""

    def __init__(self, config: AnalysisConfig):
        self.config = config
        self.logger = self._setup_logging()

        # Initialize components
        self.ai_provider = create_ai_provider(config)
        self.prompt_manager = PromptManager(config.prompt_settings.prompts_dir)

    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration."""
        if self.config.enable_detailed_logging:
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            )
        return logging.getLogger(self.__class__.__name__)

    def generate_progress_report(
        self,
        analysis_content: str,
        memory_metadata: Dict[str, Any],
        date: str,
        image_folder_path: str = "",
        day_number: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Generate a structured progress report from analysis content and memory metadata.
        
        Args:
            analysis_content: Detailed analysis text from ImageAnalyzer
            memory_metadata: Metadata from memory (previous reports, summaries, etc.)
            date: Date of the analysis
            image_folder_path: Path to the analyzed image folder
            day_number: Day number if applicable
            
        Returns:
            Dict containing structured progress report
        """
        try:
            self.logger.info(f"Generating progress report for {date}")

            # Create progress assessment prompt
            prompt = self._create_progress_assessment_prompt(
                analysis_content, memory_metadata, date, day_number
            )

            # Generate structured progress data using AI
            progress_data = self._generate_structured_progress_data(prompt, memory_metadata)

            # Create final report structure
            report = {
                "date": date,
                "day_number": day_number,
                "image_folder_path": image_folder_path,
                "analysis_content": analysis_content,
                "progress_data": progress_data,
                "generated_at": datetime.now().isoformat(),
                "model_used": f"{self.config.model_provider.value}/{self.config.model_name}",
                "status": "success"
            }

            self.logger.info(f"Progress report generated successfully for {date}")
            return report

        except Exception as e:
            self.logger.error(f"Failed to generate progress report for {date}: {e}")
            return {
                "date": date,
                "day_number": day_number,
                "image_folder_path": image_folder_path,
                "error": str(e),
                "generated_at": datetime.now().isoformat(),
                "status": "failed"
            }

    def generate_daily_progression_report(
        self,
        daily_analyses: Dict[str, Any],
        memory_metadata: Dict[str, Any],
        project_context: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive progression report from multiple daily analyses.
        
        Args:
            daily_analyses: Dict of daily analysis results from ImageAnalyzer
            memory_metadata: Metadata from memory system
            project_context: Overall project context
            
        Returns:
            Dict containing comprehensive progression report
        """
        try:
            self.logger.info(f"Generating daily progression report for {len(daily_analyses)} days")

            progression_reports = {}
            
            # Generate progress report for each day
            for day_key, analysis_data in daily_analyses.items():
                if analysis_data.get("status") == "success":
                    day_number = analysis_data.get("day_number")
                    analysis_text = analysis_data.get("analysis_text", "")
                    day_path = analysis_data.get("day_path", "")
                    
                    # Calculate date for this day
                    date = self._calculate_report_date(memory_metadata, day_number)
                    
                    # Generate progress report for this day
                    daily_report = self.generate_progress_report(
                        analysis_content=analysis_text,
                        memory_metadata=memory_metadata,
                        date=date,
                        image_folder_path=day_path,
                        day_number=day_number
                    )
                    
                    progression_reports[day_key] = daily_report

            # Generate overall progression summary
            overall_summary = self._generate_progression_summary(
                progression_reports, memory_metadata, project_context
            )

            return {
                "report_type": "daily_progression",
                "total_days": len(daily_analyses),
                "successful_reports": len(progression_reports),
                "daily_reports": progression_reports,
                "overall_summary": overall_summary,
                "generated_at": datetime.now().isoformat(),
                "status": "success"
            }

        except Exception as e:
            self.logger.error(f"Failed to generate daily progression report: {e}")
            return {
                "report_type": "daily_progression",
                "error": str(e),
                "generated_at": datetime.now().isoformat(),
                "status": "failed"
            }

    def _create_progress_assessment_prompt(
        self,
        analysis_content: str,
        memory_metadata: Dict[str, Any],
        date: str,
        day_number: Optional[int] = None,
    ) -> str:
        """Create progress assessment prompt using prompt manager."""
        # Determine which prompt to use based on provider
        prompt_name = self.config.prompt_settings.default_progress_prompt
        if self.config.model_provider.value == "openai":
            prompt_name = f"{prompt_name}_openai"

        # Prepare variables for prompt template
        variables = {
            "analysis_content": analysis_content,
            "date": date,
            "day_number": day_number or "N/A",
            "total_days_analyzed": memory_metadata.get("total_days_analyzed", 0),
            "previous_progress": memory_metadata.get("overall_progress_percentage", 0),
            "current_phase": memory_metadata.get("current_phase", "Unknown"),
            "project_start_date": memory_metadata.get("project_start_date", "Unknown"),
            "previous_reports_summary": self._get_previous_reports_summary(memory_metadata),
        }

        # Render prompt using prompt manager
        prompt = self.prompt_manager.render_prompt(prompt_name, variables)

        if prompt is None:
            # Fallback to hardcoded prompt if template not found
            self.logger.warning(f"Progress prompt template '{prompt_name}' not found, using fallback")
            prompt = self._create_fallback_progress_prompt(analysis_content, memory_metadata, date)

        return prompt

    def _generate_structured_progress_data(
        self, prompt: str, memory_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate structured progress data using AI provider."""
        try:
            self.logger.info("Generating structured progress data...")
            
            response = self.ai_provider.generate_structured_response(prompt)
            
            if not response or response.strip() == "":
                self.logger.warning("AI provider returned empty response for progress prompt")
                return self._get_default_progress_data(memory_metadata)

            # Clean and parse JSON response
            response_text = self._clean_json_response(response)
            
            try:
                progress_data = json.loads(response_text)
                
                # Validate required fields
                required_fields = [
                    "current_phase", "overall_progress_percentage", 
                    "daily_progress_percentage", "key_accomplishments"
                ]
                for field in required_fields:
                    if field not in progress_data:
                        self.logger.warning(f"Missing required field '{field}' in progress data")
                        return self._get_default_progress_data(memory_metadata)
                
                return progress_data
                
            except json.JSONDecodeError as json_error:
                self.logger.warning(f"JSON parsing failed for progress data: {json_error}")
                self.logger.warning(f"Raw response: {response[:200]}...")
                return self._get_default_progress_data(memory_metadata)

        except Exception as e:
            self.logger.warning(f"Failed to generate structured progress data: {e}")
            return self._get_default_progress_data(memory_metadata)

    def _clean_json_response(self, response: str) -> str:
        """Clean AI response to extract valid JSON."""
        response_text = response.strip()

        # Handle markdown code blocks
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            if json_end != -1:
                response_text = response_text[json_start:json_end].strip()
        elif response_text.startswith("```") and response_text.endswith("```"):
            response_text = response_text[3:-3].strip()

        # Extract JSON object boundaries
        json_start = response_text.find("{")
        json_end = response_text.rfind("}")
        if json_start != -1 and json_end != -1 and json_end > json_start:
            response_text = response_text[json_start : json_end + 1]

        return response_text

    def _generate_progression_summary(
        self,
        progression_reports: Dict[str, Any],
        memory_metadata: Dict[str, Any],
        project_context: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Generate overall progression summary from daily reports."""
        try:
            # Extract key metrics from all daily reports
            total_progress = []
            all_accomplishments = []
            all_issues = []
            phases = []

            for day_key, report in progression_reports.items():
                if report.get("status") == "success":
                    progress_data = report.get("progress_data", {})
                    
                    if "overall_progress_percentage" in progress_data:
                        total_progress.append(progress_data["overall_progress_percentage"])
                    
                    if "key_accomplishments" in progress_data:
                        all_accomplishments.extend(progress_data["key_accomplishments"])
                    
                    if "identified_issues" in progress_data:
                        all_issues.extend(progress_data["identified_issues"])
                    
                    if "current_phase" in progress_data:
                        phases.append(progress_data["current_phase"])

            # Calculate summary metrics
            final_progress = max(total_progress) if total_progress else 0
            unique_accomplishments = list(set(all_accomplishments))[:10]  # Top 10 unique
            unique_issues = list(set(all_issues))[:10]  # Top 10 unique
            final_phase = phases[-1] if phases else "Unknown"

            return {
                "final_progress_percentage": final_progress,
                "total_days_reported": len(progression_reports),
                "final_phase": final_phase,
                "key_accomplishments": unique_accomplishments,
                "identified_issues": unique_issues,
                "progress_trend": self._calculate_progress_trend(total_progress),
                "summary_generated_at": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Failed to generate progression summary: {e}")
            return {
                "error": str(e),
                "summary_generated_at": datetime.now().isoformat()
            }

    def _calculate_progress_trend(self, progress_values: List[float]) -> str:
        """Calculate overall progress trend."""
        if len(progress_values) < 2:
            return "Insufficient data"
        
        start_progress = progress_values[0]
        end_progress = progress_values[-1]
        
        if end_progress > start_progress + 5:
            return "Increasing"
        elif end_progress < start_progress - 5:
            return "Decreasing"
        else:
            return "Stable"

    def _calculate_report_date(self, memory_metadata: Dict[str, Any], day_number: int) -> str:
        """Calculate report date based on project start date and day number."""
        project_start_date = memory_metadata.get("project_start_date")
        
        if project_start_date and day_number:
            try:
                from datetime import datetime, timedelta
                start_date = datetime.strptime(project_start_date, "%Y-%m-%d")
                report_date = (start_date + timedelta(days=day_number - 1)).strftime("%Y-%m-%d")
                return report_date
            except ValueError:
                self.logger.warning(f"Invalid project start date format: {project_start_date}")
        
        return datetime.now().strftime("%Y-%m-%d")

    def _get_previous_reports_summary(self, memory_metadata: Dict[str, Any]) -> str:
        """Get summary of previous reports from memory."""
        daily_reports = memory_metadata.get("daily_reports", {})
        
        if not daily_reports:
            return "No previous reports available."
        
        # Get the most recent 3 reports
        sorted_dates = sorted(daily_reports.keys(), reverse=True)[:3]
        summary = "Recent progress reports:\n"
        
        for date in sorted_dates:
            report = daily_reports[date]
            if isinstance(report, dict):
                summary += f"- {date}: {report.get('summary', 'No summary available')}\n"
        
        return summary

    def _create_fallback_progress_prompt(
        self, analysis_content: str, memory_metadata: Dict[str, Any], date: str
    ) -> str:
        """Create fallback progress assessment prompt."""
        return f"""
INSTRUCTIONS: Generate structured progress assessment from the analysis below. Respond with ONLY valid JSON - no explanatory text, comments, or markdown formatting.

DATE: {date}
PROJECT CONTEXT:
- Days analyzed: {memory_metadata.get('total_days_analyzed', 0)}
- Previous progress: {memory_metadata.get('overall_progress_percentage', 0)}%
- Current phase: {memory_metadata.get('current_phase', 'Unknown')}
- Project start: {memory_metadata.get('project_start_date', 'Unknown')}

ANALYSIS CONTENT:
{analysis_content}

JSON REQUIREMENTS:
1. current_phase: Construction phase currently active
2. overall_progress_percentage: New overall project completion (0-100%)
3. daily_progress_percentage: Progress made today specifically
4. key_accomplishments: List 3-5 major accomplishments from today's work
5. identified_issues: Problems, delays, or concerns noted
6. next_phase_indicators: Signs indicating movement toward next construction phase
7. estimated_timeline_status: "On Schedule", "Ahead of Schedule", or "Behind Schedule"
8. critical_path_items: Key items that could affect project timeline
9. safety_observations: Safety-related observations and concerns
10. quality_assessment: Quality rating and observations

Respond with ONLY this exact JSON format:
{{
    "current_phase": "Phase name",
    "overall_progress_percentage": 50,
    "daily_progress_percentage": 5,
    "key_accomplishments": ["accomplishment 1", "accomplishment 2"],
    "identified_issues": ["issue 1", "issue 2"],
    "next_phase_indicators": ["indicator 1", "indicator 2"],
    "estimated_timeline_status": "On Schedule",
    "critical_path_items": ["item 1", "item 2"],
    "safety_observations": ["observation 1", "observation 2"],
    "quality_assessment": "Good"
}}

CRITICAL: Start immediately with {{ and end with }}. No other text."""

    def _get_default_progress_data(self, memory_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Get default progress data structure."""
        return {
            "current_phase": memory_metadata.get("current_phase", "Analysis in Progress"),
            "overall_progress_percentage": memory_metadata.get("overall_progress_percentage", 0),
            "daily_progress_percentage": 0,
            "key_accomplishments": [],
            "identified_issues": [],
            "next_phase_indicators": [],
            "estimated_timeline_status": "Unknown",
            "critical_path_items": [],
            "safety_observations": [],
            "quality_assessment": "Unknown",
        } 