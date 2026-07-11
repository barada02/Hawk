"""Smoke-test the Hawkeye API endpoints.

Run the server first (python main.py), then in another terminal:

    .\\.venv\\Scripts\\python.exe scripts\\test_endpoints.py            # health + image
    .\\.venv\\Scripts\\python.exe scripts\\test_endpoints.py --video    # also the slow video test

Each generated file's URL is fetched back to confirm storage serving works,
and saved into scripts/_test_out/ so you can eyeball the results.
"""

import argparse
import sys
from pathlib import Path

import httpx

OUT_DIR = Path(__file__).parent / "_test_out"


def _download(client: httpx.Client, base_url: str, media_url: str, label: str) -> None:
    """Fetch a returned /media URL and save it locally to prove it's served."""
    resp = client.get(base_url + media_url)
    resp.raise_for_status()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    dest = OUT_DIR / Path(media_url).name
    dest.write_bytes(resp.content)
    print(f"    downloaded {label}: {dest}  ({len(resp.content):,} bytes)")


def test_health(client: httpx.Client, base_url: str) -> None:
    print("\n[1] GET /api/health")
    resp = client.get(base_url + "/api/health")
    resp.raise_for_status()
    print("    ->", resp.json())


def test_image(client: httpx.Client, base_url: str, prompt: str) -> None:
    print("\n[2] POST /api/generate/image")
    print(f"    prompt: {prompt!r}")
    resp = client.post(
        base_url + "/api/generate/image",
        json={"prompt": prompt, "aspect_ratio": "16:9"},
    )
    if resp.status_code != 200:
        print(f"    FAILED [{resp.status_code}]: {resp.text}")
        return
    data = resp.json()
    print("    ->", data)
    _download(client, base_url, data["image_url"], "image")


def test_video(client: httpx.Client, base_url: str, prompt: str) -> None:
    print("\n[3] POST /api/generate/video  (slow — minutes; please wait)")
    print(f"    prompt: {prompt!r}")
    resp = client.post(
        base_url + "/api/generate/video",
        json={"prompt": prompt},
    )
    if resp.status_code != 200:
        print(f"    FAILED [{resp.status_code}]: {resp.text}")
        return
    data = resp.json()
    print("    ->", data)
    _download(client, base_url, data["video_url"], "video")


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-test the Hawkeye API.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument(
        "--video",
        action="store_true",
        help="also run the slow video-generation test",
    )
    parser.add_argument(
        "--image-prompt",
        default="A high-fidelity minimalist digital artwork of a banana wearing "
        "sunglasses on a neon background",
    )
    parser.add_argument(
        "--video-prompt",
        default="A simple red marble rolling down a wooden ramp, 3D render, "
        "minimalist background, 3 seconds",
    )
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    print(f"Testing {base_url}")

    # Generous timeout: video generation can take several minutes.
    with httpx.Client(timeout=600) as client:
        try:
            test_health(client, base_url)
        except httpx.ConnectError:
            print(f"\nCould not connect to {base_url}. Is the server running?")
            return 1

        test_image(client, base_url, args.image_prompt)

        if args.video:
            test_video(client, base_url, args.video_prompt)
        else:
            print("\n[3] Skipping video test (pass --video to run it).")

    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
