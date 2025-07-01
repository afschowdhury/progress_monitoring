"""
Advanced parallel processing utilities for construction progress monitoring.
Inspired by OpenAI cookbook patterns for handling large-scale API requests.
"""

import asyncio
import concurrent.futures
import json
import logging
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from queue import Empty, Queue
from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple

from ..config import AnalysisConfig


@dataclass
class ProcessingJob:
    """Represents a single processing job."""

    job_id: str
    images: List[Dict[str, Any]]
    prompt: str
    priority: int = 0
    created_at: float = field(default_factory=time.time)
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class ProcessingResult:
    """Result of a processing job."""

    job_id: str
    success: bool
    result: Optional[str] = None
    error: Optional[str] = None
    processing_time: float = 0.0
    retry_count: int = 0


class RateLimiter:
    """Rate limiter for API requests."""

    def __init__(self, requests_per_minute: int = 20, requests_per_day: int = 1000):
        self.requests_per_minute = requests_per_minute
        self.requests_per_day = requests_per_day
        self.request_times = []
        self.lock = threading.Lock()

    def can_make_request(self) -> bool:
        """Check if a request can be made without exceeding rate limits."""
        current_time = time.time()

        with self.lock:
            # Remove old requests outside the time windows
            self.request_times = [
                t for t in self.request_times if current_time - t < 86400  # 24 hours
            ]

            # Check daily limit
            if len(self.request_times) >= self.requests_per_day:
                return False

            # Check per-minute limit
            recent_requests = [
                t for t in self.request_times if current_time - t < 60  # 1 minute
            ]

            if len(recent_requests) >= self.requests_per_minute:
                return False

            return True

    def record_request(self):
        """Record that a request was made."""
        with self.lock:
            self.request_times.append(time.time())

    def get_wait_time(self) -> float:
        """Get the time to wait before the next request can be made."""
        current_time = time.time()

        with self.lock:
            # Check per-minute limit
            recent_requests = [t for t in self.request_times if current_time - t < 60]

            if len(recent_requests) >= self.requests_per_minute:
                # Wait until the oldest request is more than 1 minute old
                oldest_recent = min(recent_requests)
                return 60 - (current_time - oldest_recent)

            return 0.0


class ParallelImageProcessor:
    """Advanced parallel processor for image analysis with rate limiting."""

    def __init__(self, config: AnalysisConfig, max_workers: int = 3):
        self.config = config
        self.max_workers = max_workers
        self.logger = logging.getLogger(self.__class__.__name__)

        # Rate limiting
        self.rate_limiter = RateLimiter()

        # Job queue and results
        self.job_queue = Queue()
        self.results: Dict[str, ProcessingResult] = {}
        self.results_lock = threading.Lock()

        # Processing state
        self.is_processing = False
        self.workers: List[threading.Thread] = []

        # Statistics
        self.stats = {
            "jobs_processed": 0,
            "jobs_failed": 0,
            "total_processing_time": 0.0,
            "start_time": None,
        }

    def add_job(self, job: ProcessingJob):
        """Add a job to the processing queue."""
        self.job_queue.put(job)
        self.logger.info(f"Added job {job.job_id} to queue")

    def start_processing(self, ai_provider):
        """Start the parallel processing workers."""
        if self.is_processing:
            self.logger.warning("Processing already started")
            return

        self.is_processing = True
        self.stats["start_time"] = time.time()

        # Start worker threads
        for i in range(self.max_workers):
            worker = threading.Thread(
                target=self._worker_loop, args=(ai_provider,), name=f"Worker-{i}"
            )
            worker.daemon = True
            worker.start()
            self.workers.append(worker)

        self.logger.info(f"Started {self.max_workers} worker threads")

    def stop_processing(self):
        """Stop the parallel processing workers."""
        self.is_processing = False

        # Wait for workers to finish
        for worker in self.workers:
            worker.join(timeout=5)

        self.logger.info("Stopped all worker threads")

    def _worker_loop(self, ai_provider):
        """Main worker loop for processing jobs."""
        while self.is_processing:
            try:
                # Get job from queue with timeout
                job = self.job_queue.get(timeout=1)
                self._process_job(job, ai_provider)
                self.job_queue.task_done()

            except Empty:
                continue
            except Exception as e:
                self.logger.error(f"Worker error: {e}")

    def _process_job(self, job: ProcessingJob, ai_provider):
        """Process a single job."""
        start_time = time.time()

        try:
            # Wait for rate limit
            while not self.rate_limiter.can_make_request():
                wait_time = self.rate_limiter.get_wait_time()
                if wait_time > 0:
                    self.logger.info(f"Rate limited, waiting {wait_time:.2f} seconds")
                    time.sleep(wait_time)

            # Record request
            self.rate_limiter.record_request()

            # Process the job
            result_text = ai_provider.analyze_images(job.images, job.prompt)

            # Create success result
            processing_time = time.time() - start_time
            result = ProcessingResult(
                job_id=job.job_id,
                success=True,
                result=result_text,
                processing_time=processing_time,
                retry_count=job.retry_count,
            )

            self.logger.info(
                f"Job {job.job_id} completed successfully in {processing_time:.2f}s"
            )

        except Exception as e:
            # Handle failure
            processing_time = time.time() - start_time
            error_msg = str(e)

            # Retry logic
            if job.retry_count < job.max_retries:
                job.retry_count += 1
                job.priority += 1  # Increase priority for retries
                self.job_queue.put(job)
                self.logger.warning(
                    f"Job {job.job_id} failed, retrying ({job.retry_count}/{job.max_retries}): {error_msg}"
                )
                return

            # Final failure
            result = ProcessingResult(
                job_id=job.job_id,
                success=False,
                error=error_msg,
                processing_time=processing_time,
                retry_count=job.retry_count,
            )

            self.logger.error(
                f"Job {job.job_id} failed permanently after {job.retry_count} retries: {error_msg}"
            )

        # Store result
        with self.results_lock:
            self.results[job.job_id] = result
            self.stats["jobs_processed"] += 1
            self.stats["total_processing_time"] += processing_time

            if not result.success:
                self.stats["jobs_failed"] += 1

    def get_result(self, job_id: str) -> Optional[ProcessingResult]:
        """Get the result for a specific job."""
        with self.results_lock:
            return self.results.get(job_id)

    def get_all_results(self) -> Dict[str, ProcessingResult]:
        """Get all processing results."""
        with self.results_lock:
            return self.results.copy()

    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        with self.results_lock:
            stats = self.stats.copy()
            if stats["start_time"]:
                stats["elapsed_time"] = time.time() - stats["start_time"]
                if stats["jobs_processed"] > 0:
                    stats["avg_processing_time"] = (
                        stats["total_processing_time"] / stats["jobs_processed"]
                    )
            return stats

    def wait_for_completion(self, timeout: Optional[float] = None) -> bool:
        """Wait for all jobs to complete."""
        start_time = time.time()

        while not self.job_queue.empty():
            if timeout and (time.time() - start_time) > timeout:
                return False
            time.sleep(0.1)

        return True


def create_batch_jobs(
    images: List[Dict[str, Any]], prompt: str, batch_size: int = 10
) -> List[ProcessingJob]:
    """Create batch jobs from a list of images."""
    jobs = []

    for i in range(0, len(images), batch_size):
        batch = images[i : i + batch_size]
        job_id = f"batch_{i//batch_size + 1}_{len(images)}"

        job = ProcessingJob(job_id=job_id, images=batch, prompt=prompt)
        jobs.append(job)

    return jobs


def process_images_parallel(
    images: List[Dict[str, Any]],
    prompt: str,
    ai_provider,
    config: AnalysisConfig,
    max_workers: int = 3,
    batch_size: int = 10,
) -> str:
    """Process images in parallel with rate limiting."""
    processor = ParallelImageProcessor(config, max_workers)

    try:
        # Create batch jobs
        jobs = create_batch_jobs(images, prompt, batch_size)

        # Add jobs to processor
        for job in jobs:
            processor.add_job(job)

        # Start processing
        processor.start_processing(ai_provider)

        # Wait for completion
        processor.wait_for_completion()

        # Collect results
        results = processor.get_all_results()
        successful_results = [
            result.result for result in results.values() if result.success
        ]

        # Combine results
        combined_analysis = "\n\n".join(successful_results)

        # Log statistics
        stats = processor.get_stats()
        logging.info(f"Parallel processing completed: {stats}")

        return combined_analysis

    finally:
        processor.stop_processing()
