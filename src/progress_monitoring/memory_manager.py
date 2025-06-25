"""
Memory management module for construction progress monitoring.
"""
import os
import json
import logging
from datetime import datetime
from typing import Dict, Any

from .config import AnalysisConfig


class MemoryManager:
    """Handles project memory and historical data."""
    
    def __init__(self, memory_file_path: str):
        self.memory_file_path = memory_file_path
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def read_memory(self) -> Dict[str, Any]:
        """Read historical construction data."""
        try:
            if os.path.exists(self.memory_file_path):
                with open(self.memory_file_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        return json.loads(content)
            
            return self._get_default_memory()
            
        except (json.JSONDecodeError, FileNotFoundError) as e:
            self.logger.warning(f"Could not read memory file: {e}")
            return self._get_default_memory()
    
    def write_memory(self, memory_data: Dict[str, Any]) -> None:
        """Write updated memory data."""
        try:
            with open(self.memory_file_path, 'w', encoding='utf-8') as f:
                json.dump(memory_data, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Memory updated: {self.memory_file_path}")
        except Exception as e:
            self.logger.error(f"Failed to write memory: {e}")
    
    def update_daily_report(self, memory_data: Dict[str, Any], date: str, 
                          analysis: str, images_count: int) -> Dict[str, Any]:
        """Update memory with daily report."""
        memory_data["total_days_analyzed"] += 1
        memory_data["daily_reports"][date] = {
            "summary": analysis[:500] + "..." if len(analysis) > 500 else analysis,
            "full_analysis": analysis,
            "images_analyzed": images_count,
            "timestamp": datetime.now().isoformat()
        }
        return memory_data
    
    def add_milestone(self, memory_data: Dict[str, Any], date: str, 
                     description: str, progress: float) -> Dict[str, Any]:
        """Add a milestone to memory."""
        if progress > 10:  # Only significant progress
            milestone = {
                "date": date,
                "description": description,
                "progress_percentage": progress
            }
            memory_data["key_milestones"].append(milestone)
        return memory_data
    
    def _get_default_memory(self) -> Dict[str, Any]:
        """Get default memory structure."""
        return {
            "project_start_date": None,
            "total_days_analyzed": 0,
            "daily_reports": {},
            "key_milestones": [],
            "current_phase": "Unknown",
            "overall_progress_percentage": 0
        } 