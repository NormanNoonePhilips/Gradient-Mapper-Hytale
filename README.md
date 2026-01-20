# Gradient Mapper

A Python tool for applying gradient maps to images with parallel processing support. Transform your images by mapping their luminance values to color gradients.

## Features

- Apply gradient maps to single or multiple images
- Batch process entire folders
- Parallel processing for improved performance
- Support for multiple image formats (PNG, JPEG, WebP)
- Preserve alpha channel transparency
- Customizable output quality and format
- Flexible file naming options

## Requirements

- Python 3.6 or higher
- PIL/Pillow
- NumPy

## Installation

1. Clone or download this repository

2. Install required dependencies:

```bash
pip install Pillow numpy
```

## Folder Structure

```
gradient_mapper/
├── LICENSE.md
├── README.md
├── gradient_mapper.py
├── input/          # Place your source images here (subfolders supported)
├── gradient/       # Place your gradient maps here (subfolders supported)
└── output/         # Generated images will be saved here
```

- `input/` - Source images to be processed (searches recursively in subfolders)
- `gradient/` - Gradient map images (will be resized to 256x1 automatically, searches recursively in subfolders)
- `output/` - Output directory for processed images (created automatically)

## Usage

### Basic Syntax

```bash
python gradient_mapper.py <input> <gradient> [options]
```

### Arguments

**Positional Arguments:**
- `input` - Input image filename or `[all]` to process all images in the input folder
- `gradient` - Gradient map filename or `[all]` to use all gradients in the gradient folder

**Optional Arguments:**
- `-o, --output` - Custom output folder path (default: ./output)
- `-f, --format` - Output format: png, jpeg, jpg, webp (default: png)
- `-q, --quality` - Output quality for JPEG/WebP, 1-100 (default: 95)
- `-w, --workers` - Number of parallel workers (default: number of CPU cores)
- `--prefix` - Add prefix to output filenames
- `--suffix` - Add suffix to output filenames
- `--sequential` - Disable parallel processing (same as -w 1)

## Examples

### Process a single image with a single gradient

```bash
python gradient_mapper.py photo.png sunset_gradient.png
```

### Process all images with one gradient

```bash
python gradient_mapper.py [all] cold_blues.png
```

### Process one image with all gradients

```bash
python gradient_mapper.py portrait.jpg [all]
```

### Process all images with all gradients

```bash
python gradient_mapper.py [all] [all]
```

### Specify output format and quality

```bash
python gradient_mapper.py image.png gradient.png -f jpeg -q 90
```

```bash
python gradient_mapper.py photo.png warm_tones.png --format webp --quality 85
```

### Use parallel processing with 4 workers

```bash
python gradient_mapper.py [all] gradient.png -w 4
```

### Custom output folder with naming options

```bash
python gradient_mapper.py [all] [all] -o custom_output --prefix processed --suffix v1
```

### Sequential processing (no parallel workers)

```bash
python gradient_mapper.py image.png gradient.png --sequential
```

## How It Works

1. The script converts your base image to grayscale using standard luminance weights (0.299R + 0.587G + 0.114B)
2. Each pixel's luminance value (0-255) is used as an index into the gradient map
3. The corresponding color from the gradient is applied to that pixel
4. The original alpha channel is preserved in the output

## Gradient Maps

Gradient maps can be any image format, but they will be resized to 256x1 pixels internally. For best results:

- Use horizontal gradient images
- Ensure smooth color transitions
- Consider the full 0-255 luminance range

## Output Naming

By default, output files are named: `{input_name}_{gradient_name}.{format}`

With prefix and suffix options: `{prefix}_{input_name}_{gradient_name}_{suffix}.{format}`

## Working with Subfolders

Both the `input/` and `gradient/` folders support subfolders. The script will recursively search all subdirectories when using `[all]`.

For example, this structure works perfectly:
```
input/
├── vacation/
│   └── beach.png
└── portraits/
    └── person.png
```

When processing with `[all]`, both `beach.png` and `person.png` will be found and processed. Output files use only the base filename, so subfolder structure is not preserved in output names.

## Performance

The tool uses parallel processing by default, utilizing all available CPU cores. You can control the number of workers with the `-w` option or disable parallel processing entirely with `--sequential`.

## Supported Image Formats

**Input:** PNG, JPEG, JPG, WebP

**Output:** PNG, JPEG, WebP

Note: When outputting to JPEG, transparency is removed and the image is converted to RGB.

## License

MIT License. See LICENSE.md for details.