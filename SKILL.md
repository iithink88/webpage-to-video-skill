---
name: webpage-to-video
description: >
  Convert any HTML step-by-step presentation into a narrated MP4 video.
  Uses edge-tts (Microsoft Edge TTS API) to generate Chinese/English voiceover,
  Playwright (headless Chromium) to record the HTML page with precise slide timing,
  and ffmpeg to merge the audio track with the recorded video.
  Trigger when a user says things like "把网页转成视频", "帮我给这个 HTML 加上语音旁白",
  "生成课件视频", "把演示文稿录成视频", or "网页转视频".
agent_created: true
---

# webpage-to-video

## What This Skill Does

Convert a step-by-step HTML presentation into a narrated MP4 video:

1. **TTS Generation** — Generate one MP3 per slide using Microsoft Edge TTS (`edge-tts`)
2. **Audio Merge** — Concatenate all step audios with configurable silence gaps using `ffmpeg`
3. **Headless Recording** — Record the HTML page in Playwright (headless Chromium), advancing slides with JS calls timed to match audio durations
4. **Final Merge** — Combine webm recording + audio → H.264/AAC MP4

## File Structure

```
scripts/
├── setup_deps.py      — One-click installer for all Python dependencies
├── generate_tts.py    — Step 1: Generate TTS audio from narrations.json
└── make_video.py      — Steps 2-4: Combine audio + record + merge to MP4

references/
├── html-requirements.md        — How the HTML page must be structured
├── narrations_template.json    — Template for narrations.json
└── troubleshooting.md          — Common errors and fixes
```

## Prerequisites

The following Python packages are required. Install them once with:

```bash
python setup_deps.py --mirror tsinghua
```

| Package | Purpose |
|---------|---------|
| `edge-tts` | TTS audio generation via Microsoft Edge API |
| `mutagen` | Precise MP3 duration reading |
| `playwright` | Headless browser video recording |
| `imageio-ffmpeg` | Bundled ffmpeg binary (no manual install) |

**Python 3.9+** is required.

## HTML Page Requirements

The HTML file **must expose a global `advance()` function** that advances to the next slide.
Read `references/html-requirements.md` for the full specification.

Key points:
- `advance()` is called once between each step during recording
- Step count in the HTML must match the narrations count
- Use `null` in narrations for visual-only slides (no audio)

## Step-by-Step Workflow

### Step 0: Prepare narrations.json

Create a JSON file listing narration text for each slide:

```json
[
  "第一页的旁白文字。",
  "第二页的旁白文字。",
  null,
  "第四页（第三页是纯动画，用 null 代替）。"
]
```

- Each element = one slide
- `null` = visual-only slide (no narration, shows for `--visual-dur` seconds)
- The list length **must equal** the total number of slides in the HTML

### Step 1: Generate TTS Audio

```bash
python scripts/generate_tts.py \
  --narrations narrations.json \
  --output-dir ./audio \
  --voice zh-CN-XiaoxiaoNeural \
  --rate +0%
```

Output: `audio/step_00.mp3 ... step_NN.mp3` + `audio/durations.json`

**Available Chinese voices:**
- `zh-CN-XiaoxiaoNeural` — Female, warm, natural (recommended for teaching)
- `zh-CN-YunxiNeural` — Male, natural
- `zh-CN-XiaoyiNeural` — Female, lively
- `zh-TW-HsiaoChenNeural` — Traditional Chinese, female

**English voices:**
- `en-US-JennyNeural` — Female, conversational
- `en-US-GuyNeural` — Male, neutral

Full voice list: `python -c "import asyncio; import edge_tts; asyncio.run(edge_tts.list_voices()).__iter__().__next__()"`
Or visit: https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support

### Step 2-4: Record Video and Merge

```bash
python scripts/make_video.py \
  --html path/to/presentation/index.html \
  --audio-dir ./audio \
  --output-dir ./output
```

Optional parameters:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--advance-fn` | `advance` | JS function name to call for next slide |
| `--transition` | `1.5` | Silence gap between steps (seconds) |
| `--visual-dur` | `3.0` | Duration for visual-only steps (seconds) |
| `--width` | `1920` | Video width in pixels |
| `--height` | `1080` | Video height in pixels |
| `--ffmpeg` | (auto) | Path to custom ffmpeg binary |

Output: `output/output_video.mp4`

## Full Example (Chinese Math Lesson)

```bash
# 1. Create narrations file
cat > narrations.json << 'EOF'
[
  "今天我们来学习三角形的面积公式。",
  "先回顾平行四边形的面积：底乘高。",
  "把两个完全相同的三角形拼起来……",
  "……它们能拼成一个平行四边形！",
  "所以三角形面积等于底乘高除以2。"
]
EOF

# 2. Install dependencies (once)
python scripts/setup_deps.py --mirror tsinghua

# 3. Generate TTS
python scripts/generate_tts.py --narrations narrations.json --output-dir ./audio

# 4. Record + merge
python scripts/make_video.py \
  --html ./presentation/index.html \
  --audio-dir ./audio \
  --output-dir ./output \
  --advance-fn advance \
  --transition 1.5

# Final output: ./output/output_video.mp4
```

## Quality and Output Specs

| Setting | Value |
|---------|-------|
| Video codec | H.264 (libx264) |
| Audio codec | AAC 128 kbps |
| Resolution | 1920×1080 (configurable) |
| Frame rate | 25 fps (Playwright default) |
| CRF | 23 (good quality, ~1-3 MB/min) |
| Container | MP4 (yuv420p, compatible with all players) |

## Windows-Specific Notes

- **PowerShell stdout capture bug**: Scripts write logs to files. If you see no output, check `output/ffmpeg_merge.log` and `audio/duration_result.txt`.
- **ffmpeg path**: `imageio-ffmpeg` bundles a static ffmpeg binary. No manual PATH setup needed.
- **Path separators**: Always use forward slashes in file paths when passing to ffmpeg.
- **npm not required**: This skill is pure Python — no Node.js npm dependency.

## When the Agent Uses This Skill

1. Confirm the HTML file has a working `advance()` function (check source or ask user)
2. Ask user to provide narration texts (or extract from the HTML's existing content)
3. Write `narrations.json` to the project directory
4. Run `setup_deps.py` if dependencies are not yet installed
5. Run `generate_tts.py` → report step count and total audio duration
6. Run `make_video.py` → report output path and file size
7. Deliver the MP4 file to the user

If the slide count in narrations doesn't match the HTML, diagnose by reading the HTML source and counting `advance()` call points or step states.
