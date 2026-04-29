# backend/tests/test_thumbnail.py
import os
from PIL import Image
from app.scanner.thumbnail import generate_thumbnail


def test_generate_thumbnail_creates_file(test_image, tmp_path):
    thumb_dir = str(tmp_path / "thumbs")
    source_root = os.path.dirname(test_image)

    result_path = generate_thumbnail(test_image, thumb_dir, source_root, size=300)

    assert os.path.exists(result_path)
    thumb = Image.open(result_path)
    assert thumb.width <= 300
    assert result_path.endswith(".jpg")


def test_generate_thumbnail_mirrors_structure(test_image, tmp_path):
    thumb_dir = str(tmp_path / "thumbs")
    source_root = os.path.dirname(os.path.dirname(test_image))

    result_path = generate_thumbnail(test_image, thumb_dir, source_root, size=300)

    rel = os.path.relpath(result_path, thumb_dir)
    expected_rel = os.path.relpath(test_image, source_root) + ".jpg"
    assert rel == expected_rel


def test_thumbnail_creates_parent_dirs(test_image, tmp_path):
    thumb_dir = str(tmp_path / "deep" / "nested" / "thumbs")
    source_root = os.path.dirname(test_image)

    result_path = generate_thumbnail(test_image, thumb_dir, source_root, size=300)

    assert os.path.exists(result_path)
