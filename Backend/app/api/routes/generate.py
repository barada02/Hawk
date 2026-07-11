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
    # Chain this clip onto a previous one (continuity). Optional for the MVP.
    previous_interaction_id: str | None = None


class VideoResponse(BaseModel):
    video_url: str
    interaction_id: str


@router.post("/video", response_model=VideoResponse)
def create_video(req: VideoRequest) -> VideoResponse:
    try:
        data, interaction_id = gemini_service.generate_video(
            req.prompt, req.previous_interaction_id
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Video generation failed: {exc}")
    return VideoResponse(
        video_url=storage.save(data, "mp4"),
        interaction_id=interaction_id,
    )
