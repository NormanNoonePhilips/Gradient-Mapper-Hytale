#!/usr/bin/env python3
"""
Gradient Mapper - Apply gradient maps to images with parallel processing
Usage: python gradient_mapper.py <input> <gradient> [options]
"""

import sys
import argparse
from pathlib import Path
from multiprocessing import cpu_count

# Import from lib
from lib.core import apply_gradient_map
from lib.files import get_image_files
from lib.batch import BatchProcessor, ProcessingTask


# Folder paths
SCRIPT_DIR = Path(__file__).parent
INPUT_FOLDER = SCRIPT_DIR / "input"
GRADIENT_FOLDER = SCRIPT_DIR / "gradient"
OUTPUT_FOLDER = SCRIPT_DIR / "output"


def create_output_folder(output_path):
    """Create output folder if it doesn't exist"""
    output_path.mkdir(parents=True, exist_ok=True)


def process_single_combination(args):
    """Process a single image-gradient combination (for parallel processing)"""
    base_image_path, gradient_map_path, output_path, quality, output_format = args
    return apply_gradient_map(
        base_image_path, gradient_map_path, output_path, quality, output_format
    )


def process_images(input_arg, gradient_arg, args):
    """Process images based on arguments"""
    # Determine output folder
    output_folder = Path(args.output) if args.output else OUTPUT_FOLDER
    create_output_folder(output_folder)

    # Determine which input files to process
    if input_arg == "[all]":
        base_images = get_image_files(INPUT_FOLDER)
        if not base_images:
            print("No image files found in input folder!")
            return
    else:
        input_path = INPUT_FOLDER / input_arg
        if not input_path.exists():
            print(f'Error: Input file "{input_arg}" not found in input folder!')
            return
        base_images = [input_arg]

    # Determine which gradient files to process
    if gradient_arg == "[all]":
        gradient_maps = get_image_files(GRADIENT_FOLDER)
        if not gradient_maps:
            print("No gradient map files found in gradient folder!")
            return
    else:
        gradient_path = GRADIENT_FOLDER / gradient_arg
        if not gradient_path.exists():
            print(
                f'Error: Gradient file "{gradient_arg}" not found in gradient folder!'
            )
            return
        gradient_maps = [gradient_arg]

    print(
        f"Processing {len(base_images)} base image(s) with {len(gradient_maps)} gradient map(s)..."
    )
    print(f"Output format: {args.format.upper()}, Quality: {args.quality}")
    print(f"Workers: {args.workers}\n")

    # Prepare all combinations as ProcessingTask objects
    tasks = []
    for base_image in base_images:
        for gradient_map in gradient_maps:
            base_name = Path(base_image).stem
            gradient_name = Path(gradient_map).stem

            # Determine output filename
            if args.prefix:
                output_name = f"{args.prefix}_{base_name}_{gradient_name}"
            else:
                output_name = f"{base_name}_{gradient_name}"

            if args.suffix:
                output_name = f"{output_name}_{args.suffix}"

            output_name = f"{output_name}.{args.format.lower()}"

            base_image_path = INPUT_FOLDER / base_image
            gradient_map_path = GRADIENT_FOLDER / gradient_map
            output_path = output_folder / output_name

            tasks.append(
                ProcessingTask(
                    base_image_path=base_image_path,
                    gradient_map_path=gradient_map_path,
                    output_path=output_path,
                    quality=args.quality,
                    output_format=args.format
                )
            )

    # Process with BatchProcessor
    def progress_callback(current, total, message):
        """Print progress messages"""
        print(message)

    processor = BatchProcessor(max_workers=args.workers)
    successful_count, failed_count, error_messages = processor.process_batch(
        tasks,
        progress_callback=progress_callback,
        use_parallel=(args.workers > 1)
    )

    print(f"\nProcessing complete!")
    print(f"✓ Success: {successful_count}")
    if failed_count > 0:
        print(f"✗ Failed: {failed_count}")
    print(f"Output location: {output_folder}")


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
        """,
    )

    # Positional arguments
    parser.add_argument("input", help="Input image filename or [all] for all images")
    parser.add_argument("gradient", help="Gradient filename or [all] for all gradients")

    # Optional arguments
    parser.add_argument(
        "-o", "--output", help="Output folder path (default: ./output)", default=None
    )
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
    parser.add_argument("--prefix", help="Prefix for output filenames", default=None)
    parser.add_argument("--suffix", help="Suffix for output filenames", default=None)
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
    if args.quality < 1 or args.quality > 100:
        print("Error: Quality must be between 1 and 100")
        sys.exit(1)

    # Normalize format
    if args.format == "jpg":
        args.format = "jpeg"

    process_images(args.input, args.gradient, args)


if __name__ == "__main__":
    main()
