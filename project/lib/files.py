"""File system operations for gradient mapper"""
import os
from pathlib import Path
from typing import Dict, List
from dataclasses import dataclass


@dataclass
class GradientInfo:
    """Information about a gradient file"""
    name: str
    category: str
    path: Path
    relative_path: str


def get_image_files(folder, extensions=(".png", ".jpg", ".jpeg", ".webp")):
    """Get all image files in a folder recursively

    Args:
        folder: Path to folder to scan
        extensions: Tuple of valid file extensions

    Returns:
        List of relative paths to image files
    """
    image_files = []
    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.lower().endswith(extensions):
                # Get relative path from the base folder
                rel_path = os.path.relpath(os.path.join(root, file), folder)
                image_files.append(rel_path)
    return image_files


def scan_gradients(gradient_folder: Path) -> Dict[str, List[GradientInfo]]:
    """Scan gradient folder and organize by category

    Args:
        gradient_folder: Path to gradient folder

    Returns:
        Dictionary mapping category names to list of GradientInfo objects
    """
    gradients_by_category = {}

    # Scan for gradient files
    for root, dirs, files in os.walk(gradient_folder):
        for file in files:
            if file.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                full_path = Path(root) / file
                relative_path = full_path.relative_to(gradient_folder)

                # Determine category from parent folder
                if relative_path.parent == Path("."):
                    # File is in root gradient folder
                    category = "Uncategorized"
                else:
                    # Use parent folder name as category
                    category = relative_path.parent.name

                # Create GradientInfo
                gradient_info = GradientInfo(
                    name=file,
                    category=category,
                    path=full_path,
                    relative_path=str(relative_path)
                )

                # Add to category
                if category not in gradients_by_category:
                    gradients_by_category[category] = []
                gradients_by_category[category].append(gradient_info)

    # Sort categories and gradients within each category
    sorted_categories = {}
    for category in sorted(gradients_by_category.keys()):
        sorted_categories[category] = sorted(
            gradients_by_category[category],
            key=lambda g: g.name
        )

    return sorted_categories


def ensure_folders(*folders):
    """Create folders if they don't exist

    Args:
        *folders: Variable number of Path objects or strings
    """
    for folder in folders:
        Path(folder).mkdir(parents=True, exist_ok=True)
