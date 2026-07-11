"""Generation endpoints — the MVP surface: prompt -> image, prompt -> clip."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services import gemini_service
from app.services.storage import storage

router = APIRouter(prefix="/generate", tags=["generate"])


class ImageRequest(BaseModel):
    prompt: str
    aspect_ratio: str | None = None


class ImageResponse(BaseModel):
    image_url: str


@router.post("/image", response_model=ImageResponse)
def create_image(req: ImageRequest) -> ImageResponse:
    try:
        data = gemini_service.generate_image(req.prompt, req.aspect_ratio)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Image generation failed: {exc}")
    return ImageResponse(image_url=storage.save(data, "png"))


class VideoRequest(BaseModel):
    prompt: str
    # A previously generated keyframe (from /generate/image) to animate from.
    image_url: str | None = None
    # Clip length, e.g. "10s". Defaults to settings when omitted.
    duration: str | None = None
    # Chain this clip onto a previous one (continuity). Optional for the MVP.
    previous_interaction_id: str | None = None


class VideoResponse(BaseModel):
    video_url: str
    interaction_id: str


_MIME_BY_EXT = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "webp": "image/webp"}


@router.post("/video", response_model=VideoResponse)
def create_video(req: VideoRequest) -> VideoResponse:
    image_bytes: bytes | None = None
    image_mime = "image/png"
    if req.image_url:
        try:
            image_bytes = storage.read(req.image_url)
        except Exception as exc:
            raise HTTPException(
                status_code=400, detail=f"Could not load reference image: {exc}"
            )
        ext = req.image_url.rsplit(".", 1)[-1].lower()
        image_mime = _MIME_BY_EXT.get(ext, "image/png")

    try:
        data, interaction_id = gemini_service.generate_video(
            req.prompt,
            image_bytes=image_bytes,
            image_mime_type=image_mime,
            duration=req.duration,
            previous_interaction_id=req.previous_interaction_id,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Video generation failed: {exc}")
    return VideoResponse(
        video_url=storage.save(data, "mp4"),
        interaction_id=interaction_id,
    )
