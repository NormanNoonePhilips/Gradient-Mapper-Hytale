"""ZIP file creation service"""
import logging
import tempfile
import zipfile
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)


class ZipService:
    """Creates ZIP archives of processed images"""

    @staticmethod
    def create_archive(files: List[Path], archive_name: str = "output.zip") -> Path:
        """Create a ZIP archive of files

        Args:
            files: List of file paths to include
            archive_name: Name for the ZIP file

        Returns:
            Path to created ZIP file

        Raises:
            ValueError: If no files provided or files don't exist
        """
        if not files:
            raise ValueError("No files provided for ZIP archive")

        # Filter to only existing files
        existing_files = [f for f in files if f.exists()]

        if not existing_files:
            raise ValueError("None of the provided files exist")

        # Create temporary ZIP file
        temp_dir = Path(tempfile.gettempdir())
        zip_path = temp_dir / archive_name

        # Create ZIP
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in existing_files:
                # Add file with just the filename (no directory structure)
                zipf.write(file_path, arcname=file_path.name)

        logger.info(f"Created ZIP archive {zip_path} with {len(existing_files)} files")

        return zip_path

    @staticmethod
    def create_job_archive(job_id: str, output_files: List[Path]) -> Path:
        """Create a ZIP archive for a job's output files

        Args:
            job_id: Job ID
            output_files: List of output file paths

        Returns:
            Path to created ZIP file
        """
        archive_name = f"gradient_mapper_{job_id[:8]}.zip"
        return ZipService.create_archive(output_files, archive_name)
