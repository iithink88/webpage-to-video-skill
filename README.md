# webpage-to-video-skill

Convert any HTML step-by-step presentation into a narrated MP4 video.(能网页转成视频，并自动生成语音旁白，和页面同步。)

## What It Does

1. **TTS Generation** — Generate one MP3 per slide using Microsoft Edge TTS (`edge-tts`)
2. **Audio Merge** — Concatenate all step audios with configurable silence gaps using `ffmpeg`
3. **Headless Recording** — Record the HTML page in Playwright (headless Chromium), advancing slides with JS calls timed to match audio durations
4. **Final Merge** — Combine webm recording + audio into H.264/AAC MP4

## Quick Start

```bash
# 1. Install dependencies
python scripts/setup_deps.py --mirror tsinghua

# 2. Generate TTS audio
python scripts/generate_tts.py --narrations narrations.json --output-dir ./audio

# 3. Record video and merge
python scripts/make_video.py --html ./presentation/index.html --audio-dir ./audio --output-dir ./output
```

## HTML Requirements

Your HTML page **must expose a global `advance()` function** that moves to the next slide.

See [references/html-requirements.md](references/html-requirements.md) for the full specification.

## Narrations Format

Create a `narrations.json` file:

```json
[
  "First slide narration.",
  "Second slide narration.",
  null,
  "Fourth slide (null = visual-only, no audio)."
]
```

## Tech Stack

| Component | Tool |
|-----------|------|
| TTS | Microsoft Edge TTS API (`edge-tts`) |
| Recording | Playwright (headless Chromium) |
| Audio/Video | ffmpeg (bundled via `imageio-ffmpeg`) |
| Language | Python 3.9+ |

## Output Specs

| Setting | Value |
|---------|-------|
| Video codec | H.264 (libx264) |
| Audio codec | AAC 128 kbps |
| Resolution | 1920x1080 (configurable) |
| Frame rate | 25 fps |
| Container | MP4 |

## License

MIT
