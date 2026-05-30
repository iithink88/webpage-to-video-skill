# Troubleshooting Guide — webpage-to-video

## Common Issues and Fixes

---

### 1. pip install timeout / slow download

**Symptom**: `pip install` hangs or times out.

**Fix**: Use a Chinese mirror:
```bash
pip install edge-tts -i https://pypi.tuna.tsinghua.edu.cn/simple
# Or use setup_deps.py which handles this automatically:
python setup_deps.py --mirror tsinghua
```

---

### 2. No `.webm` file produced by Playwright

**Symptom**: After `make_video.py` runs, no `*.webm` file appears in the output directory.

**Possible causes**:
- `context.close()` was not called — the webm is only finalized when the context is closed.
  The script handles this, but check that it ran to completion.
- The HTML file path contains special characters — use forward slashes in the URL.
- Chromium crashed — check `playwright.log` or increase timeout.

**Fix**: Run with Python directly and check stderr output:
```bash
python make_video.py --html path/to/index.html --audio-dir ./audio 2>&1 | tee run.log
```

---

### 3. `advance()` is not defined / JS error

**Symptom**: Console error in Playwright: `advance is not a function`.

**Fix**: Make sure the HTML exposes a global `advance()` function, or pass the correct function name:
```bash
python make_video.py --html ... --advance-fn nextSlide
```

---

### 4. Video and audio are out of sync

**Symptom**: The video shows slide N+1 while the audio for slide N is still playing, or vice versa.

**Causes**:
- `durations.json` has inaccurate timings (estimated from file size).
- Use `mutagen` to get precise durations: it will update `durations.json` automatically
  when `make_video.py` loads it (because `generate_tts.py` uses mutagen if available).

**Fix**: Re-run `generate_tts.py` after installing mutagen:
```bash
pip install mutagen
python generate_tts.py --narrations narrations.json --output-dir ./audio
```

---

### 5. `imageio_ffmpeg` not found / ffmpeg not available

**Symptom**: `FileNotFoundError: ffmpeg` or `imageio_ffmpeg` import error.

**Fix**:
```bash
pip install imageio-ffmpeg
```

Or specify a custom ffmpeg path:
```bash
python make_video.py --html ... --ffmpeg "C:/path/to/ffmpeg.exe"
```

---

### 6. Chinese characters garbled in TTS / output file

**Symptom**: MP3 files are silent or TTS throws an encoding error.

**Fix**: Make sure `narrations.json` is saved in **UTF-8 encoding** (not GBK/GB2312).
In Windows Notepad, use "Save As → Encoding: UTF-8".

---

### 7. `playwright install chromium` fails

**Symptom**: Chromium download fails or times out.

**Fix**: Set the Playwright download mirror (Chinese mainland):
```bash
# PowerShell
$env:PLAYWRIGHT_DOWNLOAD_HOST = "https://npmmirror.com/mirrors/playwright"
python -m playwright install chromium
```

---

### 8. Final MP4 has no audio

**Symptom**: `output_video.mp4` plays but is silent.

**Possible causes**:
- `combined_audio.mp3` was not created successfully (check for errors in step 2).
- The `concat_list.txt` references paths with backslashes — ffmpeg `concat` demuxer requires forward slashes.

**Fix**: The script converts paths automatically. If it still fails, check `concat_list.txt` manually
and ensure all file paths are valid and accessible.

---

### 9. Output video is too large

**Symptom**: MP4 file size is unexpectedly large (e.g., > 50 MB for a 2-minute video).

**Fix**: Reduce CRF (higher = more compression, lower quality):
```bash
# In make_video.py, change: "-crf", "23"  →  "-crf", "28"
```

Or add `-vf scale=1280:720` to downscale the video to 720p.

---

### 10. PowerShell subprocess output is empty

**Symptom**: Running Python scripts via PowerShell shows no output.

**This is a known Windows/PowerShell issue.** The scripts write logs to files as a workaround.
Run scripts via `python script.py > out.txt 2>&1` and check the log file,
or run directly in a CMD window instead of PowerShell.
