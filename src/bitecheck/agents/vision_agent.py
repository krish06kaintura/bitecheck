"""
Agent 1: Multimodal Vision & Label Ingestion Agent.
Uses Google Gemini 2.5 Flash to extract dense packaging text and tables
into a strictly validated PackagingData Pydantic model.
Includes pre-processing for contrast enhancement, resolution normalization,
and defensive JSON fence stripping.
"""

from pathlib import Path
from PIL import Image, ImageEnhance
from pydantic import ValidationError

from bitecheck.config import settings
from bitecheck.logger import get_logger
from bitecheck.schemas.packaging import PackagingData, NutritionFacts

logger = get_logger("bitecheck.agents.vision")


VISION_SYSTEM_PROMPT = """
You are an expert FSSAI regulatory auditor and food label OCR specialist.
Your task is to inspect the two provided food packaging photographs (Front branding and Back nutrition/ingredients)
and extract structured packaging data with 100% factual fidelity.

RULES:
1. Extract the brand name and exact product title.
2. List all prominent front marketing claims (e.g. "100% Atta", "No Added Sugar", "Rich in Oats").
3. Extract the ingredients list in STRICT DESCENDING ORDER of weight as printed on the label.
4. Extract serving size (grams) and total packet net weight (grams). If serving size is unlisted, set it equal to net weight.
5. Extract nutritional values strictly normalized per 100g.
6. Identify the FSSAI dietary dot: 'GREEN_VEG' (green dot in green square), 'BROWN_NON_VEG' (brown dot in brown square), or 'UNKNOWN'.
7. Extract the 14-digit FSSAI license number if visible.
"""


def preprocess_image(image: Image.Image, max_dimension: int = 1600, contrast_factor: float = 1.15) -> Image.Image:
    """
    Normalizes resolution and enhances contrast to optimize OCR accuracy and reduce network payload.
    - Converts RGBA/P to RGB.
    - Scales down large phone photos (> 1600px) using high-quality Lanczos resampling.
    - Slightly boosts contrast to make small ingredient print legible against glossy pack reflections.
    """
    img = image

    # Ensure standard RGB color space
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    # Downscale if larger than max_dimension
    w, h = img.size
    if max(w, h) > max_dimension:
        if w > h:
            new_w = max_dimension
            new_h = int(h * (max_dimension / w))
        else:
            new_h = max_dimension
            new_w = int(w * (max_dimension / h))
        img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        logger.debug(f"Resized image from ({w}, {h}) to ({new_w}, {new_h})")

    # Slight contrast boost for legibility
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(contrast_factor)
    return img


def clean_json_response(raw_text: str) -> str:
    """
    Defensively strips markdown code fences (```json ... ```) from LLM output.
    """
    text = raw_text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        # Drop the opening fence (e.g., ```json or ```)
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        # Drop the closing fence (```)
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


class VisionAgent:
    """
    Multimodal vision agent responsible for optical label parsing.
    """

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.gemini_api_key
        self.client = None

        if self.api_key and self.api_key != "mock_key_for_testing":
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
                logger.info("Gemini Vision client initialized successfully.")
            except Exception as e:
                logger.warning(f"Failed to initialize live Gemini client: {e}. Falling back to simulation mode.")
        else:
            logger.info("VisionAgent initialized in offline/mock mode.")

    def ingest_packaging(
        self,
        front_image_path: Path | str,
        back_image_path: Path | str,
        preprocess: bool = True
    ) -> PackagingData:
        """
        Processes front and back label images and returns structured PackagingData.
        Applies image pre-processing before invoking the multimodal model.
        """
        front_path = Path(front_image_path)
        back_path = Path(back_image_path)

        if not front_path.exists():
            raise FileNotFoundError(f"Front packaging image not found: {front_path}")
        if not back_path.exists():
            raise FileNotFoundError(f"Back packaging image not found: {back_path}")

        logger.info(f"Ingesting packaging: Front={front_path.name}, Back={back_path.name}")

        # If live client is active, perform live multimodal inference
        if self.client:
            return self._call_gemini_vision(front_path, back_path, preprocess=preprocess)

        # Otherwise, return validated mock extraction for testing & offline development
        return self._mock_extraction(front_path, back_path)

    def _call_gemini_vision(
        self,
        front_path: Path,
        back_path: Path,
        preprocess: bool = True
    ) -> PackagingData:
        """Calls Gemini 2.5 Flash with structured Pydantic schema and preprocessed images."""
        from google.genai import types

        logger.info("Calling Gemini 2.5 Flash with structured output schema...")
        front_img = Image.open(front_path)
        back_img = Image.open(back_path)

        if preprocess:
            front_img = preprocess_image(front_img)
            back_img = preprocess_image(back_img)

        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[front_img, back_img, VISION_SYSTEM_PROMPT],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=PackagingData,
                temperature=0.0,
            )
        )

        cleaned_json = clean_json_response(response.text)

        try:
            # Parse response directly into Pydantic model
            extracted = PackagingData.model_validate_json(cleaned_json)
            logger.info(f"Successfully extracted label data for: {extracted.brand_name} - {extracted.product_name}")
            return extracted
        except ValidationError as e:
            logger.error(f"Pydantic schema validation failed on model output: {e}")
            raise

    def _mock_extraction(self, front_path: Path, back_path: Path) -> PackagingData:
        """
        Deterministic mock parser for local testing, unit tests, and offline runs.
        """
        logger.info("Executing deterministic mock packaging extraction.")
        return PackagingData(
            brand_name="Britannia",
            product_name="NutriChoice Oats Cookies",
            front_claims=["Rich in Oats", "Goodness of Fiber", "Zero Added Sugar"],
            ingredients_raw=[
                "Refined Wheat Flour (Maida) 64%",
                "Palm Oil",
                "Maltodextrin",
                "Rolled Oats 7%",
                "Invert Sugar Syrup",
                "INS 150d",
                "INS 503(ii)",
                "Salt"
            ],
            serving_size_g=15.0,
            net_weight_g=75.0,
            nutrition_per_100g=NutritionFacts(
                energy_kcal=480.0,
                carbohydrates_g=68.0,
                sugar_g=24.0,
                added_sugar_g=18.0,
                dietary_fiber_g=2.1,
                protein_g=6.5,
                fat_g=21.0,
                saturated_fat_g=10.0,
                trans_fat_g=0.1,
                sodium_mg=450.0,
            ),
            dietary_dot="GREEN_VEG",
            fssai_license_number="10015043001234",
        )
