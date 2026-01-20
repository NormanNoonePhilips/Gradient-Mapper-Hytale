"""Pydantic models for API requests and responses"""
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class GradientInfo(BaseModel):
    """Information about a gradient file"""
    name: str
    category: str
    path: str
    relative_path: str
    thumbnail: str  # base64 encoded thumbnail


class GradientCatalog(BaseModel):
    """Catalog of all available gradients"""
    categories: Dict[str, List[GradientInfo]]
    total_count: int


class ImageInfo(BaseModel):
    """Information about an uploaded image"""
    filename: str
    size: int  # bytes
    dimensions: tuple[int, int]  # (width, height)


class PreviewRequest(BaseModel):
    """Request to generate a preview"""
    image_name: str
    gradient_path: str
    max_dimension: int = Field(default=400, ge=100, le=2000)


class PreviewResponse(BaseModel):
    """Preview generation response"""
    preview_image: str  # base64 encoded image
    dimensions: tuple[int, int]
    original_dimensions: tuple[int, int]


class JobTask(BaseModel):
    """A single task in a batch job"""
    image_name: str
    gradient_path: str


class JobRequest(BaseModel):
    """Request to create a batch processing job"""
    tasks: List[JobTask]
    output_format: str = Field(default="png", pattern="^(png|jpeg|webp)$")
    quality: int = Field(default=95, ge=1, le=100)
    prefix: Optional[str] = None
    suffix: Optional[str] = None


class JobResponse(BaseModel):
    """Response when creating a job"""
    job_id: str
    task_count: int
    message: str


class JobStatus(BaseModel):
    """Current status of a job"""
    job_id: str
    status: str  # "queued", "processing", "completed", "failed", "cancelled"
    current: int
    total: int
    created_at: str
    completed_at: Optional[str] = None
    download_url: Optional[str] = None
    error_count: int = 0


class UploadResponse(BaseModel):
    """Response after file upload"""
    files: List[ImageInfo]
    message: str


class ImageListResponse(BaseModel):
    """List of available images"""
    images: List[ImageInfo]
    total_count: int
