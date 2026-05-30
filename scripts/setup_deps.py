#!/usr/bin/env python3
"""
setup_deps.py  —  One-click dependency installer for webpage-to-video.

Checks and installs:
  - edge-tts       (TTS generation)
  - mutagen        (precise MP3 duration)
  - playwright     (headless browser recording)
  - imageio-ffmpeg (bundled ffmpeg binary)

Then runs: playwright install chromium

Usage:
    python setup_deps.py [--mirror tsinghua]
"""
import subprocess
import sys
import os
import argparse

PACKAGES = [
    ("edge-tts", "edge_tts"),
    ("mutagen", "mutagen"),
    ("playwright", "playwright"),
    ("imageio-ffmpeg", "imageio_ffmpeg"),
]

PYPI_MIRRORS = {
    "tsinghua": "https://pypi.tuna.tsinghua.edu.cn/simple",
    "aliyun":   "https://mirrors.aliyun.com/pypi/simple",
    "douban":   "https://pypi.douban.com/simple",
    "default":  None,
}


def run_pip(args, mirror=None):
    cmd = [sys.executable, "-m", "pip"] + args
    if mirror:
        cmd += ["-i", mirror, "--trusted-host", mirror.split("/")[2]]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    return result


def check_installed(import_name):
    result = subprocess.run(
        [sys.executable, "-c", f"import {import_name}"],
        capture_output=True, text=True
    )
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description="Install webpage-to-video dependencies")
    parser.add_argument("--mirror", default="tsinghua",
                        choices=list(PYPI_MIRRORS.keys()),
                        help="PyPI mirror to use (default: tsinghua)")
    args = parser.parse_args()
    mirror = PYPI_MIRRORS.get(args.mirror)

    print("=" * 50)
    print("Webpage-to-Video: Dependency Setup")
    print("=" * 50)

    all_ok = True
    for pkg_name, import_name in PACKAGES:
        if check_installed(import_name):
            print(f"  [OK] {pkg_name} already installed")
        else:
            print(f"  [..] Installing {pkg_name}...", end=" ", flush=True)
            r = run_pip(["install", pkg_name], mirror=mirror)
            if r.returncode == 0:
                print("OK")
            else:
                print("FAILED")
                print(f"       {r.stderr[-300:]}")
                all_ok = False

    # Install Chromium for Playwright
    print("\n  [..] Installing Playwright Chromium browser...", end=" ", flush=True)
    r = subprocess.run(
        [sys.executable, "-m", "playwright", "install", "chromium"],
        capture_output=True, text=True, timeout=300
    )
    if r.returncode == 0:
        print("OK")
    else:
        print("FAILED")
        print(f"       {r.stderr[-300:]}")
        all_ok = False

    # Report ffmpeg path
    try:
        import imageio_ffmpeg
        ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
        print(f"\n  ffmpeg path: {ffmpeg_path}")
    except Exception:
        print("\n  WARNING: Could not find ffmpeg via imageio_ffmpeg.")

    print("\n" + ("=" * 50))
    if all_ok:
        print("  All dependencies installed successfully!")
        print("  You can now run generate_tts.py and make_video.py")
    else:
        print("  Some installations failed. Please check errors above.")
    print("=" * 50)


if __name__ == "__main__":
    main()
