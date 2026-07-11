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

function ImagePanel() {
  const [prompt, setPrompt] = useState(
    'A high-fidelity minimalist digital artwork of a banana wearing sunglasses on a neon background',
  )
  const [aspect, setAspect] = useState('16:9')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [imageUrl, setImageUrl] = useState<string | null>(null)

  async function run() {
    setLoading(true)
    setError(null)
    setImageUrl(null)
    try {
      const res = await generateImage(prompt, aspect)
      setImageUrl(mediaUrl(res.image_url))
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="panel">
      <h2>🖼️ Image generation</h2>
      <p className="sub">Nano Banana 2 Lite · fast</p>

      <label>Prompt</label>
      <textarea
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        rows={4}
      />

      <label>Aspect ratio</label>
      <select value={aspect} onChange={(e) => setAspect(e.target.value)}>
        {ASPECT_RATIOS.map((r) => (
          <option key={r} value={r}>
            {r}
          </option>
        ))}
      </select>

      <button onClick={run} disabled={loading || !prompt.trim()}>
        {loading ? 'Generating…' : 'Generate image'}
      </button>

      {error && <p className="error">{error}</p>}
      {imageUrl && (
        <div className="result">
          <img src={imageUrl} alt="generated" />
          <a href={imageUrl} target="_blank" rel="noreferrer">
            open full size ↗
          </a>
        </div>
      )}
    </section>
  )
}

function VideoPanel() {
  const [prompt, setPrompt] = useState(
    'A simple red marble rolling down a wooden ramp, 3D render, minimalist background, 3 seconds',
  )
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<VideoResult | null>(null)

  async function run() {
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      setResult(await generateVideo(prompt))
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="panel">
      <h2>🎬 Video generation</h2>
      <p className="sub">Omni Flash · takes a few minutes</p>

      <label>Prompt</label>
      <textarea
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        rows={4}
      />

      <button onClick={run} disabled={loading || !prompt.trim()}>
        {loading ? 'Generating… (please wait)' : 'Generate video'}
      </button>
      {loading && (
        <p className="hint">
          The browser will wait until the clip is ready — this can take several
          minutes. Don't close the tab.
        </p>
      )}

      {error && <p className="error">{error}</p>}
      {result && (
        <div className="result">
          <video src={mediaUrl(result.video_url)} controls />
          <p className="meta">
            interaction_id: <code>{result.interaction_id}</code>
          </p>
          <a href={mediaUrl(result.video_url)} target="_blank" rel="noreferrer">
            open clip ↗
          </a>
        </div>
      )}
    </section>
  )
}

function App() {
  return (
    <div className="app">
      <header className="topbar">
        <h1>Hawkeye</h1>
        <span className="tagline">AI Video Studio — test console</span>
        <span className="backend">API: {BACKEND_BASE}</span>
      </header>

      <main className="grid">
        <ImagePanel />
        <VideoPanel />
      </main>
    </div>
  )
}

export default App
