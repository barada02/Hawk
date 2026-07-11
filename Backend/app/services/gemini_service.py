"""Thin wrappers over the google-genai SDK.

Call shapes follow Backend/modelreference.md exactly. Keeping them isolated
here means routes stay dumb and we have one place to adjust when we add
image-conditioned video and the interaction-id chain.
"""

import base64
from functools import lru_cache

from google import genai
from google.genai import types

from app.core.config import settings


@lru_cache
def _client() -> genai.Client:
    # Cached so the single Client (and its HTTP transport) lives for the
    # process. Creating it per call and chaining lets it get GC'd mid-request,
    # which closes the transport ("client has been closed"). Lazy so an unset
    # key doesn't blow up at import time.
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
        if part.inline_data and part.inline_data.data:
            # Raw image bytes straight from the model (already PNG-encoded).
            return part.inline_data.data
    raise RuntimeError("Image model returned no image data")


def generate_video(
    prompt: str,
    image_bytes: bytes | None = None,
    image_mime_type: str = "image/png",
    previous_interaction_id: str | None = None,
) -> tuple[bytes, str]:
    """Omni Flash → (video bytes, interaction_id).

    - `image_bytes`: optional reference image; sent alongside the text so the
      clip animates from that keyframe (image+text → video).
    - `previous_interaction_id`: chains this clip onto a prior one for
      continuity (the interaction-id chain used to build long video).

    Input format follows the Interactions API: a plain string for text-only,
    or a list of typed content blocks when an image is included.
    """
    if image_bytes:
        interaction_input: object = [
            {"type": "text", "text": prompt},
            {
                "type": "image",
                "data": base64.b64encode(image_bytes).decode(),
                "mime_type": image_mime_type,
            },
        ]
    else:
        interaction_input = prompt

    kwargs: dict = {"model": settings.VIDEO_MODEL, "input": interaction_input}
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
