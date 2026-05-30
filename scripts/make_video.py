#!/usr/bin/env python3
"""
make_video.py  —  Step 2 & 3: Record webpage + merge audio into MP4.

This script:
  1. Reads durations.json (produced by generate_tts.py)
  2. Combines all step MP3s into a single audio track (with transition gaps)
  3. Uses Playwright (headless Chromium) to record the HTML page while
     advancing slides with timed JavaScript calls (advance())
  4. Merges the webm recording + combined audio → final MP4 via ffmpeg

Usage:
    python make_video.py --html path/to/index.html --audio-dir ./audio [options]

Required:
    --html         Path to the HTML presentation file
    --audio-dir    Directory containing step_XX.mp3 + durations.json

Optional:
    --output-dir   Output directory (default: ./output)
    --advance-fn   JS function name to advance slide (default: advance)
    --transition   Silence gap between steps in seconds (default: 1.5)
    --visual-dur   Duration for visual-only steps in seconds (default: 3.0)
    --width        Video width (default: 1920)
    --height       Video height (default: 1080)
    --ffmpeg       Path to ffmpeg executable (auto-detected from imageio_ffmpeg)

Requirements:
    pip install edge-tts playwright imageio-ffmpeg mutagen
    playwright install chromium
"""
import argparse
import glob
import json
import os
import subprocess
import sys


def find_ffmpeg(user_path=None):
    """Auto-detect ffmpeg from imageio_ffmpeg or use user-provided path."""
    if user_path and os.path.isfile(user_path):
        return user_path
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        pass
    # Last resort: assume it's in PATH
    return "ffmpeg"


def load_durations(audio_dir):
    path = os.path.join(audio_dir, "durations.json")
    if not os.path.isfile(path):
        print(f"ERROR: durations.json not found in {audio_dir}")
        print("       Run generate_tts.py first.")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def combine_audio(durations, audio_dir, output_dir, ffmpeg, transition_pad, visual_dur):
    """Combine step MP3s + silence gaps into a single combined_audio.mp3."""
    print("=== Step 2: Combining audio ===")
    os.makedirs(output_dir, exist_ok=True)

    # Create silence files
    silence_path = os.path.join(output_dir, f"silence_{transition_pad:.1f}s.mp3")
    vis_silence_path = os.path.join(output_dir, f"silence_{visual_dur:.1f}s.mp3")

    for path, dur in [(silence_path, transition_pad), (vis_silence_path, visual_dur)]:
        if not os.path.exists(path):
            subprocess.run([
                ffmpeg, "-y", "-f", "lavfi",
                "-i", f"anullsrc=r=24000:cl=mono",
                "-t", str(dur),
                "-c:a", "libmp3lame", "-b:a", "48k", path
            ], capture_output=True, timeout=30, check=True)

    # Build concat list
    n_steps = len(durations)
    concat_list = os.path.join(output_dir, "concat_list.txt")
    with open(concat_list, "w", encoding="utf-8") as f:
        for i in range(n_steps):
            step = durations.get(str(i), {})
            dur = step.get("duration", 0)
            if dur > 0:
                mp3 = os.path.join(audio_dir, f"step_{i:02d}.mp3")
                f.write(f"file '{mp3}'\n")
            else:
                f.write(f"file '{vis_silence_path}'\n")
            f.write(f"file '{silence_path}'\n")

    # Concatenate
    combined = os.path.join(output_dir, "combined_audio.mp3")
    result = subprocess.run([
        ffmpeg, "-y", "-f", "concat", "-safe", "0",
        "-i", concat_list,
        "-c:a", "libmp3lame", "-b:a", "128k",
        combined
    ], capture_output=True, text=True, timeout=120)

    if result.returncode != 0:
        print(f"  ERROR combining audio:\n{result.stderr[-500:]}")
        sys.exit(1)

    # Report duration
    try:
        import mutagen
        total = mutagen.File(combined).info.length
        print(f"  Combined audio: {os.path.basename(combined)} ({total:.1f}s)")
    except Exception:
        print(f"  Combined audio: {os.path.basename(combined)}")

    return combined


def record_video(html_path, durations, output_dir, advance_fn,
                 transition_pad, visual_dur, width, height):
    """Use Playwright to record the HTML presentation as webm."""
    print("=== Step 3: Recording video with Playwright ===")

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("ERROR: playwright not installed.")
        print("       Run: pip install playwright && playwright install chromium")
        sys.exit(1)

    n_steps = len(durations)

    # Calculate total recording time
    total_ms = 0
    for i in range(n_steps):
        dur = durations.get(str(i), {}).get("duration", 0)
        wait = (dur if dur > 0 else visual_dur) + transition_pad
        total_ms += int(wait * 1000)
    total_ms += 3000  # Final buffer

    print(f"  Slides: {n_steps}  |  Expected duration: {total_ms/1000:.1f}s")

    html_url = f"file:///{os.path.abspath(html_path).replace(os.sep, '/')}"
    print(f"  Loading: {html_url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": width, "height": height},
            record_video_dir=output_dir,
            record_video_size={"width": width, "height": height},
        )
        page = context.new_page()
        page.goto(html_url, timeout=30000)
        page.wait_for_timeout(3000)  # Wait for fonts/animations to load

        for i in range(n_steps):
            dur = durations.get(str(i), {}).get("duration", 0)
            wait_ms = int(((dur if dur > 0 else visual_dur) + transition_pad) * 1000)
            print(f"  Slide {i:02d}: {wait_ms/1000:.1f}s")
            page.wait_for_timeout(wait_ms)
            if i < n_steps - 1:
                page.evaluate(f"{advance_fn}()")

        page.wait_for_timeout(2000)  # Linger on last slide
        context.close()
        browser.close()

    # Find the webm output
    webm_files = sorted(glob.glob(os.path.join(output_dir, "*.webm")), key=os.path.getmtime)
    if not webm_files:
        print("  ERROR: Playwright produced no .webm file. Check output directory.")
        sys.exit(1)

    video_path = webm_files[-1]
    print(f"  Raw video: {os.path.basename(video_path)}")
    return video_path


def merge_video_audio(video_path, audio_path, output_dir, ffmpeg):
    """Merge webm video + MP3 audio into final MP4."""
    print("=== Step 4: Merging video + audio → MP4 ===")

    out_name = os.path.splitext(os.path.basename(video_path))[0]
    final_path = os.path.join(output_dir, "output_video.mp4")

    result = subprocess.run([
        ffmpeg, "-y",
        "-i", video_path,
        "-i", audio_path,
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "128k",
        "-shortest",
        "-pix_fmt", "yuv420p",
        final_path
    ], capture_output=True, text=True, timeout=600)

    if result.returncode != 0:
        print(f"  ERROR merging:\n{result.stderr[-600:]}")
        # Save log
        log_path = os.path.join(output_dir, "ffmpeg_merge.log")
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(result.stderr)
        print(f"  Full log saved to: {log_path}")
        sys.exit(1)

    size_mb = os.path.getsize(final_path) / (1024 * 1024)
    print(f"  Final video: {final_path} ({size_mb:.1f} MB)")
    return final_path


def main():
    parser = argparse.ArgumentParser(description="Record HTML presentation and combine with TTS audio")
    parser.add_argument("--html", required=True, help="Path to HTML presentation file")
    parser.add_argument("--audio-dir", default="./audio", help="Directory with step MP3s + durations.json")
    parser.add_argument("--output-dir", default="./output", help="Output directory")
    parser.add_argument("--advance-fn", default="advance", help="JS function to advance slide")
    parser.add_argument("--transition", type=float, default=1.5, help="Gap between steps (seconds)")
    parser.add_argument("--visual-dur", type=float, default=3.0, help="Duration for visual-only steps (seconds)")
    parser.add_argument("--width", type=int, default=1920)
    parser.add_argument("--height", type=int, default=1080)
    parser.add_argument("--ffmpeg", default=None, help="Path to ffmpeg executable")
    args = parser.parse_args()

    ffmpeg = find_ffmpeg(args.ffmpeg)
    print(f"Using ffmpeg: {ffmpeg}")

    audio_dir = os.path.abspath(args.audio_dir)
    output_dir = os.path.abspath(args.output_dir)
    html_path = os.path.abspath(args.html)

    if not os.path.isfile(html_path):
        print(f"ERROR: HTML file not found: {html_path}")
        sys.exit(1)

    durations = load_durations(audio_dir)
    print(f"Loaded {len(durations)} step durations.")

    combined_audio = combine_audio(
        durations, audio_dir, output_dir, ffmpeg,
        args.transition, args.visual_dur
    )

    video_path = record_video(
        html_path, durations, output_dir,
        args.advance_fn, args.transition, args.visual_dur,
        args.width, args.height
    )

    final = merge_video_audio(video_path, combined_audio, output_dir, ffmpeg)

    print(f"\n{'='*55}")
    print(f"  Done! Output: {final}")
    print(f"{'='*55}")


if __name__ == "__main__":
    main()
