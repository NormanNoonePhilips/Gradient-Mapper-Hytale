"""Preview generation and thumbnail creation"""
import io
import base64
from pathlib import Path
from PIL import Image
from .core import apply_gradient_map_from_memory


def generate_preview(image_data, gradient_path, max_dimension=400, quality=85, output_format="PNG"):
    """Generate a low-res preview of gradient-mapped image

    Args:
        image_data: Image data as bytes or file path
        gradient_path: Path to gradient map file
        max_dimension: Maximum width or height for preview (default: 400px)
        quality: Image quality for JPEG/WebP (1-100)
        output_format: Output format (PNG, JPEG, WEBP)

    Returns:
        bytes: Preview image as bytes
    """
    # If image_data is a path, read it
    if isinstance(image_data, (str, Path)):
        with open(image_data, 'rb') as f:
            image_data = f.read()

    # Apply gradient map with max_dimension for fast processing
    preview_bytes = apply_gradient_map_from_memory(
        image_data,
        gradient_path,
        quality=quality,
        output_format=output_format,
        max_dimension=max_dimension
    )

    return preview_bytes


def generate_preview_base64(image_data, gradient_path, max_dimension=400, quality=85, output_format="PNG"):
    """Generate a base64-encoded preview

    Args:
        image_data: Image data as bytes or file path
        gradient_path: Path to gradient map file
        max_dimension: Maximum width or height for preview
        quality: Image quality
        output_format: Output format

    Returns:
        str: Base64-encoded preview image with data URI prefix
    """
    preview_bytes = generate_preview(
        image_data, gradient_path, max_dimension, quality, output_format
    )

    # Convert to base64 with data URI
    b64_data = base64.b64encode(preview_bytes).decode('utf-8')
    mime_type = f"image/{output_format.lower()}"
    return f"data:{mime_type};base64,{b64_data}"


def create_thumbnail(gradient_path, size=(256, 10)):
    """Create a thumbnail of a gradient map

    Args:
        gradient_path: Path to gradient map file
        size: Tuple of (width, height) for thumbnail

    Returns:
        str: Base64-encoded thumbnail with data URI prefix
    """
    try:
        # Load gradient image
        gradient_img = Image.open(gradient_path).convert("RGB")

        # Resize to thumbnail size
        gradient_img = gradient_img.resize(size, Image.LANCZOS)

        # Convert to bytes
        output = io.BytesIO()
        gradient_img.save(output, format="PNG", optimize=True)
        thumbnail_bytes = output.getvalue()

        # Convert to base64
        b64_data = base64.b64encode(thumbnail_bytes).decode('utf-8')
        return f"data:image/png;base64,{b64_data}"

    except Exception as e:
        # Return empty data URI on error
        return f"data:image/png;base64,"


def get_image_dimensions(image_data):
    """Get dimensions of an image

    Args:
        image_data: Image data as bytes or file path

    Returns:
        tuple: (width, height)
    """
    if isinstance(image_data, (str, Path)):
        with Image.open(image_data) as img:
            return img.size
    else:
        with Image.open(io.BytesIO(image_data)) as img:
            return img.size
