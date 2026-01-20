"""Core gradient mapping functions"""
import io
from pathlib import Path
from PIL import Image
import numpy as np


def apply_gradient_map(
    base_image_path, gradient_map_path, output_path, quality=95, output_format="PNG"
):
    """Apply a gradient map to a base image

    Args:
        base_image_path: Path to base image file
        gradient_map_path: Path to gradient map file
        output_path: Path where output should be saved
        quality: Image quality for JPEG/WebP (1-100)
        output_format: Output format (PNG, JPEG, WEBP)

    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        # Load images
        base_img = Image.open(base_image_path).convert("RGBA")
        gradient_img = Image.open(gradient_map_path).convert("RGB")

        # Resize gradient to 256x1 if needed
        gradient_img = gradient_img.resize((256, 1), Image.LANCZOS)

        # Convert to numpy arrays
        base_array = np.array(base_img)
        gradient_array = np.array(gradient_img)[0]  # Get first row

        # Extract RGB and alpha channels
        rgb = base_array[:, :, :3]
        alpha = base_array[:, :, 3]

        # Calculate luminance (grayscale value) using standard weights
        luminance = (
            rgb[:, :, 0] * 0.299 + rgb[:, :, 1] * 0.587 + rgb[:, :, 2] * 0.114
        ).astype(np.uint8)

        # Apply gradient map by using luminance as index
        output_rgb = gradient_array[luminance]

        # Combine with original alpha channel
        output_array = np.dstack([output_rgb, alpha])

        # Create and save output image
        output_img = Image.fromarray(output_array.astype(np.uint8), "RGBA")

        # Save with appropriate format and quality
        save_kwargs = {}
        if output_format.upper() in ["JPEG", "JPG"]:
            # Convert RGBA to RGB for JPEG
            output_img = output_img.convert("RGB")
            save_kwargs["quality"] = quality
            save_kwargs["optimize"] = True
        elif output_format.upper() == "PNG":
            save_kwargs["optimize"] = True
        elif output_format.upper() == "WEBP":
            save_kwargs["quality"] = quality
            save_kwargs["method"] = 6

        output_img.save(output_path, output_format.upper(), **save_kwargs)

        return True, f"✓ Created: {output_path.name if hasattr(output_path, 'name') else output_path}"

    except Exception as e:
        return False, f"✗ Error processing {base_image_path.name if hasattr(base_image_path, 'name') else base_image_path}: {e}"


def apply_gradient_map_from_memory(
    base_image_bytes, gradient_map_path, quality=95, output_format="PNG", max_dimension=None
):
    """Apply a gradient map to an image in memory (for web use)

    Args:
        base_image_bytes: Image data as bytes or BytesIO
        gradient_map_path: Path to gradient map file
        quality: Image quality for JPEG/WebP (1-100)
        output_format: Output format (PNG, JPEG, WEBP)
        max_dimension: Optional max width/height for resizing (for preview)

    Returns:
        bytes: Processed image as bytes
    """
    # Load base image from bytes
    if isinstance(base_image_bytes, bytes):
        base_img = Image.open(io.BytesIO(base_image_bytes)).convert("RGBA")
    else:
        base_img = Image.open(base_image_bytes).convert("RGBA")

    # Resize if max_dimension specified (for previews)
    if max_dimension:
        base_img.thumbnail((max_dimension, max_dimension), Image.LANCZOS)

    # Load gradient
    gradient_img = Image.open(gradient_map_path).convert("RGB")
    gradient_img = gradient_img.resize((256, 1), Image.LANCZOS)

    # Convert to numpy arrays
    base_array = np.array(base_img)
    gradient_array = np.array(gradient_img)[0]

    # Extract RGB and alpha channels
    rgb = base_array[:, :, :3]
    alpha = base_array[:, :, 3]

    # Calculate luminance
    luminance = (
        rgb[:, :, 0] * 0.299 + rgb[:, :, 1] * 0.587 + rgb[:, :, 2] * 0.114
    ).astype(np.uint8)

    # Apply gradient map
    output_rgb = gradient_array[luminance]
    output_array = np.dstack([output_rgb, alpha])

    # Create output image
    output_img = Image.fromarray(output_array.astype(np.uint8), "RGBA")

    # Save to bytes
    save_kwargs = {}
    if output_format.upper() in ["JPEG", "JPG"]:
        output_img = output_img.convert("RGB")
        save_kwargs["quality"] = quality
        save_kwargs["optimize"] = True
    elif output_format.upper() == "PNG":
        save_kwargs["optimize"] = True
    elif output_format.upper() == "WEBP":
        save_kwargs["quality"] = quality
        save_kwargs["method"] = 6

    output_bytes = io.BytesIO()
    output_img.save(output_bytes, output_format.upper(), **save_kwargs)
    return output_bytes.getvalue()
