"""
scripts/download_weights.py
===========================
Downloads PACE model weights from the GitHub release if they are not
already present locally. Safe to run repeatedly — skips files that exist.

Usage:
    python scripts/download_weights.py          # download if missing
    python scripts/download_weights.py --force  # re-download even if present

Called automatically by the app at startup via pipeline/config.py when
is_pace_model_ready() returns False.
"""

import argparse
import os
import sys
import urllib.request

# ── Release configuration ──────────────────────────────────────────────────────
REPO         = "Spring-ISYS-2026-Alpha-Team/Accessorial_Cost_Detection_Engine"
RELEASE_TAG  = "v1.0-weights"
BASE_URL     = f"https://github.com/{REPO}/releases/download/{RELEASE_TAG}"

MODEL_FILES = {
    "models/pace_transformer_weights.pt": f"{BASE_URL}/pace_transformer_weights.pt",
    "models/artifacts.pkl":               f"{BASE_URL}/artifacts.pkl",
}

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _progress(block_num: int, block_size: int, total_size: int):
    downloaded = block_num * block_size
    if total_size > 0:
        pct = min(downloaded / total_size * 100, 100)
        bar = int(pct / 2)
        sys.stdout.write(
            f"\r  [{'█' * bar}{'░' * (50 - bar)}] {pct:5.1f}%  "
            f"({downloaded / 1024 / 1024:.1f} / {total_size / 1024 / 1024:.1f} MB)"
        )
        sys.stdout.flush()


def download_weights(force: bool = False) -> bool:
    """
    Download missing model weight files from the GitHub release.

    Returns True if all files are present after the attempt, False otherwise.
    """
    all_ok = True

    for rel_path, url in MODEL_FILES.items():
        local_path = os.path.join(REPO_ROOT, rel_path)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)

        if os.path.exists(local_path) and not force:
            size_mb = os.path.getsize(local_path) / 1024 / 1024
            print(f"  ✓ {rel_path} already present ({size_mb:.1f} MB) — skipping")
            continue

        print(f"  ↓ Downloading {rel_path} ...")
        try:
            urllib.request.urlretrieve(url, local_path, reporthook=_progress)
            sys.stdout.write("\n")
            size_mb = os.path.getsize(local_path) / 1024 / 1024
            print(f"    ✓ Saved to {local_path} ({size_mb:.1f} MB)")
        except Exception as e:
            sys.stdout.write("\n")
            print(f"    ✗ Failed: {e}")
            print(f"      URL: {url}")
            print(
                "      Make sure you are connected to the internet and the "
                f"release '{RELEASE_TAG}' exists at:\n"
                f"      https://github.com/{REPO}/releases"
            )
            all_ok = False

    return all_ok


def ensure_weights_ready() -> bool:
    """
    Called at app startup. Downloads weights only if missing.
    Returns True when both weight files are present and ready.
    """
    from pipeline.config import MODEL_WEIGHTS_PATH, MODEL_ARTIFACTS_PATH, is_pace_model_ready
    if is_pace_model_ready():
        return True
    print("PACE model weights not found — downloading from GitHub release...")
    ok = download_weights(force=False)
    if ok:
        print("PACE model weights ready.")
    else:
        print("WARNING: Could not download model weights. Scoring will be unavailable.")
    return ok


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download PACE model weights from GitHub release")
    parser.add_argument(
        "--force", action="store_true",
        help="Re-download even if files already exist locally"
    )
    args = parser.parse_args()

    print(f"PACE Weight Downloader")
    print(f"  Repo:    {REPO}")
    print(f"  Release: {RELEASE_TAG}")
    print(f"  Files:   {', '.join(MODEL_FILES.keys())}")
    print()

    ok = download_weights(force=args.force)
    sys.exit(0 if ok else 1)
