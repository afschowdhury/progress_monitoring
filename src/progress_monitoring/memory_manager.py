"""
Enhanced memory management module with Qdrant vector database and embeddings support.
"""
import json
import logging
import os
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models
    from qdrant_client.http.models import Distance, VectorParams
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False

from .config import AnalysisConfig


class MemoryManager:
    """Enhanced memory manager with vector database and embeddings support."""
    
    def __init__(self, memory_file_path: str, qdrant_host: str = "localhost", qdrant_port: int = 6333):
        self.memory_file_path = memory_file_path
        self.qdrant_host = qdrant_host
        self.qdrant_port = qdrant_port
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize components
        self.qdrant_client = None
        self.embedding_model = None
        self.collection_name = "progress_monitoring"
        
        # Initialize Qdrant and embeddings
        self._initialize_qdrant()
        self._initialize_embeddings()
    
    def _initialize_qdrant(self) -> None:
        """Initialize Qdrant client and collection."""
        if not QDRANT_AVAILABLE:
            self.logger.warning("Qdrant client not available. Install with: pip install qdrant-client")
            return
            
        try:
            self.qdrant_client = QdrantClient(host=self.qdrant_host, port=self.qdrant_port)
            
            # Check if collection exists, create if not
            collections = self.qdrant_client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.collection_name not in collection_names:
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=384, distance=Distance.COSINE),
                )
                self.logger.info(f"Created Qdrant collection: {self.collection_name}")
            else:
                self.logger.info(f"Using existing Qdrant collection: {self.collection_name}")
                
        except Exception as e:
            self.logger.warning(f"Failed to initialize Qdrant: {e}")
            self.qdrant_client = None
    
    def _initialize_embeddings(self) -> None:
        """Initialize sentence transformer model for embeddings."""
        if not EMBEDDINGS_AVAILABLE:
            self.logger.warning("Sentence transformers not available. Install with: pip install sentence-transformers")
            return
            
        try:
            # Use a lightweight, fast model for embeddings
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            self.logger.info("Initialized embedding model: all-MiniLM-L6-v2")
        except Exception as e:
            self.logger.warning(f"Failed to initialize embedding model: {e}")
            self.embedding_model = None
    
    def _date_to_timestamp(self, date_str: str) -> float:
        """Convert date string to Unix timestamp."""
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            return time.mktime(dt.timetuple())
        except ValueError:
            # If parsing fails, try to parse as datetime
            try:
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                return dt.timestamp()
            except ValueError:
                # Fallback: return current timestamp
                self.logger.warning(f"Could not parse date '{date_str}', using current timestamp")
                return time.time()
    
    def store_progress_report(
        self,
        date: str,
        image_folder_path: str,
        analysis_content: str,
        progress_report: Dict[str, Any],
        day_number: Optional[int] = None,
        config_info: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store a complete progress report with embeddings.
        
        Args:
            date: Analysis date
            image_folder_path: Path to analyzed images
            analysis_content: Full analysis text from ImageAnalyzer
            progress_report: Structured progress report from ProgressReportGenerator
            day_number: Day number if applicable
            config_info: Configuration used to generate this content
            
        Returns:
            Unique ID of the stored record
        """
        try:
            # Generate unique ID
            record_id = str(uuid.uuid4())
            
            # Create analysis summary
            analysis_summary = self._generate_summary(analysis_content, "analysis")
            
            # Create progress summary
            progress_summary = self._generate_summary(
                json.dumps(progress_report, indent=2), "progress"
            )
            
            # Prepare record
            record = {
                "id": record_id,
                "date": date,
                "date_timestamp": self._date_to_timestamp(date),
                "day_number": day_number,
                "image_folder_path": image_folder_path,
                "analysis_content": analysis_content,
                "analysis_summary": analysis_summary,
                "progress_report": progress_report,
                "progress_summary": progress_summary,
                "config_info": config_info or {},
                "timestamp": datetime.now().isoformat(),
                "record_type": "progress_report"
            }
            
            # Store in Qdrant with embeddings
            if self.qdrant_client and self.embedding_model:
                self._store_in_qdrant(record)
            
            # Also store in JSON file as backup
            self._store_in_json(record)
            
            self.logger.info(f"Stored progress report for {date} with ID: {record_id}")
            return record_id
            
        except Exception as e:
            self.logger.error(f"Failed to store progress report: {e}")
            return ""
    
    def store_analysis_report(
        self,
        date: str,
        image_folder_path: str,
        analysis_content: str,
        images_count: int,
        day_number: Optional[int] = None,
        config_info: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store an analysis report with embeddings.
        
        Args:
            date: Analysis date
            image_folder_path: Path to analyzed images
            analysis_content: Analysis text content
            images_count: Number of images analyzed
            day_number: Day number if applicable
            config_info: Configuration used to generate this content
            
        Returns:
            Unique ID of the stored record
        """
        try:
            # Generate unique ID
            record_id = str(uuid.uuid4())
            
            # Create analysis summary
            analysis_summary = self._generate_summary(analysis_content, "analysis")
            
            # Prepare record
            record = {
                "id": record_id,
                "date": date,
                "date_timestamp": self._date_to_timestamp(date),
                "day_number": day_number,
                "image_folder_path": image_folder_path,
                "analysis_content": analysis_content,
                "analysis_summary": analysis_summary,
                "images_count": images_count,
                "config_info": config_info or {},
                "timestamp": datetime.now().isoformat(),
                "record_type": "analysis_report"
            }
            
            # Store in Qdrant with embeddings
            if self.qdrant_client and self.embedding_model:
                self._store_in_qdrant(record)
            
            # Also store in JSON file as backup
            self._store_in_json(record)
            
            self.logger.info(f"Stored analysis report for {date} with ID: {record_id}")
            return record_id
            
        except Exception as e:
            self.logger.error(f"Failed to store analysis report: {e}")
            return ""
    
    def search_similar_reports(
        self, 
        query: str, 
        limit: int = 5,
        record_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar reports using semantic search.
        
        Args:
            query: Search query
            limit: Maximum number of results
            record_type: Filter by record type ("progress_report" or "analysis_report")
            
        Returns:
            List of similar reports
        """
        if not self.qdrant_client or not self.embedding_model:
            self.logger.warning("Qdrant or embeddings not available for search")
            return self._fallback_search(query, limit, record_type)
            
        try:
            # Generate query embedding
            query_vector = self.embedding_model.encode(query).tolist()
            
            # Prepare search filter
            search_filter = None
            if record_type:
                search_filter = models.Filter(
                    must=[
                        models.FieldCondition(
                            key="record_type",
                            match=models.MatchValue(value=record_type),
                        )
                    ]
                )
            
            # Search in Qdrant
            search_result = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=search_filter,
                limit=limit,
                with_payload=True,
            )
            
            # Extract and return results
            results = []
            for hit in search_result:
                result = hit.payload.copy()
                result["similarity_score"] = hit.score
                results.append(result)
                
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to search reports: {e}")
            return self._fallback_search(query, limit, record_type)
    
    def get_recent_reports(
        self, 
        days: int = 7,
        record_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get recent reports from the last N days.
        
        Args:
            days: Number of days to look back
            record_type: Filter by record type
            
        Returns:
            List of recent reports
        """
        if not self.qdrant_client:
            return self._fallback_get_recent(days, record_type)
            
        try:
            # Calculate date threshold as Unix timestamp
            from datetime import datetime, timedelta
            threshold_datetime = datetime.now() - timedelta(days=days)
            threshold_timestamp = time.mktime(threshold_datetime.timetuple())
            
            # Search with date timestamp filter
            search_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="date_timestamp",
                        range=models.Range(gte=threshold_timestamp)
                    )
                ]
            )
            
            if record_type:
                search_filter.must.append(
                    models.FieldCondition(
                        key="record_type",
                        match=models.MatchValue(value=record_type)
                    )
                )
            
            # Get results
            scroll_result = self.qdrant_client.scroll(
                collection_name=self.collection_name,
                scroll_filter=search_filter,
                limit=100,
                with_payload=True,
            )
            
            results = [hit.payload for hit in scroll_result[0]]
            
            # Sort by date descending
            results.sort(key=lambda x: x.get("date", ""), reverse=True)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to get recent reports: {e}")
            return self._fallback_get_recent(days, record_type)
    
    def get_project_memory(self) -> Dict[str, Any]:
        """Get comprehensive project memory including summaries and statistics."""
        try:
            # Get basic memory from JSON file
            basic_memory = self.read_memory()
            
            # Enhance with vector database information
            if self.qdrant_client:
                # Get collection info
                collection_info = self.qdrant_client.get_collection(self.collection_name)
                basic_memory["vector_db_stats"] = {
                    "total_records": collection_info.vectors_count,
                    "indexed_records": collection_info.indexed_vectors_count,
                }
                
                # Get recent summaries
                recent_reports = self.get_recent_reports(days=30)
                
                # Generate overall project summary
                if recent_reports:
                    progress_reports = [r for r in recent_reports if r.get("record_type") == "progress_report"]
                    analysis_reports = [r for r in recent_reports if r.get("record_type") == "analysis_report"]
                    
                    basic_memory["recent_summary"] = {
                        "total_progress_reports": len(progress_reports),
                        "total_analysis_reports": len(analysis_reports),
                        "latest_progress": progress_reports[0] if progress_reports else None,
                        "latest_analysis": analysis_reports[0] if analysis_reports else None,
                    }
            
            return basic_memory
            
        except Exception as e:
            self.logger.error(f"Failed to get project memory: {e}")
            return self.read_memory()
    
    def _store_in_qdrant(self, record: Dict[str, Any]) -> None:
        """Store record in Qdrant with embeddings."""
        try:
            # Create text for embedding (combine key fields)
            embedding_text = f"{record.get('analysis_summary', '')} {record.get('progress_summary', '')}"
            if not embedding_text.strip():
                embedding_text = record.get('analysis_content', '')[:1000]  # First 1000 chars
            
            # Generate embedding
            embedding_vector = self.embedding_model.encode(embedding_text).tolist()
            
            # Store in Qdrant
            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=[
                    models.PointStruct(
                        id=record["id"],
                        vector=embedding_vector,
                        payload=record,
                    )
                ],
            )
            
        except Exception as e:
            self.logger.error(f"Failed to store in Qdrant: {e}")
    
    def _store_in_json(self, record: Dict[str, Any]) -> None:
        """Store record in JSON file as backup."""
        try:
            # Read existing data
            existing_data = self.read_memory()
            
            # Add to records
            if "records" not in existing_data:
                existing_data["records"] = []
            
            existing_data["records"].append(record)
            
            # Keep only last 100 records in JSON (Qdrant has the full history)
            existing_data["records"] = existing_data["records"][-100:]
            
            # Update metadata
            existing_data["last_updated"] = datetime.now().isoformat()
            existing_data["total_records"] = len(existing_data["records"])
            
            # Write back
            self.write_memory(existing_data)
            
        except Exception as e:
            self.logger.error(f"Failed to store in JSON: {e}")
    
    def _generate_summary(self, content: str, content_type: str) -> str:
        """Generate a summary of the content."""
        if not content:
            return ""
            
        # Simple extractive summary - take first 3 sentences
        sentences = content.split('. ')
        summary_sentences = sentences[:3]
        summary = '. '.join(summary_sentences)
        
        if len(summary) > 500:
            summary = summary[:500] + "..."
            
        return summary
    
    def _fallback_search(self, query: str, limit: int, record_type: Optional[str]) -> List[Dict[str, Any]]:
        """Fallback search using JSON data when Qdrant is not available."""
        try:
            data = self.read_memory()
            records = data.get("records", [])
            
            # Filter by record type if specified
            if record_type:
                records = [r for r in records if r.get("record_type") == record_type]
            
            # Simple text search
            query_lower = query.lower()
            matching_records = []
            
            for record in records:
                content = f"{record.get('analysis_content', '')} {record.get('analysis_summary', '')} {record.get('progress_summary', '')}"
                if query_lower in content.lower():
                    matching_records.append(record)
            
            return matching_records[:limit]
            
        except Exception as e:
            self.logger.error(f"Fallback search failed: {e}")
            return []
    
    def _fallback_get_recent(self, days: int, record_type: Optional[str]) -> List[Dict[str, Any]]:
        """Fallback method to get recent reports when Qdrant is not available."""
        try:
            data = self.read_memory()
            records = data.get("records", [])
            
            # Filter by record type if specified
            if record_type:
                records = [r for r in records if r.get("record_type") == record_type]
            
            # Sort by date and return recent ones
            records.sort(key=lambda x: x.get("date", ""), reverse=True)
            
            return records[:days * 2]  # Approximate recent records
            
        except Exception as e:
            self.logger.error(f"Fallback get recent failed: {e}")
            return []
    
    # Legacy methods for backward compatibility
    def read_memory(self) -> Dict[str, Any]:
        """Read historical construction data from JSON file."""
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
        """Write updated memory data to JSON file."""
        try:
            with open(self.memory_file_path, 'w', encoding='utf-8') as f:
                json.dump(memory_data, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Memory updated: {self.memory_file_path}")
        except Exception as e:
            self.logger.error(f"Failed to write memory: {e}")
    
    def update_daily_report(self, memory_data: Dict[str, Any], date: str, 
                          analysis: str, images_count: int) -> Dict[str, Any]:
        """Update memory with daily report (legacy method)."""
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
        """Add a milestone to memory (legacy method)."""
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
            "overall_progress_percentage": 0,
            "records": [],
            "last_updated": datetime.now().isoformat(),
            "total_records": 0
        } 