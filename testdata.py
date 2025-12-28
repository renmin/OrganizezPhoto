from __future__ import annotations

import argparse
import random
import shutil
from pathlib import Path
from typing import Iterable, List

DEFAULT_MEDIA_EXTS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".heic",
    ".raw",
    ".nef",
    ".cr2",
    ".mp4",
    ".mov",
    ".hevc",
    ".m4v",
}


def iter_media_files(root: Path, extensions: Iterable[str]) -> Iterable[Path]:
    normalized_exts = {ext.lower() if ext.startswith(".") else f".{ext.lower()}" for ext in extensions}
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() in normalized_exts:
            yield path


def copy_samples(files: List[Path], dest_root: Path, count: int, seed: int | None) -> List[Path]:
    if not files:
        return []
    rng = random.Random(seed)
    sample_size = min(len(files), count)
    chosen = rng.sample(files, sample_size)
    copied: List[Path] = []
    dest_root.mkdir(parents=True, exist_ok=True)
    for src in chosen:
        destination = dest_root / src.name
        # Avoid overwriting existing files by appending a counter if necessary.
        counter = 1
        final_destination = destination
        while final_destination.exists():
            final_destination = destination.with_name(f"{destination.stem}_{counter}{destination.suffix}")
            counter += 1
        shutil.copy2(src, final_destination)
        copied.append(final_destination)
    return copied


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Randomly copy media files into a test source folder for QA runs.",
    )
    parser.add_argument("seed_dir", type=Path, help="Source directory containing media to sample from.")
    parser.add_argument(
        "test_dir",
        type=Path,
        nargs="?",
        default=Path("test_source"),
        help="Destination folder for copied media (default: ./test_source).",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=100,
        help="Number of media files to copy (default: 100).",
    )
    parser.add_argument(
        "--extensions",
        type=str,
        nargs="*",
        default=None,
        help="Optional list of file extensions to include (overrides defaults).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Seed for the RNG to get reproducible samples.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.seed_dir.exists() or not args.seed_dir.is_dir():
        raise SystemExit(f"Seed directory '{args.seed_dir}' does not exist or is not a directory.")

    exts = args.extensions if args.extensions else DEFAULT_MEDIA_EXTS
    media_files = list(iter_media_files(args.seed_dir, exts))
    copied = copy_samples(media_files, args.test_dir, args.count, args.seed)

    if not copied:
        print("No media files found matching the provided extensions.")
        return

    print(f"Copied {len(copied)} files to {args.test_dir}:")
    for path in copied:
        print(f" - {path}")


if __name__ == "__main__":
    main()
