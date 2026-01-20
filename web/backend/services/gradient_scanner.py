"""Gradient scanner service - scans and caches gradient catalog"""
import logging
from pathlib import Path
from typing import Dict, List, Optional

from lib.files import scan_gradients
from lib.preview import create_thumbnail
from ..models.schemas import GradientInfo, GradientCatalog

logger = logging.getLogger(__name__)


class GradientScanner:
    """Scans gradient folder on startup and caches catalog"""

    def __init__(self, gradient_folder: Path):
        """Initialize gradient scanner

        Args:
            gradient_folder: Path to gradient folder
        """
        self.gradient_folder = gradient_folder
        self.catalog: Optional[GradientCatalog] = None
        self._gradients_by_path: Dict[str, Path] = {}  # For quick path lookup

    def initialize(self):
        """Scan gradients and build catalog"""
        logger.info(f"Scanning gradients in {self.gradient_folder}...")

        # Scan gradients using lib.files
        gradients_dict = scan_gradients(self.gradient_folder)

        # Build catalog with thumbnails
        categories = {}
        total_count = 0

        for category, gradient_list in gradients_dict.items():
            category_gradients = []

            for gradient in gradient_list:
                # Generate thumbnail
                try:
                    thumbnail = create_thumbnail(gradient.path, size=(256, 10))
                except Exception as e:
                    logger.warning(f"Failed to create thumbnail for {gradient.name}: {e}")
                    thumbnail = "data:image/png;base64,"

                # Create GradientInfo
                gradient_info = GradientInfo(
                    name=gradient.name,
                    category=gradient.category,
                    path=str(gradient.path),
                    relative_path=gradient.relative_path,
                    thumbnail=thumbnail
                )

                category_gradients.append(gradient_info)

                # Add to path lookup
                self._gradients_by_path[gradient.relative_path] = gradient.path

                total_count += 1

            categories[category] = category_gradients

        self.catalog = GradientCatalog(
            categories=categories,
            total_count=total_count
        )

        logger.info(f"Scanned {total_count} gradients in {len(categories)} categories")

    def get_catalog(self) -> GradientCatalog:
        """Get the gradient catalog

        Returns:
            GradientCatalog object

        Raises:
            RuntimeError: If scanner not initialized
        """
        if self.catalog is None:
            raise RuntimeError("GradientScanner not initialized. Call initialize() first.")
        return self.catalog

    def get_gradient_path(self, relative_path: str) -> Optional[Path]:
        """Get full path for a gradient by relative path

        Args:
            relative_path: Relative path from gradient folder

        Returns:
            Full Path object, or None if not found
        """
        return self._gradients_by_path.get(relative_path)

    def get_gradient_by_category_and_name(self, category: str, name: str) -> Optional[GradientInfo]:
        """Get gradient info by category and name

        Args:
            category: Category name
            name: Gradient filename

        Returns:
            GradientInfo object, or None if not found
        """
        if self.catalog is None:
            return None

        category_list = self.catalog.categories.get(category, [])
        for gradient in category_list:
            if gradient.name == name:
                return gradient

        return None
