"""T0 visual-source guard for the Owner's approved Journey-derived app typography.

This is a SOURCE contract, not a visual or rendered-browser certification.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "component/src/index.css").read_text(encoding="utf-8")
SHELL = (ROOT / "component/src/shell.css").read_text(encoding="utf-8")


def test_existing_app_and_journey_use_same_vietnamese_font():
    assert "--font-sans: 'Be Vietnam Pro'" in INDEX
    assert re.search(r"\.journey-demo\s*\{\s*font-family:\s*'Be Vietnam Pro'", INDEX)
    assert 'font-family: "Be Vietnam Pro"' in SHELL
    assert "--font-mono: 'IBM Plex Mono'" in INDEX


def test_real_shadow_shell_and_donor_canvas_share_baseline_palette():
    assert re.search(r"body\s*\{[^}]*background:\s*#edf1f5\s*;[^}]*color:\s*#10263c", INDEX, re.S)
    assert re.search(r"\.logi-shell\s*\{[^}]*background:\s*#edf1f5\s*;[^}]*color:\s*#10263c", SHELL, re.S)
