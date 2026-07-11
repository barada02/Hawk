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


def _extract_video_bytes(interaction) -> bytes | None:
    """Pull the video bytes out of an interaction's model_output steps."""
    for step in getattr(interaction, "steps", None) or []:
        if step.type == "model_output" and step.content:
            for part in step.content:
                if part.type == "video":
                    data = getattr(part, "data", None)
                    if data:
                        try:
                            return base64.b64decode(data)
                        except Exception:
                            return data
    return None


def generate_video(
    prompt: str,
    image_bytes: bytes | None = None,
    image_mime_type: str = "image/png",
    previous_interaction_id: str | None = None,
    duration: str | None = None,
) -> tuple[bytes, str]:
    """Omni Flash → (video bytes, interaction_id).

    - `image_bytes`: optional reference image; sent alongside the text so the
      clip animates from that keyframe (image+text → video).
    - `previous_interaction_id`: chains this clip onto a prior one for
      continuity (the interaction-id chain used to build long video).
    - `duration`: clip length (e.g. "10s"); defaults to settings.

    Follows the working call shape: an explicit generation_config,
    response_modalities=['video'], and a response_format carrying the
    duration. Crucially, when an image is supplied we set
    video_config.task='image_to_video' so the model conditions on the
    keyframe (otherwise it largely ignores it → inconsistent output).
    """
    if image_bytes:
        task = "image_to_video"
        interaction_input: object = [
            {"type": "text", "text": prompt},
            {
                "type": "image",
                "data": base64.b64encode(image_bytes).decode(),
                "mime_type": image_mime_type,
                "resolution": settings.VIDEO_IMAGE_RESOLUTION,
            },
        ]
    else:
        task = "text_to_video"
        interaction_input = prompt

    kwargs: dict = {
        "model": settings.VIDEO_MODEL,
        "input": interaction_input,
        "generation_config": {
            "max_output_tokens": settings.VIDEO_MAX_OUTPUT_TOKENS,
            "thinking_level": settings.VIDEO_THINKING_LEVEL,
            "video_config": {"task": task},
        },
        "response_modalities": ["video"],
        "response_format": {
            "type": "video",
            "duration": duration or settings.VIDEO_DURATION,
        },
    }
    if previous_interaction_id:
        kwargs["previous_interaction_id"] = previous_interaction_id

    interaction = _client().interactions.create(**kwargs)

    video_bytes = _extract_video_bytes(interaction)
    if video_bytes is None:
        raise RuntimeError("Video model returned no video data")

    return video_bytes, interaction.id
