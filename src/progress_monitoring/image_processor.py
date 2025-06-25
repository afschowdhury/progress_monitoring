"""
Image processing module for construction progress monitoring.
"""
import os
import base64
import logging
from pathlib import Path
from typing import List, Dict, Any

from .config import AnalysisConfig


class ImageProcessor:
    """Handles image file processing and preparation."""
    
    def __init__(self, config: AnalysisConfig):
        self.config = config
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.webp', '.heic', '.heif'}
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def get_image_files(self, folder_path: str) -> List[str]:
        """Get all supported image files from folder."""
        folder = Path(folder_path)
        if not folder.exists():
            raise FileNotFoundError(f"Folder not found: {folder_path}")
        
        image_files = []
        for file_path in folder.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in self.supported_formats:
                image_files.append(str(file_path))
        
        if not image_files:
            raise ValueError(f"No supported image files found in {folder_path}")
        
        image_files.sort()
        self.logger.info(f"Found {len(image_files)} image files")
        return image_files
    
    def prepare_images(self, image_files: List[str]) -> List[Dict[str, Any]]:
        """Prepare images for AI analysis."""
        prepared_images = []
        max_size_bytes = self.config.max_file_size_mb * 1024 * 1024
        
        for image_path in image_files[:self.config.max_images_per_request]:
            try:
                file_size = os.path.getsize(image_path)
                mime_type = self._get_mime_type(image_path)
                
                if file_size > max_size_bytes:
                    # Use file upload method for large files
                    image_data = {
                        'path': image_path,
                        'method': 'file_upload',
                        'mime_type': mime_type,
                        'size': file_size
                    }
                else:
                    # Use inline/base64 method for smaller files
                    with open(image_path, 'rb') as f:
                        image_bytes = f.read()
                    
                    image_data = {
                        'path': image_path,
                        'method': 'base64',
                        'data': image_bytes,
                        'base64_data': base64.b64encode(image_bytes).decode('utf-8'),
                        'mime_type': mime_type,
                        'size': file_size
                    }
                
                prepared_images.append(image_data)
                self.logger.info(f"Prepared image: {image_path} ({file_size} bytes)")
                
            except Exception as e:
                self.logger.error(f"Failed to prepare image {image_path}: {e}")
                continue
        
        return prepared_images
    
    def _get_mime_type(self, image_path: str) -> str:
        """Get MIME type from file extension."""
        ext = Path(image_path).suffix.lower()
        mime_type_map = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg', 
            '.png': 'image/png',
            '.webp': 'image/webp',
            '.heic': 'image/heic',
            '.heif': 'image/heif'
        }
        return mime_type_map.get(ext, 'image/jpeg') 