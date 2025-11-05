"""Pytest configuration and fixtures."""

import shutil
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest
from PIL import Image


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def sample_image_rgb(temp_dir: Path) -> Path:
    """Create a sample RGB test image."""
    img_path = temp_dir / "test_image.jpg"
    img = Image.new("RGB", (100, 100), color=(255, 0, 0))
    img.save(img_path, "JPEG")
    return img_path


@pytest.fixture
def sample_image_rgba(temp_dir: Path) -> Path:
    """Create a sample RGBA test image with transparency."""
    img_path = temp_dir / "test_image_rgba.png"
    img = Image.new("RGBA", (100, 100), color=(0, 255, 0, 128))
    img.save(img_path, "PNG")
    return img_path


@pytest.fixture
def sample_image_png(temp_dir: Path) -> Path:
    """Create a sample PNG test image."""
    img_path = temp_dir / "test_image.png"
    img = Image.new("RGB", (50, 50), color=(0, 0, 255))
    img.save(img_path, "PNG")
    return img_path


@pytest.fixture
def test_input_dir(temp_dir: Path) -> Path:
    """Create a test input-images directory structure."""
    input_dir = temp_dir / "input-images"
    input_dir.mkdir(parents=True)
    return input_dir


@pytest.fixture
def test_output_dir(temp_dir: Path) -> Path:
    """Create a test output directory."""
    output_dir = temp_dir / "output"
    output_dir.mkdir(parents=True)
    return output_dir


@pytest.fixture
def author_folder(test_input_dir: Path, sample_image_rgb: Path) -> tuple[Path, Path]:
    """Create an author folder with a test image."""
    author_dir = test_input_dir / "test_author"
    author_dir.mkdir()

    # Copy sample image to author folder
    test_image = author_dir / "test_image.jpg"
    shutil.copy(sample_image_rgb, test_image)

    return author_dir, test_image
