"""REST API routes"""
import logging
from typing import List

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from lib.files import get_image_files
from lib.preview import generate_preview_base64, get_image_dimensions
from ..models.schemas import (
    GradientCatalog,
    ImageInfo,
    ImageListResponse,
    JobRequest,
    JobResponse,
    JobStatus,
    PreviewRequest,
    PreviewResponse,
    UploadResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")


# These will be set by the main app
gradient_scanner = None
job_queue = None
input_folder = None
output_folder = None


def set_dependencies(scanner, queue, inp_folder, out_folder):
    """Set dependencies (called from main.py)"""
    global gradient_scanner, job_queue, input_folder, output_folder
    gradient_scanner = scanner
    job_queue = queue
    input_folder = inp_folder
    output_folder = out_folder


@router.get("/gradients", response_model=GradientCatalog)
async def list_gradients():
    """List all available gradients organized by category"""
    if gradient_scanner is None:
        raise HTTPException(status_code=500, detail="Gradient scanner not initialized")

    try:
        catalog = gradient_scanner.get_catalog()
        return catalog
    except Exception as e:
        logger.error(f"Error listing gradients: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload", response_model=UploadResponse)
async def upload_images(files: List[UploadFile] = File(...)):
    """Upload images to input folder"""
    if input_folder is None:
        raise HTTPException(status_code=500, detail="Input folder not configured")

    # Ensure input folder exists
    input_folder.mkdir(parents=True, exist_ok=True)

    uploaded_files = []

    for file in files:
        # Validate file type
        if not file.content_type or not file.content_type.startswith("image/"):
            logger.warning(f"Skipping non-image file: {file.filename}")
            continue

        # Save file
        file_path = input_folder / file.filename
        content = await file.read()

        with open(file_path, "wb") as f:
            f.write(content)

        # Get file info
        try:
            dimensions = get_image_dimensions(file_path)
            file_info = ImageInfo(
                filename=file.filename,
                size=len(content),
                dimensions=dimensions
            )
            uploaded_files.append(file_info)
            logger.info(f"Uploaded {file.filename} ({len(content)} bytes)")
        except Exception as e:
            logger.error(f"Error processing {file.filename}: {e}")
            # Delete invalid file
            file_path.unlink(missing_ok=True)

    if not uploaded_files:
        raise HTTPException(status_code=400, detail="No valid image files uploaded")

    return UploadResponse(
        files=uploaded_files,
        message=f"Successfully uploaded {len(uploaded_files)} file(s)"
    )


@router.get("/images", response_model=ImageListResponse)
async def list_images():
    """List all images in input folder"""
    if input_folder is None:
        raise HTTPException(status_code=500, detail="Input folder not configured")

    try:
        # Get image files
        image_files = get_image_files(input_folder)

        images = []
        for img_path in image_files:
            full_path = input_folder / img_path
            if full_path.exists():
                try:
                    dimensions = get_image_dimensions(full_path)
                    size = full_path.stat().st_size

                    images.append(ImageInfo(
                        filename=img_path,
                        size=size,
                        dimensions=dimensions
                    ))
                except Exception as e:
                    logger.warning(f"Error reading {img_path}: {e}")

        return ImageListResponse(
            images=images,
            total_count=len(images)
        )

    except Exception as e:
        logger.error(f"Error listing images: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/images/{image_path:path}")
async def get_image(image_path: str):
    """Serve an uploaded image file"""
    if input_folder is None:
        raise HTTPException(status_code=500, detail="Input folder not configured")

    file_path = input_folder / image_path
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Image not found: {image_path}")

    return FileResponse(file_path)


@router.post("/preview", response_model=PreviewResponse)
async def generate_preview(request: PreviewRequest):
    """Generate a preview of gradient-mapped image"""
    if input_folder is None or gradient_scanner is None:
        raise HTTPException(status_code=500, detail="Service not configured")

    try:
        # Get image path
        image_path = input_folder / request.image_name
        if not image_path.exists():
            raise HTTPException(status_code=404, detail=f"Image not found: {request.image_name}")

        # Get gradient path
        gradient_path = gradient_scanner.get_gradient_path(request.gradient_path)
        if gradient_path is None:
            raise HTTPException(status_code=404, detail=f"Gradient not found: {request.gradient_path}")

        # Get original dimensions
        original_dimensions = get_image_dimensions(image_path)

        # Generate preview
        preview_base64 = generate_preview_base64(
            image_path,
            gradient_path,
            max_dimension=request.max_dimension,
            quality=85,
            output_format="PNG"
        )

        # Calculate preview dimensions
        width, height = original_dimensions
        if width > height:
            new_width = min(width, request.max_dimension)
            new_height = int(height * (new_width / width))
        else:
            new_height = min(height, request.max_dimension)
            new_width = int(width * (new_height / height))

        return PreviewResponse(
            preview_image=preview_base64,
            dimensions=(new_width, new_height),
            original_dimensions=original_dimensions
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating preview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/jobs", response_model=JobResponse)
async def create_job(job_request: JobRequest):
    """Submit a batch processing job"""
    if job_queue is None:
        raise HTTPException(status_code=500, detail="Job queue not configured")

    try:
        # Validate tasks
        if not job_request.tasks:
            raise HTTPException(status_code=400, detail="No tasks provided")

        # Create job
        job_id = await job_queue.create_job(job_request)

        return JobResponse(
            job_id=job_id,
            task_count=len(job_request.tasks),
            message=f"Job created with {len(job_request.tasks)} task(s)"
        )

    except Exception as e:
        logger.error(f"Error creating job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    """Get status of a job"""
    if job_queue is None:
        raise HTTPException(status_code=500, detail="Job queue not configured")

    status = job_queue.get_status(job_id)
    if status is None:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    return status


@router.get("/jobs/{job_id}/download")
async def download_job_results(job_id: str):
    """Download job results as ZIP file"""
    if job_queue is None:
        raise HTTPException(status_code=500, detail="Job queue not configured")

    # Get job status
    status = job_queue.get_status(job_id)
    if status is None:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    if status.status != "completed":
        raise HTTPException(status_code=400, detail=f"Job not completed (status: {status.status})")

    # Get output files
    output_files = job_queue.get_output_files(job_id)
    if not output_files:
        raise HTTPException(status_code=404, detail="No output files found")

    try:
        # Create ZIP archive
        from ..services.zip_service import ZipService
        zip_path = ZipService.create_job_archive(job_id, output_files)

        # Return ZIP file
        return FileResponse(
            zip_path,
            media_type="application/zip",
            filename=f"gradient_mapper_{job_id[:8]}.zip"
        )

    except Exception as e:
        logger.error(f"Error creating download: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/jobs/{job_id}")
async def cancel_job(job_id: str):
    """Cancel a running job"""
    if job_queue is None:
        raise HTTPException(status_code=500, detail="Job queue not configured")

    success = job_queue.cancel_job(job_id)
    if not success:
        raise HTTPException(status_code=400, detail="Job cannot be cancelled")

    return {"message": f"Job {job_id} cancelled"}
