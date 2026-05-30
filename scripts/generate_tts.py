#!/usr/bin/env python3
"""
generate_tts.py  —  Step 1: Generate TTS audio narration files.

Usage:
    python generate_tts.py --narrations narrations.json [options]

Arguments:
    --narrations   Path to JSON file with narration texts (list of strings).
                   Index 0 = step 00, index 1 = step 01, ...
                   Use null for visual-only steps (no audio).
    --output-dir   Directory to save step_XX.mp3 + durations.json (default: ./audio)
    --voice        edge-tts voice name (default: zh-CN-XiaoxiaoNeural)
    --rate         speech rate, e.g. +0% +10% -5% (default: +0%)

Output:
    audio/step_00.mp3 ... step_NN.mp3
    audio/durations.json  — precise per-step durations
"""
import argparse
import asyncio
import json
import os
import sys


def get_mp3_duration_mutagen(filepath):
    """Get precise MP3 duration using mutagen (preferred)."""
    try:
        import mutagen
        audio = mutagen.File(filepath)
        return audio.info.length
    except Exception:
        return None


def get_mp3_duration_estimate(filepath):
    """Fallback: estimate duration from file size (assume ~48 kbps)."""
    try:
        file_size = os.path.getsize(filepath)
        return max((file_size * 8) / 48000, 0.5)
    except Exception:
        return 3.0


def get_mp3_duration(filepath):
    dur = get_mp3_duration_mutagen(filepath)
    if dur is None:
        dur = get_mp3_duration_estimate(filepath)
    return round(dur, 3)


async def generate_one(text, idx, output_dir, voice, rate):
    """Generate a single TTS MP3 file."""
    try:
        import edge_tts
    except ImportError:
        print("ERROR: edge-tts not installed. Run: pip install edge-tts")
        sys.exit(1)

    outpath = os.path.join(output_dir, f"step_{idx:02d}.mp3")
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    await communicate.save(outpath)
    duration = get_mp3_duration(outpath)
    return idx, outpath, duration


async def main():
    parser = argparse.ArgumentParser(description="Generate TTS audio for webpage-to-video workflow")
    parser.add_argument("--narrations", required=True, help="Path to JSON narrations file")
    parser.add_argument("--output-dir", default="./audio", help="Output directory for MP3 files")
    parser.add_argument("--voice", default="zh-CN-XiaoxiaoNeural", help="edge-tts voice name")
    parser.add_argument("--rate", default="+0%", help="Speech rate (e.g. +0%, +10%)")
    args = parser.parse_args()

    # Load narrations
    with open(args.narrations, "r", encoding="utf-8") as f:
        narrations = json.load(f)

    if not isinstance(narrations, list):
        print("ERROR: narrations JSON must be a list of strings (use null for visual-only steps).")
        sys.exit(1)

    output_dir = os.path.abspath(args.output_dir)
    os.makedirs(output_dir, exist_ok=True)

    durations = {}
    for i, text in enumerate(narrations):
        if text is None:
            print(f"Step {i:02d}: [visual only, skipped]")
            durations[str(i)] = {"file": None, "duration": 0, "text": "[visual only]"}
            continue

        print(f"Generating step {i:02d}: {text[:40]}...")
        idx, path, dur = await generate_one(text, i, output_dir, args.voice, args.rate)
        size = os.path.getsize(path)
        print(f"  -> {os.path.basename(path)} ({size} bytes, {dur:.2f}s)")
        durations[str(i)] = {
            "file": os.path.basename(path),
            "duration": dur,
            "text": text[:60] + "..." if len(text) > 60 else text,
        }

    # Save durations.json
    durations_path = os.path.join(output_dir, "durations.json")
    with open(durations_path, "w", encoding="utf-8") as f:
        json.dump(durations, f, ensure_ascii=False, indent=2)

    total = sum(d["duration"] for d in durations.values())
    print(f"\nSaved durations.json  —  total narration: {total:.1f}s ({total/60:.1f} min)")
    print(f"Output: {output_dir}")


if __name__ == "__main__":
    asyncio.run(main())
