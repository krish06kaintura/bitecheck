"""
Unit tests for Phase 3: Agent 1 Multimodal Vision & Ingestion.
"""

from pathlib import Path
from PIL import Image
import pytest

from bitecheck.agents.vision_agent import VisionAgent, preprocess_image, clean_json_response
from bitecheck.schemas.packaging import PackagingData


@pytest.fixture
def mock_images(tmp_path: Path):
    """Creates temporary dummy front and back images for testing."""
    front_path = tmp_path / "front.png"
    back_path = tmp_path / "back.png"

    img = Image.new("RGB", (2000, 1000), color="white")
    img.save(front_path)
    img.save(back_path)

    return front_path, back_path


def test_vision_agent_mock_extraction(mock_images):
    """Verifies that VisionAgent processes images and returns valid PackagingData."""
    front_path, back_path = mock_images
    agent = VisionAgent()

    data = agent.ingest_packaging(front_path, back_path)

    assert isinstance(data, PackagingData)
    assert data.brand_name == "Britannia"
    assert data.product_name == "NutriChoice Oats Cookies"
    assert len(data.ingredients_raw) > 0
    assert data.serving_size_g == 15.0
    assert data.net_weight_g == 75.0
    assert data.nutrition_per_100g.energy_kcal == 480.0


def test_vision_agent_missing_image_raises_error(tmp_path: Path):
    """Verifies that missing image paths raise FileNotFoundError."""
    agent = VisionAgent()
    missing_front = tmp_path / "non_existent_front.jpg"
    valid_back = tmp_path / "back.jpg"
    Image.new("RGB", (10, 10)).save(valid_back)

    with pytest.raises(FileNotFoundError):
        agent.ingest_packaging(missing_front, valid_back)


def test_preprocess_image_resizes_and_normalizes():
    """Verifies that large photos are resized to max_dimension and RGBA is converted to RGB."""
    large_rgba = Image.new("RGBA", (3000, 2000), color=(255, 0, 0, 255))
    processed = preprocess_image(large_rgba, max_dimension=1600)

    assert processed.mode == "RGB"
    assert processed.size[0] == 1600
    assert processed.size[1] == int(2000 * (1600 / 3000))


def test_clean_json_response_strips_markdown_fences():
    """Verifies that ```json ... ``` markdown wrappers are cleanly stripped."""
    raw = "```json\n{\"brand_name\": \"TestBrand\"}\n```"
    cleaned = clean_json_response(raw)
    assert cleaned == "{\"brand_name\": \"TestBrand\"}"

    raw_plain = "{\"brand_name\": \"TestBrand\"}"
    assert clean_json_response(raw_plain) == "{\"brand_name\": \"TestBrand\"}"
