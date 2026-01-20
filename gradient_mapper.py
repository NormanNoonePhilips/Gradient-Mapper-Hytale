#!/usr/bin/env python3
"""
Gradient Mapper - Apply gradient maps to images with parallel processing
Usage: python gradient_mapper.py <input> <gradient> [options]
"""

import os
import sys
import argparse
from pathlib import Path
from PIL import Image
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import cpu_count

# Folder paths
SCRIPT_DIR = Path(__file__).parent
INPUT_FOLDER = SCRIPT_DIR / "input"
GRADIENT_FOLDER = SCRIPT_DIR / "gradient"
OUTPUT_FOLDER = SCRIPT_DIR / "output"

# Supported image extensions
IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp")


def create_output_folder(output_path):
    """Create output folder if it doesn't exist"""
    output_path.mkdir(parents=True, exist_ok=True)


def path_to_filename_component(relative_path):
    """
    Convert a relative path to a filename component.
    Example: "vacation/beach.png" -> "vacation_beach"
    Example: "portraits/family/photo.png" -> "portraits_family_photo"
    """
    path_obj = Path(relative_path)
    # Get all parts except the extension
    parts = list(path_obj.parent.parts) + [path_obj.stem]
    # Filter out current directory markers and empty strings
    parts = [p for p in parts if p and p != '.']
    # Join with underscores, fallback to just stem if no parts
    return '_'.join(parts) if parts else path_obj.stem


def apply_gradient_map(base_image_path,
                       gradient_map_path,
                       output_path,
                       quality=95,
                       output_format="PNG"):
    """Apply a gradient map to a base image"""
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
        luminance = (rgb[:, :, 0] * 0.299 + rgb[:, :, 1] * 0.587 +
                     rgb[:, :, 2] * 0.114).astype(np.uint8)

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

        return True, f"✓ Created: {output_path.name}"

    except Exception as e:
        return False, f"✗ Error processing {base_image_path.name}: {str(e)}"


def process_single_combination(args):
    """Process a single image-gradient combination (for parallel processing)"""
    base_image_path, gradient_map_path, output_path, quality, output_format = args
    return apply_gradient_map(base_image_path, gradient_map_path, output_path,
                              quality, output_format)


def get_image_files(folder, extensions=IMAGE_EXTENSIONS):
    """Get all image files in a folder recursively"""
    image_files = []
    for root, _, files in os.walk(folder):
        for file in files:
            if file.lower().endswith(extensions):
                # Get relative path from the base folder
                rel_path = os.path.relpath(os.path.join(root, file), folder)
                image_files.append(rel_path)
    return sorted(image_files)  # Sort for consistent ordering


def build_output_filename(base_image, gradient_map, args):
    """Build the output filename from components"""
    # Convert paths to filename components (includes subfolders)
    base_component = path_to_filename_component(base_image)
    gradient_component = path_to_filename_component(gradient_map)

    # Build output filename with optional prefix/suffix
    output_parts = []

    if args.prefix:
        output_parts.append(args.prefix)

    output_parts.append(base_component)
    output_parts.append(gradient_component)

    if args.suffix:
        output_parts.append(args.suffix)

    return '_'.join(output_parts) + f'.{args.format.lower()}'


def process_images(input_arg, gradient_arg, args):
    """Process images based on arguments"""
    # Determine output folder
    output_folder = Path(args.output) if args.output else OUTPUT_FOLDER
    create_output_folder(output_folder)

    # Determine which input files to process
    if input_arg == "[all]":
        base_images = get_image_files(INPUT_FOLDER)
        if not base_images:
            print("Error: No image files found in input folder!")
            return
    else:
        input_path = INPUT_FOLDER / input_arg
        if not input_path.exists():
            print(
                f'Error: Input file "{input_arg}" not found in input folder!')
            return
        base_images = [input_arg]

    # Determine which gradient files to process
    if gradient_arg == "[all]":
        gradient_maps = get_image_files(GRADIENT_FOLDER)
        if not gradient_maps:
            print("Error: No gradient map files found in gradient folder!")
            return
    else:
        gradient_path = GRADIENT_FOLDER / gradient_arg
        if not gradient_path.exists():
            print(
                f'Error: Gradient file "{gradient_arg}" not found in gradient folder!'
            )
            return
        gradient_maps = [gradient_arg]

    # Display processing info
    total_tasks = len(base_images) * len(gradient_maps)
    print(
        f"Processing {len(base_images)} base image(s) with {len(gradient_maps)} gradient map(s)..."
    )
    print(f"Total combinations: {total_tasks}")
    print(f"Output format: {args.format.upper()}, Quality: {args.quality}")
    print(f"Workers: {args.workers}\n")

    # Prepare all combinations
    tasks = []
    for base_image in base_images:
        for gradient_map in gradient_maps:
            output_name = build_output_filename(base_image, gradient_map, args)

            base_image_path = INPUT_FOLDER / base_image
            gradient_map_path = GRADIENT_FOLDER / gradient_map
            output_path = output_folder / output_name

            tasks.append((
                base_image_path,
                gradient_map_path,
                output_path,
                args.quality,
                args.format,
            ))

    # Process with parallel execution
    processed_count = 0
    failed_count = 0

    if args.workers == 1:
        # Sequential processing
        for task in tasks:
            success, message = process_single_combination(task)
            print(message)
            if success:
                processed_count += 1
            else:
                failed_count += 1
    else:
        # Parallel processing
        with ProcessPoolExecutor(max_workers=args.workers) as executor:
            futures = {
                executor.submit(process_single_combination, task): task
                for task in tasks
            }

            for future in as_completed(futures):
                success, message = future.result()
                print(message)
                if success:
                    processed_count += 1
                else:
                    failed_count += 1

    # Display summary
    print(f"\n{'='*50}")
    print(f"Processing complete!")
    print(f"✓ Success: {processed_count}")
    if failed_count > 0:
        print(f"✗ Failed: {failed_count}")
    print(f"Output location: {output_folder}")
    print(f"{'='*50}")


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(
        description="Apply gradient maps to images with parallel processing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python gradient_mapper.py image.png cold_blues.png
  python gradient_mapper.py [all] cold_blues.png -w 4
  python gradient_mapper.py image.png [all] -f jpeg -q 90
  python gradient_mapper.py [all] [all] -o custom_output --prefix grad
  python gradient_mapper.py image.png gradient.png --format webp --quality 85

Note: Files in subfolders will have their path included in the output name.
  Example: input/vacation/beach.png + gradient/warm/sunset.png
           -> vacation_beach_warm_sunset.png
        """,
    )

    # Positional arguments
    parser.add_argument("input",
                        help="Input image filename or [all] for all images")
    parser.add_argument("gradient",
                        help="Gradient filename or [all] for all gradients")

    # Optional arguments
    parser.add_argument("-o",
                        "--output",
                        help="Output folder path (default: ./output)",
                        default=None)
    parser.add_argument(
        "-f",
        "--format",
        choices=["png", "jpeg", "jpg", "webp"],
        default="png",
        help="Output format (default: png)",
    )
    parser.add_argument(
        "-q",
        "--quality",
        type=int,
        default=95,
        help="Output quality for JPEG/WebP (1-100, default: 95)",
    )
    parser.add_argument(
        "-w",
        "--workers",
        type=int,
        default=None,
        help=f"Number of parallel workers (default: {cpu_count()})",
    )
    parser.add_argument("--prefix",
                        help="Prefix for output filenames",
                        default=None)
    parser.add_argument("--suffix",
                        help="Suffix for output filenames",
                        default=None)
    parser.add_argument(
        "--sequential",
        action="store_true",
        help="Disable parallel processing (same as -w 1)",
    )

    args = parser.parse_args()

    # Set workers
    if args.sequential:
        args.workers = 1
    elif args.workers is None:
        args.workers = cpu_count()

    # Validate quality
    if not 1 <= args.quality <= 100:
        print("Error: Quality must be between 1 and 100")
        sys.exit(1)

    # Normalize format
    if args.format == "jpg":
        args.format = "jpeg"

    process_images(args.input, args.gradient, args)


if __name__ == "__main__":
    main()
