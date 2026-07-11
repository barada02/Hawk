---
name: modelsreference
description: Reference code and instructions for correctly invoking newer Gemini API models (e.g., Nano Banana 2 Lite and Omni Flash) using the new google-genai SDK.
---

# 🚀 Gemini API Models Quick Reference

This reference guide contains clean, concise, and verified code snippets for invoking models using the modern **`google-genai`** Python SDK.

---

## 1️⃣ Client Initialization
Always use the unified `google-genai` SDK and initialize the client:

```python
import os
from google import genai
from google.genai import types

# Initialize client (looks for GEMINI_API_KEY env variable by default)
client = genai.Client()
```

---

## 2️⃣ Nano Banana 2 Lite Image Generation (`gemini-3.1-flash-lite-image`)
⚠️ **CRITICAL:** Do NOT use `client.models.generate_images`. Instead, use `client.models.generate_content` and configure `response_modalities=["IMAGE"]`.

```python
from PIL import Image

# 1. Request image generation (with custom aspect ratio configuration)
response = client.models.generate_content(
    model="gemini-3.1-flash-lite-image",
    contents="A high-fidelity minimalist digital artwork of a banana wearing sunglasses on a neon background",
    config=types.GenerateContentConfig(
        response_modalities=["IMAGE"],
        image_config=types.ImageConfig(
            aspect_ratio="16:9"  # Options include "1:1", "4:3", "9:16", "16:9", etc.
        )
    )
)

# 2. Extract and save the generated image using built-in .as_image() helper
if response.parts:
    for j, part in enumerate(response.parts):
        if part.inline_data:
            image = part.as_image()
            image.save(f"generated_output_{j}.png")
            print(f"Saved: generated_output_{j}.png")
```

---

## 3️⃣ Gemini Omni Flash Video Generation (`gemini-omni-flash-preview`)
⚠️ **CRITICAL:** Use `client.interactions.create` with the Interactions API to generate/edit videos. State is managed server-side via the interaction ID.

```python
import base64

# 1. Request initial video generation
interaction_1 = client.interactions.create(
    model="gemini-omni-flash-preview",
    input="A simple red marble rolling down a wooden ramp, 3D render, minimalist background, 3 seconds"
)

# Save initial video output
if interaction_1.output_video and interaction_1.output_video.data:
    try:
        video_bytes = base64.b64decode(interaction_1.output_video.data)
    except Exception:
        video_bytes = interaction_1.output_video.data
    with open("initial_marble.mp4", "wb") as f:
        f.write(video_bytes)

# 2. Perform stateful conversational editing on the generated video
interaction_2 = client.interactions.create(
    model="gemini-omni-flash-preview",
    input="Change the marble's color to bright neon blue",
    previous_interaction_id=interaction_1.id  # Links the edit to the previous video session
)

# Save edited video output
if interaction_2.output_video and interaction_2.output_video.data:
    try:
        video_bytes_edited = base64.b64decode(interaction_2.output_video.data)
    except Exception:
        video_bytes_edited = interaction_2.output_video.data
    with open("edited_marble.mp4", "wb") as f:
        f.write(video_bytes_edited)
```

---

## 4️⃣ Gemini Live API WebSocket (`gemini-3.1-flash-live-preview`)
⚠️ **CRITICAL:** The model does NOT support text output modality. You must configure `response_modalities=["AUDIO"]`.

```python
import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types
import numpy as np
import sounddevice as sd

# Initialize the client
client = genai.Client()

# Configure connection to receive AUDIO modalities
config = types.LiveConnectConfig(response_modalities=[types.Modality.AUDIO])

def play_audio(pcm_data: bytes):
    # Convert raw PCM (16-bit, little-endian) to numpy array
    audio_array = np.frombuffer(pcm_data, dtype=np.int16)
    # Play at 24kHz sample rate (mono)
    sd.play(audio_array, samplerate=24000)
    sd.wait()

async def run_interactive_session():
    async with client.aio.live.connect(model="gemini-3.1-flash-live-preview", config=config) as session:
        while True:
            user_msg = await asyncio.to_thread(input, "\n👤 You: ")
            if user_msg.lower().strip() in ["quit", "exit"]:
                break
            
            await session.send_realtime_input(text=user_msg)
            
            audio_buffer = bytearray()
            async for response in session.receive():
                if response.server_content is not None:
                    model_turn = response.server_content.model_turn
                    if model_turn:
                        for part in model_turn.parts:
                            if part.inline_data:
                                audio_buffer.extend(part.inline_data.data)
                
                if response.server_content and response.server_content.turn_complete:
                    break
            
            if len(audio_buffer) > 0:
                await asyncio.to_thread(play_audio, bytes(audio_buffer))

asyncio.run(run_interactive_session())
```

---

## 5️⃣ Programmatic Video Stitching (ffmpeg Concat)
To stitch multiple generated video clips dynamically and losslessly without requiring system-level `ffmpeg` installation or risking Python version incompatibilities (e.g., with `moviepy` on Python 3.13+), use `imageio-ffmpeg` to invoke static `ffmpeg` binaries.

### Installation
```bash
pip install imageio-ffmpeg
```

### Usage Snippet
```python
import subprocess
import imageio_ffmpeg
from pathlib import Path

def stitch_videos(clip_paths: list[Path], output_path: Path):
    # 1. Create a temporary inputs list file for the ffmpeg concat demuxer
    inputs_txt_path = output_path.parent / "inputs.txt"
    with open(inputs_txt_path, "w", encoding="utf-8") as f:
        for clip in clip_paths:
            # Use relative filenames in the list to avoid escaping issues
            f.write(f"file '{clip.name}'\n")

    # 2. Get the path to the portable ffmpeg binary
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

    # 3. Build and execute the command (lossless stream copy)
    cmd = [
        ffmpeg_exe,
        "-y",               # Overwrite existing files
        "-f", "concat",     # Use concat demuxer
        "-safe", "0",       # Allow arbitrary paths
        "-i", str(inputs_txt_path),
        "-c", "copy",       # Stream copy (no re-encoding, extremely fast)
        str(output_path)
    ]

    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    # Clean up the list file
    if inputs_txt_path.exists():
        inputs_txt_path.unlink()

    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg failed: {result.stderr}")
    
    print(f"Stitched video saved to {output_path}")
```

