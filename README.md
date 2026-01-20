# Gradient Mapper

A Python tool for applying gradient maps to images with parallel processing support and a web interface. Transform your images by mapping their luminance values to color gradients.

## Features

- Apply gradient maps to single or multiple images
- Batch process entire folders
- Parallel processing for improved performance
- Web UI with real-time preview and batch processing
- Support for multiple image formats (PNG, JPEG, WebP)
- Preserve alpha channel transparency
- Customizable output quality and format
- Flexible file naming options
- WebSocket-based progress tracking

## Requirements

- Python 3.10 or higher
- uv (dependency manager)

## Installation

1. Clone or download this repository

2. Install required dependencies:

```bash
uv sync
```

## Folder Structure

```
gradient_mapper/
├── LICENSE
├── README.md
├── gradient_mapper.py
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
├── lib/                # Shared core library
│   ├── __init__.py
│   ├── core.py         # Core gradient mapping functions
│   ├── files.py        # File system operations
│   ├── batch.py        # Batch processing coordinator
│   └── preview.py      # Preview generation
├── web/                # FastAPI backend + static frontend
│   ├── __init__.py
│   ├── backend/
│   │   ├── __init__.py
│   │   ├── main.py     # FastAPI application
│   │   ├── api/        # REST API and WebSocket routes
│   │   ├── models/     # Pydantic schemas
│   │   └── services/   # Business logic services
│   └── frontend/       # Static HTML/CSS/JS
│       ├── index.html
│       ├── css/
│       └── js/
├── input/              # Place source images here
├── gradient/           # Place gradient maps here
└── output/             # Generated images saved here
```

## Usage

### Command Line Interface

Run the CLI without activating a virtual environment:

```bash
uv run python gradient_mapper.py [input] [gradient] [options]
```

#### Basic Syntax

```bash
python gradient_mapper.py <input> <gradient> [options]
```

#### Arguments

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

#### Examples

Process a single image with a single gradient:

```bash
python gradient_mapper.py photo.png sunset_gradient.png
```

Process all images with one gradient:

```bash
python gradient_mapper.py [all] cold_blues.png
```

Process one image with all gradients:

```bash
python gradient_mapper.py portrait.jpg [all]
```

Process all images with all gradients:

```bash
python gradient_mapper.py [all] [all]
```

Specify output format and quality:

```bash
python gradient_mapper.py image.png gradient.png -f jpeg -q 90
```

```bash
python gradient_mapper.py photo.png warm_tones.png --format webp --quality 85
```

Use parallel processing with 4 workers:

```bash
python gradient_mapper.py [all] gradient.png -w 4
```

Custom output folder with naming options:

```bash
python gradient_mapper.py [all] [all] -o custom_output --prefix processed --suffix v1
```

Sequential processing (no parallel workers):

```bash
python gradient_mapper.py image.png gradient.png --sequential
```

### Web UI

Run the web application with live reload:

```bash
uv run uvicorn web.backend.main:app --reload
```

Open `http://localhost:8000` in your browser.

The web UI provides:
- Drag and drop image upload
- Real-time preview with side-by-side, slider, and grid comparison modes
- Gradient selector with categories and search
- Batch queue for processing multiple combinations
- WebSocket-based progress tracking
- Download results as ZIP file

## Docker

Build and run with Docker:

```bash
docker build -t gradient-mapper .
docker run --rm -p 8000:8000 \
  -v "$PWD/input:/app/input" \
  -v "$PWD/gradient:/app/gradient" \
  -v "$PWD/output:/app/output" \
  gradient-mapper
```

Or use Docker Compose for development:

```bash
docker compose up --build
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

## API Documentation

When running the web application, visit `http://localhost:8000/docs` for interactive API documentation.

### REST API Endpoints

- `GET /api/gradients` - List all available gradients
- `POST /api/upload` - Upload images
- `GET /api/images` - List uploaded images
- `GET /api/images/{path}` - Get a specific image
- `POST /api/preview` - Generate preview
- `POST /api/jobs` - Create batch processing job
- `GET /api/jobs/{job_id}` - Get job status
- `GET /api/jobs/{job_id}/download` - Download results
- `DELETE /api/jobs/{job_id}` - Cancel job

### WebSocket

Connect to `/ws` for real-time progress updates. Send a subscribe message:

```json
{
  "type": "subscribe",
  "job_id": "your-job-id"
}
```

Receive progress updates:

```json
{
  "type": "progress",
  "job_id": "your-job-id",
  "current": 5,
  "total": 10,
  "status": "processing",
  "message": "Processing image 5 of 10"
}
```

## Environment Variables

For the web application:

- `CORS_ALLOW_ORIGINS` - Comma-separated list of allowed origins (default: `http://localhost:8000,http://127.0.0.1:8000`)
- `CORS_ALLOW_CREDENTIALS` - Allow credentials in CORS requests (default: false)

## License

MIT License. See LICENSE file for details.
