#!/usr/bin/env python3
"""Issue #190 — visual acceptance comparison (no OCR, geometry-aware).

Compares two rendered PNGs of the same viewport (reference vs candidate) and
writes the artifacts the #190 acceptance rule requires:

    side-by-side-<tag>.png   reference | candidate, padded to a common canvas
    overlay-<tag>.png        50/50 alpha blend of both
    diff-<tag>.png           amplified absolute difference (heat map)
    diff-<tag>.json          numeric summary (mean abs diff, changed-pixel %,
                             changed-region bbox, per-band row diffs)

Usage:
    python scripts/compare_journey_visual_190.py <reference.png> <candidate.png> [tag] [outdir]

Deliberately simple Pillow arithmetic; it never reads text out of the images.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageOps, ImageStat

THRESHOLD = 24  # per-channel abs diff above this counts as "visibly changed"


def load(path: Path) -> Image.Image:
    with Image.open(path) as im:
        return im.convert("RGB")


def pad_to(im: Image.Image, size: tuple[int, int], fill=(255, 255, 255)) -> Image.Image:
    if im.size == size:
        return im
    canvas = Image.new("RGB", size, fill)
    canvas.paste(im, (0, 0))
    return canvas


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    ref_path, cand_path = Path(sys.argv[1]), Path(sys.argv[2])
    tag = sys.argv[3] if len(sys.argv) > 3 else "populated"
    outdir = Path(sys.argv[4]) if len(sys.argv) > 4 else ref_path.parent
    outdir.mkdir(parents=True, exist_ok=True)

    ref, cand = load(ref_path), load(cand_path)
    size = (max(ref.width, cand.width), max(ref.height, cand.height))
    ref_p, cand_p = pad_to(ref, size), pad_to(cand, size)

    # side-by-side (left = reference, right = candidate)
    gutter = 12
    sbs = Image.new("RGB", (size[0] * 2 + gutter, size[1]), (24, 32, 44))
    sbs.paste(ref_p, (0, 0))
    sbs.paste(cand_p, (size[0] + gutter, 0))
    sbs.save(outdir / f"side-by-side-{tag}.png")

    # 50/50 overlay
    overlay = Image.blend(ref_p, cand_p, 0.5)
    overlay.save(outdir / f"overlay-{tag}.png")

    # amplified absolute difference
    diff = ImageChops.difference(ref_p, cand_p)
    heat = ImageOps.autocontrast(diff.convert("L")).convert("RGB")
    heat.save(outdir / f"diff-{tag}.png")

    stat = ImageStat.Stat(diff)
    mean = [round(v, 2) for v in stat.mean]
    bbox = diff.convert("L").point(lambda p: 255 if p > THRESHOLD else 0).getbbox()
    mask = diff.convert("L").point(lambda p: 255 if p > THRESHOLD else 0)
    changed_px = mask.histogram()[255]
    total = size[0] * size[1]

    # horizontal band profile: which vertical regions moved
    bands = []
    band_h = 64
    grey = diff.convert("L")
    for y in range(0, size[1], band_h):
        box = (0, y, size[0], min(y + band_h, size[1]))
        m = ImageStat.Stat(grey.crop(box)).mean[0]
        bands.append({"y": y, "mean_abs_diff": round(m, 2)})

    summary = {
        "reference": str(ref_path),
        "candidate": str(cand_path),
        "viewport": list(size),
        "mean_abs_diff_rgb": mean,
        "changed_pixel_pct_threshold": THRESHOLD,
        "changed_pixel_pct": round(100.0 * changed_px / total, 2),
        "changed_region_bbox": list(bbox) if bbox else None,
        "bands": bands,
        "artifacts": {
            "side_by_side": str(outdir / f"side-by-side-{tag}.png"),
            "overlay": str(outdir / f"overlay-{tag}.png"),
            "diff_heat": str(outdir / f"diff-{tag}.png"),
        },
    }
    (outdir / f"diff-{tag}.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
