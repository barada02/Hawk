"""Generation endpoints — the MVP surface: prompt -> image, prompt -> clip."""

import json
from typing import Callable, Coroutine, Any
from urllib.parse import parse_qs

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.routing import APIRoute
from pydantic import BaseModel

from app.services import gemini_service
from app.services.storage import storage


class RobustRoute(APIRoute):
    def get_route_handler(self) -> Callable[[Request], Coroutine[Any, Any, Response]]:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            content_type = request.headers.get("content-type", "")
            body = await request.body()
            parsed_data = None

            # 1. Try JSON parsing
            try:
                if body:
                    parsed_data = json.loads(body)
            except Exception:
                pass

            # 2. Try URL-encoded form parsing
            if parsed_data is None and body:
                try:
                    decoded_body = body.decode("utf-8", errors="ignore")
                    if "=" in decoded_body and not decoded_body.strip().startswith("{"):
                        qs = parse_qs(decoded_body)
                        parsed_data = {k: v[0] for k, v in qs.items()}
                except Exception:
                    pass

            # 3. Try query parameters as fallback
            if (parsed_data is None or not parsed_data) and request.query_params:
                parsed_data = dict(request.query_params)

            # If we successfully parsed dictionary data, rewrite the request to be JSON!
            if parsed_data is not None and isinstance(parsed_data, dict):
                headers = dict(request.headers)
                headers["content-type"] = "application/json"
                request._headers = headers
                
                new_body = json.dumps(parsed_data).encode("utf-8")
                
                async def new_receive():
                    return {"type": "http.request", "body": new_body, "more_body": False}
                request._receive = new_receive
                request._body = new_body

            return await original_route_handler(request)

        return custom_route_handler


router = APIRouter(prefix="/generate", tags=["generate"], route_class=RobustRoute)


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
