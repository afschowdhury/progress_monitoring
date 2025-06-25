"""
Main construction site analyzer that orchestrates all components.
"""
import json
import logging
from datetime import datetime
from typing import Dict, Any

from .config import AnalysisConfig
from .providers import create_ai_provider
from .image_processor import ImageProcessor
from .memory_manager import MemoryManager
from .prompts import PromptManager


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
You are an expert construction project manager analyzing construction site images taken on {today}.

CONTEXT:
- Current project phase: {memory_data.get('current_phase', 'Unknown')}
- Total days analyzed: {memory_data.get('total_days_analyzed', 0)}
- Overall progress: {memory_data.get('overall_progress_percentage', 0)}%
- Project start: {memory_data.get('project_start_date', 'Unknown')}

{context}

ANALYSIS REQUIREMENTS:
1. Daily Activities: What construction work was performed today?
2. Progress Made: Specific accomplishments and completions
3. Key Observations: Notable changes, installations, issues
4. Safety Assessment: Safety practices and concerns
5. Equipment/Personnel: Visible equipment and workforce
6. Quality Control: Work quality assessment
7. Weather Impact: How conditions affected work
8. Timeline: Project schedule status

Provide detailed, professional analysis comparing with previous progress where available.
Focus on concrete observations and measurable progress indicators.
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
        
        if progress_prompt is None:
            # Fallback to hardcoded prompt if template not found
            self.logger.warning(f"Progress prompt template '{prompt_name}' not found, using fallback")
            progress_prompt = self._create_fallback_progress_prompt(analysis_text, memory_data)
        
        try:
            response = self.ai_provider.generate_structured_response(progress_prompt)
            return json.loads(response)
        except (json.JSONDecodeError, Exception) as e:
            self.logger.warning(f"Could not parse progress data: {e}")
            return self._get_default_progress_data(memory_data)
    
    def _create_fallback_progress_prompt(self, analysis_text: str, memory_data: Dict[str, Any]) -> str:
        """Create fallback progress prompt if template is not available."""
        return f"""
Based on this construction analysis, provide a structured assessment:

ANALYSIS: {analysis_text}

PROJECT DATA:
- Days analyzed: {memory_data['total_days_analyzed']}
- Previous progress: {memory_data.get('overall_progress_percentage', 0)}%
- Current phase: {memory_data.get('current_phase', 'Unknown')}

Respond with ONLY valid JSON in this exact format:
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
"""
    
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