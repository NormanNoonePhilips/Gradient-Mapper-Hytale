"""Job queue manager for batch processing"""
import asyncio
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, Optional
from dataclasses import dataclass, field

from lib.batch import BatchProcessor, ProcessingTask
from ..models.schemas import JobRequest, JobStatus

logger = logging.getLogger(__name__)


def _resolve_within(base: Path, relative_path: str) -> Path:
    base_resolved = base.resolve()
    candidate = (base / relative_path).resolve()
    try:
        candidate.relative_to(base_resolved)
    except ValueError as exc:
        raise ValueError(f"Invalid path: {relative_path}") from exc
    return candidate


def _safe_output_name(name: str) -> str:
    return Path(name).name


@dataclass
class Job:
    """Represents a batch processing job"""
    job_id: str
    tasks: list[ProcessingTask]
    status: str = "queued"  # queued, processing, completed, failed, cancelled
    current: int = 0
    total: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    error_count: int = 0
    output_files: list[Path] = field(default_factory=list)
    cancel_requested: bool = False


class JobQueue:
    """Manages batch processing jobs with progress tracking"""

    def __init__(self, input_folder: Path, gradient_folder: Path, output_folder: Path):
        """Initialize job queue

        Args:
            input_folder: Path to input folder
            gradient_folder: Path to gradient folder
            output_folder: Path to output folder
        """
        self.input_folder = input_folder
        self.gradient_folder = gradient_folder
        self.output_folder = output_folder
        self.jobs: Dict[str, Job] = {}
        self.progress_callbacks: Dict[str, list[Callable]] = {}
        self._batch_processor = BatchProcessor()

    async def create_job(self, job_request: JobRequest) -> str:
        """Create a new batch processing job

        Args:
            job_request: Job request with tasks and settings

        Returns:
            Job ID
        """
        job_id = str(uuid.uuid4())

        # Ensure output folder exists
        self.output_folder.mkdir(parents=True, exist_ok=True)

        # Build ProcessingTask objects
        tasks = []
        output_files = []

        for task_req in job_request.tasks:
            # Build input path
            input_path = _resolve_within(self.input_folder, task_req.image_name)
            if not input_path.exists():
                raise ValueError(f"Input image not found: {task_req.image_name}")

            # Build gradient path (could be relative)
            gradient_path = _resolve_within(self.gradient_folder, task_req.gradient_path)
            if not gradient_path.exists():
                raise ValueError(f"Gradient not found: {task_req.gradient_path}")

            # Build output filename
            base_name = Path(task_req.image_name).stem
            gradient_name = Path(task_req.gradient_path).stem

            if job_request.prefix:
                output_name = f"{job_request.prefix}_{base_name}_{gradient_name}"
            else:
                output_name = f"{base_name}_{gradient_name}"

            if job_request.suffix:
                output_name = f"{output_name}_{job_request.suffix}"

            output_name = f"{output_name}.{job_request.output_format}"
            output_name = _safe_output_name(output_name)
            output_path = self.output_folder / output_name

            # Create task
            processing_task = ProcessingTask(
                base_image_path=input_path,
                gradient_map_path=gradient_path,
                output_path=output_path,
                quality=job_request.quality,
                output_format=job_request.output_format
            )

            tasks.append(processing_task)
            output_files.append(output_path)

        # Create job
        job = Job(
            job_id=job_id,
            tasks=tasks,
            total=len(tasks),
            output_files=output_files
        )

        self.jobs[job_id] = job

        # Start processing in background
        asyncio.create_task(self._process_job(job_id))

        logger.info(f"Created job {job_id} with {len(tasks)} tasks")

        return job_id

    async def _process_job(self, job_id: str):
        """Process a job asynchronously

        Args:
            job_id: Job ID to process
        """
        job = self.jobs.get(job_id)
        if not job:
            logger.error(f"Job {job_id} not found")
            return

        try:
            if job.cancel_requested:
                job.status = "cancelled"
                job.completed_at = datetime.now().isoformat()
                await self._broadcast_cancelled(job_id)
                return

            job.status = "processing"
            await self._broadcast_progress(job_id, "Job started")

            loop = asyncio.get_running_loop()

            def _schedule_progress(current, total, message):
                job.current = current
                asyncio.create_task(self._broadcast_progress(job_id, message))

            # Progress callback for batch processor (runs in worker thread)
            def progress_callback(current, total, message):
                loop.call_soon_threadsafe(_schedule_progress, current, total, message)

            # Run batch processing in thread pool to avoid blocking
            successful_count, failed_count, error_messages = await loop.run_in_executor(
                None,
                lambda: self._batch_processor.process_batch(
                    job.tasks,
                    progress_callback=progress_callback,
                    use_parallel=True,
                    cancel_check=lambda: job.cancel_requested
                )
            )

            # Update job status
            if job.cancel_requested:
                job.status = "cancelled"
                job.completed_at = datetime.now().isoformat()
                await self._broadcast_cancelled(job_id)
                return

            job.error_count = failed_count
            if failed_count == len(job.tasks):
                job.status = "failed"
            elif failed_count > 0:
                job.status = "completed"  # Partial success
            else:
                job.status = "completed"

            job.completed_at = datetime.now().isoformat()

            # Broadcast completion
            await self._broadcast_complete(job_id)

            logger.info(f"Job {job_id} completed: {successful_count} success, {failed_count} failed")

        except Exception as e:
            logger.error(f"Job {job_id} failed with error: {e}")
            job.status = "failed"
            job.completed_at = datetime.now().isoformat()
            await self._broadcast_error(job_id, str(e))

    async def _broadcast_progress(self, job_id: str, message: str):
        """Broadcast progress update to all subscribers

        Args:
            job_id: Job ID
            message: Progress message
        """
        if job_id in self.progress_callbacks:
            job = self.jobs.get(job_id)
            if job:
                if job.cancel_requested:
                    return
                for callback in self.progress_callbacks[job_id]:
                    try:
                        await callback({
                            "type": "progress",
                            "job_id": job_id,
                            "current": job.current,
                            "total": job.total,
                            "status": job.status,
                            "message": message
                        })
                    except Exception as e:
                        logger.error(f"Error in progress callback: {e}")

    async def _broadcast_complete(self, job_id: str):
        """Broadcast job completion

        Args:
            job_id: Job ID
        """
        if job_id in self.progress_callbacks:
            for callback in self.progress_callbacks[job_id]:
                try:
                    await callback({
                        "type": "complete",
                        "job_id": job_id,
                        "download_url": f"/api/jobs/{job_id}/download"
                    })
                except Exception as e:
                    logger.error(f"Error in complete callback: {e}")

    async def _broadcast_cancelled(self, job_id: str):
        if job_id in self.progress_callbacks:
            for callback in self.progress_callbacks[job_id]:
                try:
                    await callback({
                        "type": "cancelled",
                        "job_id": job_id,
                        "message": "Cancelled"
                    })
                except Exception as e:
                    logger.error(f"Error in cancelled callback: {e}")

    async def _broadcast_error(self, job_id: str, error_message: str):
        """Broadcast job error

        Args:
            job_id: Job ID
            error_message: Error message
        """
        if job_id in self.progress_callbacks:
            for callback in self.progress_callbacks[job_id]:
                try:
                    await callback({
                        "type": "error",
                        "job_id": job_id,
                        "message": error_message
                    })
                except Exception as e:
                    logger.error(f"Error in error callback: {e}")

    def subscribe_progress(self, job_id: str, callback: Callable):
        """Subscribe to job progress updates

        Args:
            job_id: Job ID to subscribe to
            callback: Async callback function
        """
        if job_id not in self.progress_callbacks:
            self.progress_callbacks[job_id] = []
        self.progress_callbacks[job_id].append(callback)

    def unsubscribe_progress(self, job_id: str, callback: Callable):
        """Unsubscribe from job progress updates

        Args:
            job_id: Job ID
            callback: Callback to remove
        """
        if job_id in self.progress_callbacks:
            try:
                self.progress_callbacks[job_id].remove(callback)
            except ValueError:
                pass

    def get_status(self, job_id: str) -> Optional[JobStatus]:
        """Get job status

        Args:
            job_id: Job ID

        Returns:
            JobStatus object or None if not found
        """
        job = self.jobs.get(job_id)
        if not job:
            return None

        download_url = None
        if job.status == "completed":
            download_url = f"/api/jobs/{job_id}/download"

        return JobStatus(
            job_id=job.job_id,
            status=job.status,
            current=job.current,
            total=job.total,
            created_at=job.created_at,
            completed_at=job.completed_at,
            download_url=download_url,
            error_count=job.error_count
        )

    def get_output_files(self, job_id: str) -> Optional[list[Path]]:
        """Get output files for a job

        Args:
            job_id: Job ID

        Returns:
            List of output file paths, or None if job not found
        """
        job = self.jobs.get(job_id)
        if not job:
            return None

        # Return only files that actually exist
        return [f for f in job.output_files if f.exists()]

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a running job

        Args:
            job_id: Job ID to cancel

        Returns:
            True if cancelled, False if not found or already completed
        """
        job = self.jobs.get(job_id)
        if not job:
            return False

        if job.status in ["completed", "failed", "cancelled"]:
            return False

        job.cancel_requested = True
        job.status = "cancelled"
        job.completed_at = datetime.now().isoformat()

        logger.info(f"Job {job_id} cancelled")

        await self._broadcast_cancelled(job_id)

        return True
