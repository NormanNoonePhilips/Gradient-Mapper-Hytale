"""Batch processing coordinator for gradient mapping"""
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import cpu_count
from pathlib import Path
from typing import Callable, List, Tuple, Optional
from dataclasses import dataclass

from .core import apply_gradient_map


@dataclass
class ProcessingTask:
    """A single gradient mapping task"""
    base_image_path: Path
    gradient_map_path: Path
    output_path: Path
    quality: int = 95
    output_format: str = "PNG"


class BatchProcessor:
    """Batch processing coordinator using ProcessPoolExecutor"""

    def __init__(self, max_workers: Optional[int] = None):
        """Initialize batch processor

        Args:
            max_workers: Number of worker processes (default: CPU count)
        """
        self.max_workers = max_workers or cpu_count()

    def process_single(self, task: ProcessingTask) -> Tuple[bool, str]:
        """Process a single task

        Args:
            task: ProcessingTask to execute

        Returns:
            tuple: (success: bool, message: str)
        """
        return apply_gradient_map(
            task.base_image_path,
            task.gradient_map_path,
            task.output_path,
            task.quality,
            task.output_format
        )

    def process_batch(
        self,
        tasks: List[ProcessingTask],
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        use_parallel: bool = True
    ) -> Tuple[int, int, List[str]]:
        """Process multiple tasks

        Args:
            tasks: List of ProcessingTask objects
            progress_callback: Optional callback function(current, total, message)
            use_parallel: Whether to use parallel processing

        Returns:
            tuple: (successful_count, failed_count, error_messages)
        """
        successful_count = 0
        failed_count = 0
        error_messages = []
        total = len(tasks)

        if not use_parallel or self.max_workers == 1:
            # Sequential processing
            for i, task in enumerate(tasks, 1):
                success, message = self.process_single(task)

                if progress_callback:
                    progress_callback(i, total, message)

                if success:
                    successful_count += 1
                else:
                    failed_count += 1
                    error_messages.append(message)

        else:
            # Parallel processing
            with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all tasks
                futures = {
                    executor.submit(self._process_task_wrapper, task): task
                    for task in tasks
                }

                # Process completed tasks
                completed = 0
                for future in as_completed(futures):
                    completed += 1
                    success, message = future.result()

                    if progress_callback:
                        progress_callback(completed, total, message)

                    if success:
                        successful_count += 1
                    else:
                        failed_count += 1
                        error_messages.append(message)

        return successful_count, failed_count, error_messages

    @staticmethod
    def _process_task_wrapper(task: ProcessingTask) -> Tuple[bool, str]:
        """Wrapper for processing task (needed for ProcessPoolExecutor)

        Args:
            task: ProcessingTask to execute

        Returns:
            tuple: (success: bool, message: str)
        """
        return apply_gradient_map(
            task.base_image_path,
            task.gradient_map_path,
            task.output_path,
            task.quality,
            task.output_format
        )
