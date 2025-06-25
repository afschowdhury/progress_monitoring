"""
Main construction site analyzer that orchestrates all components.
"""
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List

from .config import AnalysisConfig
from .providers import create_ai_provider
from .image_processor import ImageProcessor
from .memory_manager import MemoryManager
from .prompts import PromptManager
from icecream import ic
ic.configureOutput(includeContext=True, prefix="DEBUG -")


class ConstructionSiteAnalyzer:
    """Main construction site analyzer that orchestrates all components."""
    
    def __init__(self, config: AnalysisConfig):
        self.config = config
        self.logger = self._setup_logging()
        
        # Initialize components
        self.ai_provider = create_ai_provider(config)
        self.image_processor = ImageProcessor(config)
        self.memory_manager = MemoryManager(config.memory_file_path)
        
        # Initialize prompt manager
        self.prompt_manager = PromptManager(config.prompt_settings.prompts_dir)
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration."""
        if self.config.enable_detailed_logging:
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        return logging.getLogger(self.__class__.__name__)
    
    def analyze_daily_progression(self, img_data_path: str, project_start_date: str = None) -> Dict[str, Any]:
        """Analyze all day folders sequentially and generate reports for each day."""
        try:
            # Get all day folders and sort them
            day_folders = []
            if os.path.exists(img_data_path):
                for item in os.listdir(img_data_path):
                    if os.path.isdir(os.path.join(img_data_path, item)) and item.startswith('day'):
                        day_folders.append(item)
            
            day_folders.sort(key=lambda x: int(x.replace('day', '')))
            
            if not day_folders:
                raise ValueError(f"No day folders found in {img_data_path}")
            
            self.logger.info(f"Found {len(day_folders)} day folders: {day_folders}")
            
            # Initialize memory
            memory_data = self.memory_manager.read_memory()
            if not memory_data.get("project_start_date"):
                if project_start_date:
                    memory_data["project_start_date"] = project_start_date
                else:
                    memory_data["project_start_date"] = datetime.now().strftime("%Y-%m-%d")
            
            # Reset daily reports for fresh analysis
            memory_data["daily_reports"] = {}
            memory_data["total_days_analyzed"] = 0
            
            all_daily_reports = {}
            previous_day_summary = ""
            
            # Process each day
            for i, day_folder in enumerate(day_folders):
                day_number = i + 1
                day_path = os.path.join(img_data_path, day_folder)
                
                # Calculate analysis date (project start + day number - 1)
                if project_start_date:
                    start_date = datetime.strptime(project_start_date, "%Y-%m-%d")
                    analysis_date = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
                else:
                    analysis_date = f"Day-{day_number}"
                
                self.logger.info(f"Analyzing {day_folder} (Day {day_number}) for date {analysis_date}")
                
                # Analyze this day
                daily_report = self._analyze_single_day(
                    day_path, day_number, len(day_folders), 
                    analysis_date, memory_data, previous_day_summary
                )
                
                # Update memory with this day's report
                memory_data = self.memory_manager.update_daily_report(
                    memory_data, analysis_date, 
                    daily_report["daily_description"], 
                    daily_report["images_processed"]
                )
                
                # Update memory with progress data
                memory_data = self._update_memory_with_progress(
                    memory_data, daily_report["progress_report"], analysis_date
                )
                
                # Store the report
                all_daily_reports[f"day_{day_number}"] = daily_report
                
                # Update previous day summary for next iteration
                previous_day_summary = daily_report["daily_description"][:500] + "..." if len(daily_report["daily_description"]) > 500 else daily_report["daily_description"]
            
            # Save updated memory
            self.memory_manager.write_memory(memory_data)
            
            # Return comprehensive results
            return {
                "analysis_type": "daily_progression",
                "total_days_analyzed": len(day_folders),
                "project_start_date": memory_data["project_start_date"],
                "daily_reports": all_daily_reports,
                "final_memory_state": {
                    "project_start_date": memory_data["project_start_date"],
                    "total_days_analyzed": memory_data["total_days_analyzed"],
                    "current_phase": memory_data["current_phase"],
                    "overall_progress_percentage": memory_data["overall_progress_percentage"],
                    "key_milestones": memory_data["key_milestones"]
                },
                "status": "success"
            }
            
        except Exception as e:
            self.logger.error(f"Daily progression analysis failed: {e}")
            return {
                "analysis_type": "daily_progression",
                "error": str(e),
                "status": "failed"
            }
    
    def _analyze_single_day(self, day_path: str, day_number: int, total_days: int, 
                           analysis_date: str, memory_data: Dict[str, Any], 
                           previous_day_summary: str) -> Dict[str, Any]:
        """Analyze a single day's images."""
        try:
            # Process images for this day
            image_files = self.image_processor.get_image_files(day_path)
            prepared_images = self.image_processor.prepare_images(image_files)
            
            if not prepared_images:
                raise ValueError(f"No images could be prepared for analysis in {day_path}")
            
            # Create day-specific analysis prompt
            prompt = self._create_daily_comparison_prompt(
                memory_data, day_number, total_days, analysis_date, previous_day_summary
            )
            
            # Analyze with AI
            self.logger.info(f"Analyzing Day {day_number} with {self.config.model_provider.value}")
            analysis_text = self.ai_provider.analyze_images(prepared_images, prompt)
            
            # Generate structured progress report
            progress_data = self._generate_progress_report(analysis_text, memory_data)
            
            # Format results for this day
            return {
                "day_number": day_number,
                "analysis_date": analysis_date,
                "images_processed": len(image_files),
                "daily_description": analysis_text,
                "progress_report": progress_data,
                "status": "success"
            }
            
        except Exception as e:
            self.logger.error(f"Analysis failed for day {day_number}: {e}")
            return {
                "day_number": day_number,
                "analysis_date": analysis_date,
                "error": str(e),
                "status": "failed"
            }
    
    def _create_daily_comparison_prompt(self, memory_data: Dict[str, Any], day_number: int, 
                                      total_days: int, analysis_date: str, 
                                      previous_day_summary: str) -> str:
        """Create daily comparison prompt using prompt manager."""
        # Determine which prompt to use based on provider
        prompt_name = "daily_comparison_analysis"
        if self.config.model_provider.value == "openai":
            prompt_name = "daily_comparison_analysis_openai"
        
        # Prepare variables for prompt template
        variables = {
            "day_number": day_number,
            "total_days": total_days,
            "analysis_date": analysis_date,
            "current_phase": memory_data.get('current_phase', 'Unknown'),
            "overall_progress_percentage": memory_data.get('overall_progress_percentage', 0),
            "project_start_date": memory_data.get('project_start_date', 'Unknown'),
            "previous_day_summary": previous_day_summary if previous_day_summary else "This is the first day of analysis."
        }
        
        # Render prompt using prompt manager
        prompt = self.prompt_manager.render_prompt(prompt_name, variables)
        ic(f"day {day_number} prompt: {prompt}")
        
        if prompt is None:
            # Fallback to hardcoded prompt if template not found
            self.logger.warning(f"Daily comparison prompt template '{prompt_name}' not found, using fallback")
            prompt = self._create_fallback_daily_prompt(
                memory_data, day_number, total_days, analysis_date, previous_day_summary
            )
        
        return prompt
    
    def _create_fallback_daily_prompt(self, memory_data: Dict[str, Any], day_number: int, 
                                    total_days: int, analysis_date: str, 
                                    previous_day_summary: str) -> str:
        """Create fallback daily comparison prompt if template is not available."""
        return f"""
INSTRUCTIONS: Provide a direct, professional construction analysis for Day {day_number}. Do not include conversational phrases or commentary. Start immediately with factual observations using the structure below.

DAY {day_number} ANALYSIS ({analysis_date})

PROJECT CONTEXT:
- Day: {day_number} of {total_days}
- Current phase: {memory_data.get('current_phase', 'Unknown')}
- Overall progress: {memory_data.get('overall_progress_percentage', 0)}%
- Project start: {memory_data.get('project_start_date', 'Unknown')}

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

    def analyze_construction_site(self, folder_path: str) -> Dict[str, Any]:
        """Analyze construction site images and generate comprehensive report."""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            
            # Read existing memory
            memory_data = self.memory_manager.read_memory()
            if not memory_data.get("project_start_date"):
                memory_data["project_start_date"] = today
            
            # Process images
            image_files = self.image_processor.get_image_files(folder_path)
            prepared_images = self.image_processor.prepare_images(image_files)
            
            if not prepared_images:
                raise ValueError("No images could be prepared for analysis")
            
            # Create analysis prompt using prompt manager
            prompt = self._create_analysis_prompt(memory_data, today)
            
            # Analyze with AI
            self.logger.info(f"Analyzing with {self.config.model_provider.value}")
            analysis_text = self.ai_provider.analyze_images(prepared_images, prompt)
            
            # Update memory with analysis
            memory_data = self.memory_manager.update_daily_report(
                memory_data, today, analysis_text, len(image_files)
            )
            
            # Generate structured progress report
            progress_data = self._generate_progress_report(analysis_text, memory_data)
            
            # Update memory with progress data
            memory_data = self._update_memory_with_progress(memory_data, progress_data, today)
            
            # Save updated memory
            self.memory_manager.write_memory(memory_data)
            
            # Return results
            return self._format_results(today, len(image_files), analysis_text, 
                                      progress_data, memory_data)
            
        except Exception as e:
            self.logger.error(f"Analysis failed: {e}")
            return {
                "analysis_date": datetime.now().strftime("%Y-%m-%d"),
                "error": str(e),
                "status": "failed"
            }
    
    def _create_analysis_prompt(self, memory_data: Dict[str, Any], today: str) -> str:
        """Create comprehensive analysis prompt using prompt manager."""
        # Build context from memory
        context = self._build_context_from_memory(memory_data)
        
        # Determine which prompt to use based on provider
        prompt_name = self.config.prompt_settings.default_analysis_prompt
        if self.config.model_provider.value == "openai":
            prompt_name = f"{prompt_name}_openai"
        
        # Prepare variables for prompt template
        variables = {
            "analysis_date": today,
            "current_phase": memory_data.get('current_phase', 'Unknown'),
            "total_days_analyzed": memory_data.get('total_days_analyzed', 0),
            "overall_progress_percentage": memory_data.get('overall_progress_percentage', 0),
            "project_start_date": memory_data.get('project_start_date', 'Unknown'),
            "historical_context": context
        }
        
        # Render prompt using prompt manager
        prompt = self.prompt_manager.render_prompt(prompt_name, variables)
        
        if prompt is None:
            # Fallback to hardcoded prompt if template not found
            self.logger.warning(f"Prompt template '{prompt_name}' not found, using fallback")
            prompt = self._create_fallback_prompt(memory_data, today, context)
        
        return prompt
    
    def _create_fallback_prompt(self, memory_data: Dict[str, Any], today: str, context: str) -> str:
        """Create fallback prompt if template is not available."""
        return f"""
INSTRUCTIONS: Provide a direct, professional construction site analysis. Do not include conversational phrases, greetings, or commentary. Start immediately with factual observations using the structure below.

ANALYSIS DATE: {today}
PROJECT CONTEXT:
- Current phase: {memory_data.get('current_phase', 'Unknown')}
- Days analyzed: {memory_data.get('total_days_analyzed', 0)}
- Overall progress: {memory_data.get('overall_progress_percentage', 0)}%
- Project start: {memory_data.get('project_start_date', 'Unknown')}

{context}

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
    
    def _build_context_from_memory(self, memory_data: Dict[str, Any]) -> str:
        """Build context string from memory data."""
        context = ""
        if memory_data.get("daily_reports"):
            recent_reports = list(memory_data["daily_reports"].items())[-3:]
            context = "Recent progress:\n"
            for date, report in recent_reports:
                context += f"- {date}: {report.get('summary', 'No summary')}\n"
        return context
    
    def _generate_progress_report(self, analysis_text: str, memory_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate structured progress report using prompt manager."""
        # Determine which prompt to use based on provider
        prompt_name = self.config.prompt_settings.default_progress_prompt
        if self.config.model_provider.value == "openai":
            prompt_name = f"{prompt_name}_openai"
        
        # Prepare variables for prompt template
        variables = {
            "analysis_text": analysis_text,
            "total_days_analyzed": memory_data.get('total_days_analyzed', 0),
            "previous_progress": memory_data.get('overall_progress_percentage', 0),
            "current_phase": memory_data.get('current_phase', 'Unknown')
        }
        
        # Render prompt using prompt manager
        progress_prompt = self.prompt_manager.render_prompt(prompt_name, variables)
        ic(f"Progress prompt: {progress_prompt}")
        
        if progress_prompt is None:
            # Fallback to hardcoded prompt if template not found
            self.logger.warning(f"Progress prompt template '{prompt_name}' not found, using fallback")
            progress_prompt = self._create_fallback_progress_prompt(analysis_text, memory_data)
        
        try:
            # Log the prompt being sent
            self.logger.info("Sending progress assessment prompt to AI provider...")
            ic(f"Progress prompt length: {len(progress_prompt)}")
            
            response = self.ai_provider.generate_structured_response(progress_prompt)
            ic(f"Progress prompt response: {response}")
            
            # Additional validation before JSON parsing
            if not response or response.strip() == "":
                self.logger.warning("AI provider returned empty response for progress prompt")
                return self._get_default_progress_data(memory_data)
            
            # Try to extract JSON if response contains additional text
            response_text = response.strip()
            
            # Look for JSON block if response has markdown formatting
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                if json_end != -1:
                    response_text = response_text[json_start:json_end].strip()
            elif response_text.startswith("```") and response_text.endswith("```"):
                # Remove markdown code block formatting
                response_text = response_text[3:-3].strip()
            
            # Find JSON object boundaries if response has extra text
            json_start = response_text.find("{")
            json_end = response_text.rfind("}")
            if json_start != -1 and json_end != -1 and json_end > json_start:
                response_text = response_text[json_start:json_end + 1]
            
            ic(f"Cleaned progress response: {response_text}")
            return json.loads(response_text)
            
        except json.JSONDecodeError as json_error:
            self.logger.warning(f"JSON parsing failed for progress data: {json_error}")
            self.logger.warning(f"Raw response was: {response[:200]}..." if len(response) > 200 else f"Raw response was: {response}")
            return self._get_default_progress_data(memory_data)
        except Exception as e:
            self.logger.warning(f"Failed to generate progress data: {e}")
            return self._get_default_progress_data(memory_data)
    
    def _create_fallback_progress_prompt(self, analysis_text: str, memory_data: Dict[str, Any]) -> str:
        """Create fallback progress prompt if template is not available."""
        return f"""
INSTRUCTIONS: Generate structured progress assessment from the analysis below. Respond with ONLY valid JSON - no explanatory text, comments, or markdown formatting.

PROJECT CONTEXT:
- Days analyzed: {memory_data.get('total_days_analyzed', 0)}
- Previous progress: {memory_data.get('overall_progress_percentage', 0)}%
- Current phase: {memory_data.get('current_phase', 'Unknown')}

ANALYSIS TEXT:
{analysis_text}

JSON REQUIREMENTS:
1. current_phase: Construction phase currently active
2. overall_progress_percentage: New overall project completion (0-100%)
3. daily_progress_percentage: Progress made today specifically
4. key_accomplishments: List 3-5 major accomplishments from today's work
5. identified_issues: Problems, delays, or concerns noted
6. next_phase_indicators: Signs indicating movement toward next construction phase
7. estimated_timeline_status: "On Schedule", "Ahead of Schedule", or "Behind Schedule"
8. critical_path_items: Key items that could affect project timeline

Respond with ONLY this exact JSON format:
{{
    "current_phase": "Phase name",
    "overall_progress_percentage": 50,
    "daily_progress_percentage": 5,
    "key_accomplishments": ["accomplishment 1", "accomplishment 2"],
    "identified_issues": ["issue 1", "issue 2"],
    "next_phase_indicators": ["indicator 1", "indicator 2"],
    "estimated_timeline_status": "On Schedule",
    "critical_path_items": ["item 1", "item 2"]
}}

CRITICAL: Start immediately with {{ and end with }}. No other text."""
    
    def _get_default_progress_data(self, memory_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get default progress data structure."""
        return {
            "current_phase": memory_data.get("current_phase", "Analysis in Progress"),
            "overall_progress_percentage": memory_data.get("overall_progress_percentage", 0),
            "daily_progress_percentage": 0,
            "key_accomplishments": [],
            "identified_issues": [],
            "next_phase_indicators": [],
            "estimated_timeline_status": "Unknown", 
            "critical_path_items": []
        }
    
    def _update_memory_with_progress(self, memory_data: Dict[str, Any], 
                                   progress_data: Dict[str, Any], today: str) -> Dict[str, Any]:
        """Update memory with progress data."""
        memory_data["current_phase"] = progress_data.get("current_phase", memory_data.get("current_phase"))
        memory_data["overall_progress_percentage"] = progress_data.get("overall_progress_percentage", 0)
        
        # Add milestone if significant progress
        memory_data = self.memory_manager.add_milestone(
            memory_data, today, 
            f"Progress in {progress_data.get('current_phase', 'construction')}",
            progress_data.get("daily_progress_percentage", 0)
        )
        
        return memory_data
    
    def _format_results(self, today: str, images_count: int, analysis_text: str,
                       progress_data: Dict[str, Any], memory_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format final results."""
        return {
            "analysis_date": today,
            "model_used": f"{self.config.model_provider.value}/{self.config.model_name}",
            "images_processed": images_count,
            "daily_description": analysis_text,
            "progress_report": progress_data,
            "updated_memory": {
                "project_start_date": memory_data["project_start_date"],
                "total_days_analyzed": memory_data["total_days_analyzed"],
                "current_phase": memory_data["current_phase"],
                "overall_progress_percentage": memory_data["overall_progress_percentage"],
                "recent_milestones": memory_data["key_milestones"][-5:] if memory_data["key_milestones"] else []
            },
            "status": "success"
        }

    def analyze_single_day(self, image_folder_path: str, day_number: int, total_days: int) -> Dict[str, Any]:
        """
        Analyze a specific day's construction progress given only the image folder path and day number.
        
        Args:
            image_folder_path: Path to the folder containing images for this specific day
            day_number: The day number in the project sequence
            
        Returns:
            Dict containing analysis results and updated memory state
        """
        try:
            # Read existing memory
            memory_data = self.memory_manager.read_memory()
            
            # Calculate analysis date
            analysis_date = self._calculate_analysis_date(memory_data, day_number)
            
            # Get previous day analysis from memory if available
            previous_day_analysis = self._get_previous_day_summary(memory_data, day_number)
            
            self.logger.info(f"Analyzing single day: Day {day_number} at {image_folder_path}")
            
            # Process images for this day
            image_files = self.image_processor.get_image_files(image_folder_path)
            prepared_images = self.image_processor.prepare_images(image_files)
            
            if not prepared_images:
                raise ValueError(f"No images could be prepared for analysis in {image_folder_path}")
            
            # Create day-specific analysis prompt
            prompt = self._create_daily_comparison_prompt(
                memory_data, day_number, total_days, analysis_date, previous_day_analysis
            )
            
            # Analyze with AI
            self.logger.info(f"Analyzing Day {day_number} with {self.config.model_provider.value}")
            analysis_text = self.ai_provider.analyze_images(prepared_images, prompt)
            
            # Generate structured progress report
            progress_data = self._generate_progress_report(analysis_text, memory_data)
            ic(f"Progress data MAIN: {progress_data}")
            # Update memory with this day's report
            memory_data = self.memory_manager.update_daily_report(
                memory_data, analysis_date, 
                analysis_text, 
                len(image_files)
            )
            
            # Update memory with progress data
            memory_data = self._update_memory_with_progress(
                memory_data, progress_data, analysis_date
            )
            
            # Update total days analyzed if this is a new maximum
            if day_number > memory_data.get('total_days_analyzed', 0):
                memory_data['total_days_analyzed'] = day_number
            
            # Save updated memory
            self.memory_manager.write_memory(memory_data)
            
            # Format and return results
            return {
                "analysis_type": "single_day",
                "day_number": day_number,
                "analysis_date": analysis_date,
                "model_used": f"{self.config.model_provider.value}/{self.config.model_name}",
                "images_processed": len(image_files),
                "daily_description": analysis_text,
                "progress_report": progress_data,
                "updated_memory": {
                    "project_start_date": memory_data["project_start_date"],
                    "total_days_analyzed": memory_data["total_days_analyzed"],
                    "current_phase": memory_data["current_phase"],
                    "overall_progress_percentage": memory_data["overall_progress_percentage"],
                    "recent_milestones": memory_data["key_milestones"][-5:] if memory_data["key_milestones"] else []
                },
                "status": "success"
            }
            
        except Exception as e:
            self.logger.error(f"Single day analysis failed for Day {day_number}: {e}")
            return {
                "analysis_type": "single_day",
                "day_number": day_number,
                "error": str(e),
                "status": "failed"
            }
    
    def _calculate_analysis_date(self, memory_data: Dict[str, Any], day_number: int) -> str:
        """Calculate the analysis date based on project start date and day number."""
        project_start_date = memory_data.get("project_start_date")
        
        if project_start_date:
            try:
                start_date = datetime.strptime(project_start_date, "%Y-%m-%d")
                analysis_date = (start_date + timedelta(days=day_number - 1)).strftime("%Y-%m-%d")
                return analysis_date
            except ValueError:
                self.logger.warning(f"Invalid project start date format: {project_start_date}")
        
        # Fallback to current date if no valid start date
        return datetime.now().strftime("%Y-%m-%d")
    
    def _get_previous_day_summary(self, memory_data: Dict[str, Any], day_number: int) -> str:
        """Get analysis from the previous day from memory if available."""
        if day_number <= 1:
            return ""
        
        # Calculate the previous day's date
        previous_day_date = self._calculate_analysis_date(memory_data, day_number - 1)
        
        daily_reports = memory_data.get("daily_reports", {})
        
        # Look for the specific previous day first
        if previous_day_date in daily_reports:
            report = daily_reports[previous_day_date]
            if isinstance(report, dict):
                # Use full_analysis if available, otherwise fall back to summary
                full_analysis = report.get("full_analysis", "")
                if full_analysis:
                    # Return a meaningful portion of the full analysis for context
                    return full_analysis[:1500] + "..." if len(full_analysis) > 1500 else full_analysis
                
                # Fallback to summary if full_analysis not available
                summary = report.get("summary", "")
                return summary[:500] + "..." if len(summary) > 500 else summary
        
        # If exact previous day not found, look for the most recent analysis
        sorted_dates = sorted(daily_reports.keys(), reverse=True)
        for date in sorted_dates:
            report = daily_reports[date]
            if isinstance(report, dict):
                # Use full_analysis for better context
                full_analysis = report.get("full_analysis", "")
                if full_analysis:
                    return full_analysis[:1500] + "..." if len(full_analysis) > 1500 else full_analysis
                
                # Fallback to summary
                summary = report.get("summary", "")
                return summary[:500] + "..." if len(summary) > 500 else summary
        
        # If no previous day found, return empty string
        return "" 