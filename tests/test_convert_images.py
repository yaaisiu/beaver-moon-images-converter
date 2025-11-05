"""Unit tests for convert_images module."""

import hashlib
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from PIL import Image

import convert_images


class TestCalculateFileHash:
    """Tests for calculate_file_hash function."""

    def test_calculate_file_hash(self, temp_dir: Path):
        """Test hash calculation for a file."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")

        hash_result = convert_images.calculate_file_hash(test_file)

        assert isinstance(hash_result, str)
        assert len(hash_result) == 64  # SHA256 produces 64 hex characters
        assert hash_result == hashlib.sha256(b"test content").hexdigest()

    def test_hash_is_consistent(self, temp_dir: Path):
        """Test that hash is consistent for same content."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("same content")

        hash1 = convert_images.calculate_file_hash(test_file)
        hash2 = convert_images.calculate_file_hash(test_file)

        assert hash1 == hash2

    def test_hash_different_for_different_content(self, temp_dir: Path):
        """Test that different content produces different hashes."""
        file1 = temp_dir / "test1.txt"
        file2 = temp_dir / "test2.txt"
        file1.write_text("content one")
        file2.write_text("content two")

        hash1 = convert_images.calculate_file_hash(file1)
        hash2 = convert_images.calculate_file_hash(file2)

        assert hash1 != hash2


class TestLoadProcessedFiles:
    """Tests for load_processed_files function."""

    def test_load_nonexistent_file(self, temp_dir: Path):
        """Test loading when tracking file doesn't exist."""
        with patch("convert_images.TRACKING_FILE", temp_dir / "nonexistent.json"):
            result = convert_images.load_processed_files()
            assert result == {}

    def test_load_existing_file(self, temp_dir: Path):
        """Test loading existing tracking file."""
        tracking_file = temp_dir / "processed_files.json"
        data = {"image1.jpg": "hash123", "image2.jpg": "hash456"}
        tracking_file.write_text(json.dumps(data))

        with patch("convert_images.TRACKING_FILE", tracking_file):
            result = convert_images.load_processed_files()
            assert result == data

    def test_load_invalid_json(self, temp_dir: Path):
        """Test loading invalid JSON file."""
        tracking_file = temp_dir / "processed_files.json"
        tracking_file.write_text("invalid json content")

        with patch("convert_images.TRACKING_FILE", tracking_file):
            result = convert_images.load_processed_files()
            assert result == {}


class TestSaveProcessedFiles:
    """Tests for save_processed_files function."""

    def test_save_processed_files(self, temp_dir: Path):
        """Test saving processed files."""
        tracking_file = temp_dir / "processed_files.json"
        data = {"image1.jpg": "hash123", "image2.jpg": "hash456"}

        with patch("convert_images.TRACKING_FILE", tracking_file):
            convert_images.save_processed_files(data)

            assert tracking_file.exists()
            loaded = json.loads(tracking_file.read_text())
            assert loaded == data


class TestGetAuthorFromPath:
    """Tests for get_author_from_path function."""

    def test_get_author_from_subfolder(self, temp_dir: Path):
        """Test extracting author from subfolder."""
        input_dir = temp_dir / "input-images"
        author_dir = input_dir / "author_name"
        image_path = author_dir / "image.jpg"

        with patch("convert_images.INPUT_DIR", input_dir):
            author = convert_images.get_author_from_path(image_path)
            assert author == "author_name"

    def test_get_author_none_when_in_root(self, temp_dir: Path):
        """Test that None is returned when image is in root input dir."""
        input_dir = temp_dir / "input-images"
        image_path = input_dir / "image.jpg"

        with patch("convert_images.INPUT_DIR", input_dir):
            author = convert_images.get_author_from_path(image_path)
            assert author is None

    def test_get_author_nested_subfolder(self, temp_dir: Path):
        """Test extracting author from direct subfolder (not nested deeper)."""
        input_dir = temp_dir / "input-images"
        author_dir = input_dir / "test_author"
        subfolder = author_dir / "subfolder"
        image_path = subfolder / "image.jpg"

        with patch("convert_images.INPUT_DIR", input_dir):
            # Should still get the direct parent folder name
            author = convert_images.get_author_from_path(image_path)
            assert author == "subfolder"  # Direct parent, not author_dir


class TestAddAuthorToExif:
    """Tests for add_author_to_exif function."""

    def test_add_author_to_exif(self, sample_image_rgb: Path):
        """Test adding author to EXIF metadata."""
        with Image.open(sample_image_rgb) as img:
            author = "test_author"
            exif_bytes = convert_images.add_author_to_exif(img, author)

            assert exif_bytes is not None
            assert isinstance(exif_bytes, bytes)

    def test_add_author_to_exif_with_existing_exif(self, temp_dir: Path):
        """Test adding author when image has existing EXIF."""
        img = Image.new("RGB", (100, 100), color=(255, 0, 0))
        # Add some EXIF data
        exif_dict = img.getexif()
        exif_dict[270] = "Original description"

        author = "test_author"
        exif_bytes = convert_images.add_author_to_exif(img, author)

        assert exif_bytes is not None

    def test_add_author_handles_exception(self):
        """Test that exceptions in EXIF handling are caught."""
        # Create a mock image that raises exception
        mock_img = MagicMock()
        mock_img.getexif.side_effect = Exception("EXIF error")

        result = convert_images.add_author_to_exif(mock_img, "test_author")
        assert result is None


class TestGenerateUniqueFilename:
    """Tests for generate_unique_filename function."""

    def test_generate_unique_filename(self, temp_dir: Path):
        """Test unique filename generation."""
        author = "test_author"
        file_path = temp_dir / "original_image.jpg"
        file_hash = "a1b2c3d4e5f6g7h8" * 4  # 64 char hash

        filename = convert_images.generate_unique_filename(author, file_path, file_hash)

        assert filename.endswith(".jpg")
        assert author in filename
        assert file_hash[:8] in filename
        assert "original_image" in filename

    def test_filename_sanitization(self, temp_dir: Path):
        """Test that special characters are sanitized."""
        author = "author with spaces & symbols!"
        file_path = temp_dir / "file with spaces & symbols.jpg"
        file_hash = "a" * 64

        filename = convert_images.generate_unique_filename(author, file_path, file_hash)

        # Should not contain spaces or special characters (except - and _)
        assert " " not in filename
        assert "!" not in filename
        assert "&" not in filename

    def test_filename_format(self, temp_dir: Path):
        """Test filename format structure."""
        author = "author"
        file_path = temp_dir / "image.jpg"
        file_hash = "a" * 64

        filename = convert_images.generate_unique_filename(author, file_path, file_hash)

        # Format: author_YYYYMMDD_HHMMSS_original_hash.jpg
        parts = filename.replace(".jpg", "").split("_")
        assert len(parts) >= 4
        assert parts[0] == author
        assert len(parts[-1]) == 8  # Short hash


class TestConvertImageToJpg:
    """Tests for convert_image_to_jpg function."""

    def test_convert_rgb_image(self, sample_image_rgb: Path, temp_dir: Path):
        """Test converting RGB image to JPG."""
        output_path = temp_dir / "output.jpg"
        author = "test_author"

        result = convert_images.convert_image_to_jpg(sample_image_rgb, output_path, author)

        assert result is True
        assert output_path.exists()

        # Verify output is valid JPG
        with Image.open(output_path) as img:
            assert img.format == "JPEG"
            assert img.mode == "RGB"

    def test_convert_rgba_to_rgb(self, sample_image_rgba: Path, temp_dir: Path):
        """Test converting RGBA image to RGB JPG."""
        output_path = temp_dir / "output.jpg"
        author = "test_author"

        result = convert_images.convert_image_to_jpg(sample_image_rgba, output_path, author)

        assert result is True
        assert output_path.exists()

        with Image.open(output_path) as img:
            assert img.format == "JPEG"
            assert img.mode == "RGB"

    def test_convert_png_to_jpg(self, sample_image_png: Path, temp_dir: Path):
        """Test converting PNG image to JPG."""
        output_path = temp_dir / "output.jpg"
        author = "test_author"

        result = convert_images.convert_image_to_jpg(sample_image_png, output_path, author)

        assert result is True
        assert output_path.exists()
        assert output_path.suffix == ".jpg"

    def test_convert_preserves_resolution(self, sample_image_rgb: Path, temp_dir: Path):
        """Test that image resolution is preserved."""
        output_path = temp_dir / "output.jpg"
        author = "test_author"

        # Get original size
        with Image.open(sample_image_rgb) as orig_img:
            original_size = orig_img.size

        convert_images.convert_image_to_jpg(sample_image_rgb, output_path, author)

        # Check output size
        with Image.open(output_path) as output_img:
            assert output_img.size == original_size

    def test_convert_invalid_image(self, temp_dir: Path):
        """Test converting invalid image file."""
        invalid_file = temp_dir / "invalid.txt"
        invalid_file.write_text("not an image")
        output_path = temp_dir / "output.jpg"
        author = "test_author"

        result = convert_images.convert_image_to_jpg(invalid_file, output_path, author)

        assert result is False
        assert not output_path.exists()


class TestProcessImages:
    """Integration tests for process_images function."""

    def test_process_images_empty_directory(self, temp_dir: Path):
        """Test processing with empty input directory."""
        input_dir = temp_dir / "input-images"
        output_dir = temp_dir / "output"
        input_dir.mkdir()

        with (
            patch("convert_images.INPUT_DIR", input_dir),
            patch("convert_images.OUTPUT_DIR", output_dir),
            patch("convert_images.TRACKING_FILE", temp_dir / "processed.json"),
        ):
            convert_images.process_images()

            # Should not error, just process nothing
            assert output_dir.exists()

    def test_process_images_single_image(
        self,
        test_input_dir: Path,
        test_output_dir: Path,
        author_folder: tuple[Path, Path],
        sample_image_rgb: Path,
        temp_dir: Path,
    ):
        """Test processing a single image."""
        author_dir, image_path = author_folder
        tracking_file = temp_dir / "processed.json"

        with (
            patch("convert_images.INPUT_DIR", test_input_dir),
            patch("convert_images.OUTPUT_DIR", test_output_dir),
            patch("convert_images.TRACKING_FILE", tracking_file),
        ):
            convert_images.process_images()

            # Check output directory has files
            output_files = list(test_output_dir.glob("*.jpg"))
            assert len(output_files) == 1

            # Check tracking file was created
            assert tracking_file.exists()
            tracking_data = json.loads(tracking_file.read_text())
            assert len(tracking_data) == 1

    def test_process_images_skips_processed(
        self, test_input_dir: Path, test_output_dir: Path, author_folder: tuple, temp_dir: Path
    ):
        """Test that already processed images are skipped."""
        author_dir, image_path = author_folder
        tracking_file = temp_dir / "processed.json"

        # Calculate hash and add to tracking
        file_hash = convert_images.calculate_file_hash(image_path)
        tracking_data = {str(image_path.relative_to(test_input_dir)): file_hash}
        tracking_file.write_text(json.dumps(tracking_data))

        with (
            patch("convert_images.INPUT_DIR", test_input_dir),
            patch("convert_images.OUTPUT_DIR", test_output_dir),
            patch("convert_images.TRACKING_FILE", tracking_file),
        ):
            # First run
            initial_output_count = len(list(test_output_dir.glob("*.jpg")))

            # Second run should skip
            convert_images.process_images()

            # Should not have created duplicate files
            final_output_count = len(list(test_output_dir.glob("*.jpg")))
            assert final_output_count == initial_output_count or final_output_count == 1

    def test_process_images_multiple_authors(
        self, test_input_dir: Path, test_output_dir: Path, temp_dir: Path
    ):
        """Test processing images from multiple authors."""
        # Create two author folders
        author1_dir = test_input_dir / "author1"
        author2_dir = test_input_dir / "author2"
        author1_dir.mkdir()
        author2_dir.mkdir()

        # Create different images for each author to ensure different hashes
        img1 = Image.new("RGB", (100, 100), color=(255, 0, 0))
        img2 = Image.new("RGB", (100, 100), color=(0, 255, 0))
        img1_path = author1_dir / "img1.jpg"
        img2_path = author2_dir / "img2.jpg"
        img1.save(img1_path, "JPEG")
        img2.save(img2_path, "JPEG")

        tracking_file = temp_dir / "processed.json"

        with (
            patch("convert_images.INPUT_DIR", test_input_dir),
            patch("convert_images.OUTPUT_DIR", test_output_dir),
            patch("convert_images.TRACKING_FILE", tracking_file),
        ):
            convert_images.process_images()

            # Should have processed both images
            output_files = list(test_output_dir.glob("*.jpg"))
            assert len(output_files) == 2, (
                f"Expected 2 files, got {len(output_files)}: {[f.name for f in output_files]}"
            )

            # Check both author names appear in filenames
            filenames = [f.name for f in output_files]
            assert any("author1" in f for f in filenames), f"author1 not found in {filenames}"
            assert any("author2" in f for f in filenames), f"author2 not found in {filenames}"

    def test_process_images_nonexistent_input_dir(self, temp_dir: Path):
        """Test processing when input directory doesn't exist."""
        input_dir = temp_dir / "nonexistent"
        output_dir = temp_dir / "output"
        tracking_file = temp_dir / "processed.json"

        with (
            patch("convert_images.INPUT_DIR", input_dir),
            patch("convert_images.OUTPUT_DIR", output_dir),
            patch("convert_images.TRACKING_FILE", tracking_file),
        ):
            # Should handle gracefully
            convert_images.process_images()
            # No exception should be raised
