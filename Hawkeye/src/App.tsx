import { useState } from 'react'
import {
  BACKEND_BASE,
  generateImage,
  generateVideo,
  mediaUrl,
  type VideoResult,
} from './api'
import './App.css'

const ASPECT_RATIOS = ['16:9', '1:1', '9:16', '4:3', '3:4']

function App() {
  // Shared keyframe: Step 1 produces it, Step 2 animates it.
  const [keyframeUrl, setKeyframeUrl] = useState<string | null>(null)

  // --- Step 1: image ---
  const [imgPrompt, setImgPrompt] = useState(
    'A lone astronaut standing on a red desert planet at sunset, cinematic, wide shot',
  )
  const [aspect, setAspect] = useState('16:9')
  const [imgLoading, setImgLoading] = useState(false)
  const [imgError, setImgError] = useState<string | null>(null)

  // --- Step 2: video ---
  const [vidPrompt, setVidPrompt] = useState(
    'The astronaut slowly turns to face the camera as dust drifts past, gentle camera push-in',
  )
  const [duration, setDuration] = useState('10s')
  const [vidLoading, setVidLoading] = useState(false)
  const [vidError, setVidError] = useState<string | null>(null)
  const [video, setVideo] = useState<VideoResult | null>(null)

  async function runImage() {
    setImgLoading(true)
    setImgError(null)
    setKeyframeUrl(null)
    setVideo(null)
    try {
      const res = await generateImage(imgPrompt, aspect)
      setKeyframeUrl(mediaUrl(res.image_url))
    } catch (e) {
      setImgError(e instanceof Error ? e.message : String(e))
    } finally {
      setImgLoading(false)
    }
  }

  async function runVideo() {
    if (!keyframeUrl) return
    setVidLoading(true)
    setVidError(null)
    setVideo(null)
    try {
      // Pass the keyframe path (strip the backend origin the API added).
      const imagePath = keyframeUrl.replace(BACKEND_BASE, '')
      setVideo(await generateVideo(vidPrompt, imagePath, duration))
    } catch (e) {
      setVidError(e instanceof Error ? e.message : String(e))
    } finally {
      setVidLoading(false)
    }
  }

  return (
    <div className="app">
      <header className="topbar">
        <h1>Hawkeye</h1>
        <span className="tagline">AI Video Studio — keyframe → clip</span>
        <span className="backend">API: {BACKEND_BASE}</span>
      </header>

      <main className="flow">
        {/* Step 1 */}
        <section className="panel">
          <div className="step">
            <span className="badge">1</span>
            <div>
              <h2>Generate keyframe</h2>
              <p className="sub">Nano Banana 2 Lite · the first frame of your shot</p>
            </div>
          </div>

          <label>Image prompt</label>
          <textarea
            value={imgPrompt}
            onChange={(e) => setImgPrompt(e.target.value)}
            rows={3}
          />

          <label>Aspect ratio</label>
          <select value={aspect} onChange={(e) => setAspect(e.target.value)}>
            {ASPECT_RATIOS.map((r) => (
              <option key={r} value={r}>
                {r}
              </option>
            ))}
          </select>

          <button onClick={runImage} disabled={imgLoading || !imgPrompt.trim()}>
            {imgLoading ? 'Generating…' : 'Generate keyframe'}
          </button>

          {imgError && <p className="error">{imgError}</p>}
          {keyframeUrl && (
            <div className="result">
              <img src={keyframeUrl} alt="keyframe" />
              <span className="ok">✓ keyframe ready — animate it below</span>
            </div>
          )}
        </section>

        {/* connector */}
        <div className="connector" aria-hidden="true">
          ↓ image + text
        </div>

        {/* Step 2 */}
        <section className={`panel ${keyframeUrl ? '' : 'disabled'}`}>
          <div className="step">
            <span className="badge">2</span>
            <div>
              <h2>Animate into a clip</h2>
              <p className="sub">
                Omni Flash · the keyframe + your motion prompt → video (takes a
                few minutes)
              </p>
            </div>
          </div>

          {!keyframeUrl && (
            <p className="hint">Generate a keyframe first to unlock this step.</p>
          )}

          <label>Motion prompt</label>
          <textarea
            value={vidPrompt}
            onChange={(e) => setVidPrompt(e.target.value)}
            rows={3}
            disabled={!keyframeUrl}
          />

          <label>Duration</label>
          <select
            value={duration}
            onChange={(e) => setDuration(e.target.value)}
            disabled={!keyframeUrl}
          >
            {['4s', '6s', '8s', '10s'].map((d) => (
              <option key={d} value={d}>
                {d}
              </option>
            ))}
          </select>

          <button
            onClick={runVideo}
            disabled={vidLoading || !keyframeUrl || !vidPrompt.trim()}
          >
            {vidLoading ? 'Generating clip… (please wait)' : 'Generate video from keyframe'}
          </button>
          {vidLoading && (
            <p className="hint">
              The browser will wait until the clip is ready — this can take
              several minutes. Don't close the tab.
            </p>
          )}

          {vidError && <p className="error">{vidError}</p>}
          {video && (
            <div className="result">
              <video src={mediaUrl(video.video_url)} controls />
              <p className="meta">
                interaction_id: <code>{video.interaction_id}</code>
              </p>
              <a
                href={mediaUrl(video.video_url)}
                target="_blank"
                rel="noreferrer"
              >
                open clip ↗
              </a>
            </div>
          )}
        </section>
      </main>
    </div>
  )
}

export default App
