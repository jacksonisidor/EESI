#!/usr/bin/env python3
"""
Example: run EESI similarity search from the command line.

Usage (from repository root, with .env configured):
  python examples/query_example.py --image path/to/bathroom.jpg
  python examples/query_example.py --crop path/to/toilet.jpg --label toilet
"""

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from PIL import Image

from pipeline.query import query_from_crop, query_from_image


def main():
    parser = argparse.ArgumentParser(description="EESI query pipeline example")
    parser.add_argument("--image", help="Full bathroom image (Path 1)")
    parser.add_argument("--crop", help="Pre-cropped object image (Path 2)")
    parser.add_argument(
        "--label",
        help="Object label for crop mode (e.g. toilet, sink)",
    )
    parser.add_argument("-k", type=int, default=5, help="Top-K matches per object")
    args = parser.parse_args()

    if bool(args.image) == bool(args.crop):
        parser.error("Provide exactly one of --image or --crop")

    if args.crop:
        if not args.label:
            parser.error("--label is required with --crop")
        image = Image.open(args.crop)
        results = query_from_crop(image, args.label, k=args.k)
    else:
        image = Image.open(args.image)
        results = query_from_image(image, k=args.k)

    if results is None:
        print("No results (non-bathroom image or no detections).", file=sys.stderr)
        sys.exit(1)

    # Strip PIL images / base64 for readable CLI output
    def slim(match):
        return {k: v for k, v in match.items() if k not in ("image_data",)}

    if isinstance(results, dict):
        out = {label: [slim(m) for m in matches] for label, matches in results.items()}
    else:
        out = [slim(m) for m in results]

    print(json.dumps(out, indent=2, default=str))


if __name__ == "__main__":
    main()
