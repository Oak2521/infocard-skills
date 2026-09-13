#!/usr/bin/env python3
"""Capture a local card with an already installed Chromium browser."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

RATIOS = {"3:4": (1500, 2000), "4:3": (2000, 1500), "1:1": (1800, 1800),
          "16:9": (1920, 1080), "9:16": (1080, 1920), "2.35:1": (2350, 1000),
          "3:1": (1800, 600), "5:2": (2500, 1000)}


def find_browser(env=None):
    env = os.environ if env is None else env
    override = env.get("CHROME_BIN")
    if override:
        found = shutil.which(override, path=env.get("PATH", ""))
        if found:
            return found
        raise FileNotFoundError("CHROME_BIN does not identify an executable browser")
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser",
                 "chrome", "chrome.exe", "msedge", "msedge.exe"):
        found = shutil.which(name, path=env.get("PATH", ""))
        if found:
            return found
    candidates = [Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
                  Path("/Applications/Chromium.app/Contents/MacOS/Chromium"),
                  Path("/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge")]
    for key in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA"):
        if env.get(key):
            for suffix in ("Google/Chrome/Application/chrome.exe", "Microsoft/Edge/Application/msedge.exe"):
                candidates.append(Path(env[key]) / suffix)
    for candidate in candidates:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    raise FileNotFoundError("No installed Chrome/Chromium/Edge found. Set CHROME_BIN; no browser was downloaded.")


def capture(input_path, output_path, ratio):
    source = Path(input_path).resolve(strict=True)
    if not source.is_file():
        raise ValueError("Input must be a local HTML file")
    width, height = RATIOS[ratio]
    browser = find_browser()
    target = Path(output_path).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    # Isolated temporary profile avoids touching an existing user's browser session.
    with tempfile.TemporaryDirectory(prefix="infocard-") as profile:
        subprocess.run([browser, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                        "--no-first-run", "--no-default-browser-check", "--disable-background-networking",
                        f"--user-data-dir={profile}", "--virtual-time-budget=5000",
                        "--force-device-scale-factor=1", f"--window-size={width},{height}",
                        f"--screenshot={target}", source.as_uri() + "#ratio=" + ratio], check=True)
    if not target.is_file() or not target.stat().st_size:
        raise RuntimeError("Browser exited without a screenshot")
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input")
    parser.add_argument("output")
    parser.add_argument("ratio", choices=RATIOS)
    args = parser.parse_args()
    try:
        print(f"Saved screenshot to {capture(args.input, args.output, args.ratio)}")
    except (OSError, ValueError, subprocess.SubprocessError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
