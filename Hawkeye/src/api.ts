// Fallback to local dev if placeholder is not replaced at container startup
const PLACEHOLDER = '__VITE_BACKEND_URI_PLACEHOLDER__'
export const BACKEND_BASE = (
  PLACEHOLDER.startsWith('__VITE')
    ? (import.meta.env.VITE_BACKEND_URI || 'http://127.0.0.1:8000')
    : PLACEHOLDER
).replace(/\/$/, '')

// Media URLs from the API are relative (e.g. /media/xyz.png) — prefix them.
export function mediaUrl(path: string): string {
  return /^https?:\/\//.test(path) ? path : BACKEND_BASE + path
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(BACKEND_BASE + path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const detail = await res
      .json()
      .then((d) => d?.detail)
      .catch(() => null)
    throw new Error(detail || `Request failed (HTTP ${res.status})`)
  }
  return res.json() as Promise<T>
}

export interface ImageResult {
  image_url: string
}

export interface VideoResult {
  video_url: string
  interaction_id: string
}

export function generateImage(prompt: string, aspectRatio: string) {
  return postJson<ImageResult>('/api/generate/image', {
    prompt,
    aspect_ratio: aspectRatio,
  })
}

export function generateVideo(
  prompt: string,
  imageUrl?: string,
  duration?: string,
) {
  return postJson<VideoResult>('/api/generate/video', {
    prompt,
    image_url: imageUrl ?? null,
    duration: duration ?? null,
  })
}
