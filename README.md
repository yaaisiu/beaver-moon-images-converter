# Image Conversion Tool

A Python script that converts images from the `input-images/` directory to JPG format, preserving resolution and adding author metadata from folder names.

## Features

- Converts images (HEIC, JPEG, PNG, etc.) to JPG format
- Preserves original image resolution
- Extracts author name from folder structure
- Adds author name to EXIF metadata (Artist, ImageDescription, Copyright fields)
- Generates unique filenames: `{author}_{datetime}_{original}_{hash}.jpg`
- Tracks processed files to avoid reprocessing (incremental processing support)
- Handles multiple image formats including HEIC/HEIF

## Requirements

- Python 3.10.16 or higher
- Pillow (PIL)
- pillow-heif (for HEIC/HEIF support)

## Installation

### Standard Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

### Development Installation

For development with testing and linting:
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Docker Installation

1. Build the Docker image:
```bash
docker-compose build
```

2. Run the conversion:
```bash
docker-compose up
```

The Docker setup automatically mounts `input-images/` and `output/` directories.

## Usage

1. Organize your images in the `input-images/` directory:
   ```
   input-images/
     ├── author1/
     │   ├── image1.HEIC
     │   └── image2.jpg
     └── author2/
         └── image3.jpeg
   ```

2. Run the conversion script:
```bash
python convert_images.py
```

3. Converted images will be saved to the `output/` directory with unique filenames:
   ```
   output/
     ├── author1_20251105_143022_image1_a1b2c3d4.jpg
     ├── author1_20251105_143023_image2_e5f6g7h8.jpg
     └── author2_20251105_143024_image3_i9j0k1l2.jpg
   ```

## How It Works

1. **Scanning**: Recursively scans `input-images/` for all image files
2. **Author Extraction**: Extracts author name from parent folder name
3. **Tracking**: Uses `processed_files.json` to track processed files by hash
4. **Conversion**: Converts images to JPG format while preserving resolution
5. **Metadata**: Adds author name to EXIF metadata fields
6. **Naming**: Generates unique filenames with author, datetime, original name, and hash
7. **Output**: Saves converted images to `output/` directory

## File Structure

- `convert_images.py` - Main conversion script
- `requirements.txt` - Python dependencies
- `requirements-dev.txt` - Development dependencies (pytest, ruff)
- `tests/` - Test suite with unit and integration tests
- `Dockerfile` - Docker container configuration
- `docker-compose.yaml` - Docker Compose service definition
- `pyproject.toml` - Ruff configuration and project metadata
- `pytest.ini` - Pytest configuration
- `.github/workflows/ci.yml` - GitHub Actions CI/CD pipeline
- `input-images/` - Source images organized by author (folder name = author name)
- `output/` - Converted JPG files with unique names
- `processed_files.json` - Tracking file for processed images (auto-generated)

## Incremental Processing

The script tracks processed files by their SHA256 hash. This means:
- You can add new images to `input-images/` and run the script again
- Already processed images will be skipped
- Only new or changed images will be converted

## Development

### Running Tests

Run the test suite with coverage:
```bash
pytest
```

Run tests with verbose output:
```bash
pytest -v
```

### Code Quality

Lint code with Ruff:
```bash
ruff check .
```

Format code with Ruff:
```bash
ruff format .
```

Check formatting without modifying files:
```bash
ruff format --check .
```

### CI/CD

The project includes a GitHub Actions workflow (`.github/workflows/ci.yml`) that automatically:
- Runs Ruff linting and formatting checks
- Executes the test suite with coverage reporting
- Builds the Docker image to verify it works

The CI pipeline runs on:
- Push to `main` or `master` branch
- Pull requests
- Manual workflow dispatch

## Notes

- Original images are not modified or deleted
- The script preserves image resolution during conversion
- EXIF metadata includes author name in Artist, ImageDescription, and Copyright fields
- Transparent images (PNG with alpha channel) are converted with white background

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `pytest`
5. Run linting: `ruff check .` and `ruff format --check .`
6. Submit a pull request

