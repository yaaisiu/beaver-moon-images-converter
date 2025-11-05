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

1. Install dependencies:
```bash
pip install -r requirements.txt
```

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
- `input-images/` - Source images organized by author (folder name = author name)
- `output/` - Converted JPG files with unique names
- `processed_files.json` - Tracking file for processed images (auto-generated)

## Incremental Processing

The script tracks processed files by their SHA256 hash. This means:
- You can add new images to `input-images/` and run the script again
- Already processed images will be skipped
- Only new or changed images will be converted

## Notes

- Original images are not modified or deleted
- The script preserves image resolution during conversion
- EXIF metadata includes author name in Artist, ImageDescription, and Copyright fields
- Transparent images (PNG with alpha channel) are converted with white background


