"""Thin wrappers over the google-genai SDK.

Call shapes follow Backend/modelreference.md exactly. Keeping them isolated
here means routes stay dumb and we have one place to adjust when we add
image-conditioned video and the interaction-id chain.
"""

import base64
import io

from google import genai
from google.genai import types

from app.core.config import settings


def _client() -> genai.Client:
    # Explicit key from settings (loaded from .env); on Cloud Run the same
    # env var is present. Created per call is cheap and avoids import-time
    # failures when the key isn't set yet.
    if settings.GEMINI_API_KEY:
        return genai.Client(api_key=settings.GEMINI_API_KEY)
    return genai.Client()


def generate_image(prompt: str, aspect_ratio: str | None = None) -> bytes:
    """Nano Banana 2 Lite → PNG bytes of a single generated image."""
    response = _client().models.generate_content(
        model=settings.IMAGE_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(
                aspect_ratio=aspect_ratio or settings.DEFAULT_ASPECT_RATIO,
            ),
        ),
    )
    for part in response.parts or []:
        if part.inline_data:
            buf = io.BytesIO()
            part.as_image().save(buf, format="PNG")
            return buf.getvalue()
    raise RuntimeError("Image model returned no image data")


def generate_video(
    prompt: str,
    previous_interaction_id: str | None = None,
) -> tuple[bytes, str]:
    """Omni Flash → (video bytes, interaction_id).

    `previous_interaction_id` chains this clip onto a prior one for continuity
    (used in later stages). Image-conditioned input comes next once we confirm
    the exact `input=` format for passing an image into interactions.create.
    """
    kwargs: dict = {"model": settings.VIDEO_MODEL, "input": prompt}
    if previous_interaction_id:
        kwargs["previous_interaction_id"] = previous_interaction_id

    interaction = _client().interactions.create(**kwargs)

    output = interaction.output_video
    if not (output and output.data):
        raise RuntimeError("Video model returned no video data")

    try:
        video_bytes = base64.b64decode(output.data)
    except Exception:
        video_bytes = output.data

    return video_bytes, interaction.id
