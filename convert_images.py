#!/usr/bin/env python3
"""
Image conversion script that processes images from input-images/ directory,
converts them to JPG format, and saves to output/ with unique filenames.
Preserves author name from folder structure and adds it to EXIF metadata.
"""

import json
import hashlib
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Set

from PIL import Image

try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    logging.warning("pillow-heif not available. HEIC files may not be supported.")


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
INPUT_DIR = Path("input-images")
OUTPUT_DIR = Path("output")
TRACKING_FILE = Path("processed_files.json")

# Supported image extensions
IMAGE_EXTENSIONS = {'.heic', '.heif', '.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp'}


def calculate_file_hash(file_path: Path) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def load_processed_files() -> Dict[str, str]:
    """Load the tracking file with processed files."""
    if TRACKING_FILE.exists():
        try:
            with open(TRACKING_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Error loading tracking file: {e}. Starting fresh.")
            return {}
    return {}


def save_processed_files(processed: Dict[str, str]) -> None:
    """Save the tracking file with processed files."""
    try:
        with open(TRACKING_FILE, 'w', encoding='utf-8') as f:
            json.dump(processed, f, indent=2)
    except IOError as e:
        logger.error(f"Error saving tracking file: {e}")


def get_author_from_path(file_path: Path) -> Optional[str]:
    """Extract author name from folder structure."""
    # Get the parent directory name (should be the author folder)
    parent = file_path.parent
    # Check if parent is the input directory itself
    if parent == INPUT_DIR:
        return None
    # Return the direct parent folder name as author
    return parent.name


def add_author_to_exif(image: Image.Image, author: str) -> Optional[bytes]:
    """Add author name to EXIF metadata and return EXIF bytes."""
    try:
        # Get existing EXIF data
        exif_dict = image.getexif()
        
        # EXIF tag for Artist is 315 (0x013B)
        artist_tag = 315
        
        # Add author to EXIF
        exif_dict[artist_tag] = author
        
        # Also try to add to ImageDescription and Copyright for better compatibility
        # ImageDescription tag is 270
        exif_dict[270] = f"Author: {author}"
        
        # Copyright tag is 33432
        exif_dict[33432] = f"Copyright {datetime.now().year} {author}"
        
        # Convert EXIF dict to bytes
        return exif_dict.tobytes()
        
    except Exception as e:
        logger.warning(f"Could not add EXIF metadata for author '{author}': {e}")
        # Return existing EXIF if available, otherwise None
        try:
            return image.getexif().tobytes() if image.getexif() else None
        except:
            return None


def generate_unique_filename(author: str, file_path: Path, file_hash: str) -> str:
    """Generate unique filename with author, datetime, and hash."""
    # Get current datetime
    now = datetime.now()
    datetime_str = now.strftime("%Y%m%d_%H%M%S")
    
    # Use first 8 characters of hash for uniqueness
    short_hash = file_hash[:8]
    
    # Sanitize author name for filename
    safe_author = "".join(c for c in author if c.isalnum() or c in ('-', '_')).strip()
    
    # Get original filename stem (without extension)
    original_stem = file_path.stem
    # Sanitize original filename
    safe_original = "".join(c for c in original_stem if c.isalnum() or c in ('-', '_', ' ')).strip()
    safe_original = safe_original.replace(' ', '_')[:20]  # Limit length
    
    # Combine: author_datetime_original_hash.jpg
    filename = f"{safe_author}_{datetime_str}_{safe_original}_{short_hash}.jpg"
    
    return filename


def convert_image_to_jpg(input_path: Path, output_path: Path, author: str) -> bool:
    """Convert image to JPG format preserving resolution and adding EXIF metadata."""
    try:
        # Open image
        with Image.open(input_path) as img:
            # Convert RGBA to RGB if necessary (JPG doesn't support transparency)
            if img.mode in ('RGBA', 'LA', 'P'):
                # Create white background
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                rgb_img.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = rgb_img
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Add author to EXIF metadata
            exif_data = add_author_to_exif(img, author)
            
            # Save as JPG with high quality to preserve resolution
            save_kwargs = {'quality': 95, 'optimize': True}
            if exif_data:
                save_kwargs['exif'] = exif_data
            
            img.save(output_path, 'JPEG', **save_kwargs)
            
            logger.info(f"Converted: {input_path.name} -> {output_path.name}")
            return True
            
    except Exception as e:
        logger.error(f"Error converting {input_path}: {e}")
        return False


def process_images() -> None:
    """Main function to process all images."""
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    # Load processed files tracking
    processed_files = load_processed_files()
    processed_hashes: Set[str] = set(processed_files.values())
    
    # Scan input directory for images
    if not INPUT_DIR.exists():
        logger.error(f"Input directory '{INPUT_DIR}' does not exist!")
        return
    
    image_files = []
    for ext in IMAGE_EXTENSIONS:
        image_files.extend(INPUT_DIR.rglob(f"*{ext}"))
        image_files.extend(INPUT_DIR.rglob(f"*{ext.upper()}"))
    
    logger.info(f"Found {len(image_files)} image files to process")
    
    # Process each image
    processed_count = 0
    skipped_count = 0
    error_count = 0
    
    for image_path in image_files:
        try:
            # Calculate file hash
            file_hash = calculate_file_hash(image_path)
            
            # Check if already processed
            if file_hash in processed_hashes:
                logger.debug(f"Skipping already processed: {image_path}")
                skipped_count += 1
                continue
            
            # Get author from folder structure
            author = get_author_from_path(image_path)
            if not author:
                logger.warning(f"Could not determine author for {image_path}, skipping")
                error_count += 1
                continue
            
            # Generate unique output filename
            output_filename = generate_unique_filename(author, image_path, file_hash)
            output_path = OUTPUT_DIR / output_filename
            
            # Check if output file already exists (shouldn't happen with unique names, but safety check)
            if output_path.exists():
                logger.warning(f"Output file already exists: {output_path}, skipping")
                skipped_count += 1
                continue
            
            # Convert image
            if convert_image_to_jpg(image_path, output_path, author):
                # Record as processed
                processed_files[str(image_path.relative_to(INPUT_DIR))] = file_hash
                processed_hashes.add(file_hash)
                processed_count += 1
            else:
                error_count += 1
                
        except Exception as e:
            logger.error(f"Unexpected error processing {image_path}: {e}")
            error_count += 1
    
    # Save updated tracking file
    save_processed_files(processed_files)
    
    # Summary
    logger.info(f"\nProcessing complete!")
    logger.info(f"  Processed: {processed_count}")
    logger.info(f"  Skipped (already processed): {skipped_count}")
    logger.info(f"  Errors: {error_count}")
    logger.info(f"  Total: {len(image_files)}")


if __name__ == "__main__":
    process_images()

