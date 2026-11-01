"""Component must forget old customer data on each server-model rerun."""
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(shutil.which("node") is None, reason="node is required")
def test_customer_component_clears_previous_model_on_rerun():
    result = subprocess.run(
        ["node", str(ROOT / "tests/component/dom_acceptance_g15_tenant_reset.mjs")],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS G1.5 tenant/revocation model rerun" in result.stdout
