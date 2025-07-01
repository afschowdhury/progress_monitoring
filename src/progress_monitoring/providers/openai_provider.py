"""
OpenAI provider implementation with rate limiting and parallel processing.
"""

import asyncio
import base64
import concurrent.futures
import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from ..config import AnalysisConfig
from .base import AIProvider

# Add tenacity for retry logic
try:
    from tenacity import (
        before_sleep_log,
        retry,
        retry_if_exception_type,
        stop_after_attempt,
        wait_random_exponential,
    )

    TENACITY_AVAILABLE = True
except ImportError:
    TENACITY_AVAILABLE = False
    print("Warning: tenacity not installed. Install with: pip install tenacity")


@dataclass
class BatchConfig:
    """Configuration for batch processing."""

    max_images_per_batch: int = 10
    max_concurrent_requests: int = 3
    request_delay_seconds: float = 1.0
    max_retries: int = 6
    timeout_seconds: int = 60


class OpenAIProvider(AIProvider):
    """OpenAI provider implementation with rate limiting and parallel processing."""

    def __init__(self, config: AnalysisConfig):
        super().__init__(config)
        try:
            import openai

            self.client = openai.OpenAI(api_key=config.api_key)
        except ImportError:
            raise ImportError("Please install openai: pip install openai")

        # Batch processing configuration
        self.batch_config = BatchConfig()

        # Rate limiting state
        self.request_count = 0
        self.last_request_time = 0
        self.rate_limit_window = 60  # 1 minute window

    def _handle_rate_limit_error(self, e):
        """Handle rate limit errors with exponential backoff."""
        if not TENACITY_AVAILABLE:
            # Fallback to simple retry logic
            self.logger.warning("Tenacity not available, using simple retry logic")
            time.sleep(2)  # Simple 2-second delay
            return

        # Let tenacity handle the retry
        raise e

    def _is_rate_limit_error(self, exception) -> bool:
        """Check if the exception is a rate limit error."""
        error_str = str(exception).lower()
        return (
            "rate limit" in error_str
            or "429" in error_str
            or "too many requests" in error_str
            or "quota" in error_str
        )

    @(
        retry(
            wait=wait_random_exponential(min=1, max=60),
            stop=stop_after_attempt(6),
            retry=retry_if_exception_type(Exception),
            before_sleep=before_sleep_log(logging.getLogger(__name__), logging.WARNING),
        )
        if TENACITY_AVAILABLE
        else None
    )
    def _make_openai_request(self, messages: List[Dict], max_tokens: int = 4000) -> Any:
        """Make OpenAI API request with retry logic."""
        try:
            # Rate limiting: ensure minimum delay between requests
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            if time_since_last < self.batch_config.request_delay_seconds:
                sleep_time = self.batch_config.request_delay_seconds - time_since_last
                time.sleep(sleep_time)

            response = self.client.chat.completions.create(
                model=self.config.model_name,
                messages=messages,
                max_tokens=max_tokens,
                timeout=self.batch_config.timeout_seconds,
            )

            # Update rate limiting state
            self.last_request_time = time.time()
            self.request_count += 1

            return response

        except Exception as e:
            # Check if it's a rate limit error
            if self._is_rate_limit_error(e):
                self.logger.warning(f"Rate limit hit: {e}")
                self._handle_rate_limit_error(e)
            raise

    def _prepare_messages_for_batch(
        self, images: List[Dict[str, Any]], prompt: str
    ) -> List[Dict]:
        """Prepare messages for a batch of images."""
        messages = [{"role": "user", "content": [{"type": "text", "text": prompt}]}]

        # Add images to message content
        for img_data in images:
            if img_data["method"] == "base64":
                image_content = {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{img_data['mime_type']};base64,{img_data['base64_data']}"
                    },
                }
                messages[0]["content"].append(image_content)
            else:
                # For file uploads, we need to convert to base64
                with open(img_data["path"], "rb") as f:
                    image_bytes = f.read()
                base64_image = base64.b64encode(image_bytes).decode("utf-8")
                image_content = {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{img_data['mime_type']};base64,{base64_image}"
                    },
                }
                messages[0]["content"].append(image_content)

        return messages

    def _process_image_batch(
        self, image_batch: List[Dict[str, Any]], prompt: str
    ) -> str:
        """Process a single batch of images."""
        try:
            messages = self._prepare_messages_for_batch(image_batch, prompt)
            response = self._make_openai_request(messages, max_tokens=4000)
            return response.choices[0].message.content
        except Exception as e:
            self.logger.error(f"Failed to process image batch: {e}")
            raise

    def _split_images_into_batches(
        self, images: List[Dict[str, Any]]
    ) -> List[List[Dict[str, Any]]]:
        """Split images into batches for parallel processing."""
        batches = []
        batch_size = self.batch_config.max_images_per_batch

        for i in range(0, len(images), batch_size):
            batch = images[i : i + batch_size]
            batches.append(batch)

        self.logger.info(f"Split {len(images)} images into {len(batches)} batches")
        return batches

    def analyze_images(self, images: List[Dict[str, Any]], prompt: str) -> str:
        """Analyze images using OpenAI GPT-4 Vision with parallel processing."""
        try:
            if len(images) <= self.batch_config.max_images_per_batch:
                # Single batch - use simple processing
                self.logger.info(f"Processing {len(images)} images in single batch")
                return self._process_image_batch(images, prompt)

            # Multiple batches - use parallel processing
            self.logger.info(f"Processing {len(images)} images in parallel batches")
            batches = self._split_images_into_batches(images)

            # Process batches in parallel with rate limiting
            results = []
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=self.batch_config.max_concurrent_requests
            ) as executor:
                # Submit all batch processing tasks
                future_to_batch = {
                    executor.submit(self._process_image_batch, batch, prompt): i
                    for i, batch in enumerate(batches)
                }

                # Collect results as they complete
                for future in concurrent.futures.as_completed(future_to_batch):
                    batch_index = future_to_batch[future]
                    try:
                        result = future.result()
                        results.append((batch_index, result))
                        self.logger.info(
                            f"Completed batch {batch_index + 1}/{len(batches)}"
                        )
                    except Exception as e:
                        self.logger.error(f"Batch {batch_index + 1} failed: {e}")
                        raise

            # Sort results by batch index and combine
            results.sort(key=lambda x: x[0])
            combined_analysis = "\n\n".join([result[1] for result in results])

            return combined_analysis

        except Exception as e:
            self.logger.error(f"OpenAI analysis failed: {e}")
            raise

    def generate_structured_response(self, prompt: str) -> str:
        """Generate structured response using OpenAI with rate limiting."""
        try:
            messages = [{"role": "user", "content": prompt}]

            # Call OpenAI API with retry logic
            response = self._make_openai_request(messages, max_tokens=2000)

            # Validate response
            if not response or not response.choices:
                self.logger.error("OpenAI response is empty or invalid")
                raise ValueError("Empty response from OpenAI API")

            response_text = response.choices[0].message.content
            if not response_text or response_text.strip() == "":
                self.logger.error("OpenAI response text is empty")
                raise ValueError("Empty response text from OpenAI API")

            return response_text.strip()

        except Exception as e:
            self.logger.error(f"OpenAI structured response failed: {e}")
            raise

    def set_batch_config(self, config: BatchConfig):
        """Update batch processing configuration."""
        self.batch_config = config
        self.logger.info(f"Updated batch config: {config}")

    def get_rate_limit_stats(self) -> Dict[str, Any]:
        """Get current rate limiting statistics."""
        return {
            "request_count": self.request_count,
            "last_request_time": self.last_request_time,
            "time_since_last_request": time.time() - self.last_request_time,
            "batch_config": self.batch_config,
        }
