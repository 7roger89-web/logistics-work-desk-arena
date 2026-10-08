#!/usr/bin/env python3
"""Issue #190 — measure the Owner reference PNG by pixel segmentation (no OCR).

The reference is a flat 1536x1466 render, so geometry can be recovered from
colour runs along scan lines: the page background is a light grey, surfaces are
white cards, the attention band is red-tinted, the dark CTA is near-black.

Usage: python scripts/measure_reference_190.py [reference.png] [--json out.json]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image

BG = (238, 242, 247)          # page grey (approx)
TOL = 10


def cls(px):
    r, g, b = px[:3]
    if abs(r - BG[0]) <= TOL and abs(g - BG[1]) <= TOL and abs(b - BG[2]) <= TOL:
        return 'bg'
    if r > 245 and g > 245 and b > 245:
        return 'white'
    if r > 200 and g < 120 and b < 120:
        return 'red'
    if r < 60 and g < 60 and b < 90:
        return 'dark'
    return 'other'


def runs(seq):
    out = []
    cur, start = seq[0], 0
    for i, v in enumerate(seq[1:], 1):
        if v != cur:
            out.append((cur, start, i - 1))
            cur, start = v, i
    out.append((cur, start, len(seq) - 1))
    return out


def main():
    path = Path(sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'evidence/190/reference-original.png')
    im = Image.open(path).convert('RGB')
    w, h = im.size
    px = im.load()
    out = {'image': str(path), 'size': [w, h], 'probes': {}}

    def row(y):
        return [cls(px[x, y]) for x in range(w)]

    def col(x):
        return [cls(px[x, y]) for y in range(h)]

    def significant(rs, min_len=6):
        return [(c, a, b) for (c, a, b) in rs if b - a + 1 >= min_len and c != 'other']

    # vertical structure along a column inside the left map card
    for x in (60, 300, 700, 1200, 1500):
        out['probes'][f'col_x{x}'] = significant(runs(col(x)), 4)
    # horizontal structure along rows of interest
    for y in (40, 150, 300, 560, 900, 940, 1100, 1440, 1455):
        out['probes'][f'row_y{y}'] = significant(runs(row(y)), 4)

    # precise edges: map card vs panel card border along y=560
    y = 560
    transitions = []
    prev = px[0, y]
    for x in range(1, w):
        cur = px[x, y]
        if sum(abs(a - b) for a, b in zip(cur, prev)) > 60:
            transitions.append((x, prev, cur))
        prev = cur
    out['probes']['row560_strong_transitions'] = [
        {'x': t[0], 'from': list(t[1]), 'to': list(t[2])} for t in transitions][:40]

    # vertical strong transitions along x=1200 (inside right panel)
    x = 1200
    transitions = []
    prev = px[x, 0]
    for y in range(1, h):
        cur = px[x, y]
        if sum(abs(a - b) for a, b in zip(cur, prev)) > 60:
            transitions.append((y, prev, cur))
        prev = cur
    out['probes']['col1200_strong_transitions'] = [
        {'y': t[0], 'from': list(t[1]), 'to': list(t[2])} for t in transitions][:60]

    # cards row: white runs along y=1000
    out['probes']['cards_row_y1000'] = [(c, a, b) for (c, a, b) in runs(row(1000)) if c == 'white' and b - a > 40]
    # card vertical extent along x=100 below y=930
    out['probes']['card_col_x100'] = [(c, a, b) for (c, a, b) in runs(col(100)) if a > 900 and b - a > 4]

    print(json.dumps(out, indent=1))
    if '--json' in sys.argv:
        Path(sys.argv[sys.argv.index('--json') + 1]).write_text(json.dumps(out, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
