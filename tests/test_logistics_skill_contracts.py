"""Focused contract/index validation for LOG-SKILL01."""

from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACK_ROOT = ROOT / "skills" / "logistics"
EXPECTED_IDS = [
    "logistics.business_context",
    "logistics.customer_intake",
    "logistics.payment_scenario",
    "logistics.quote_builder",
    "logistics.sales_enablement",
]
REQUIRED_FRONTMATTER = {
    "id",
    "version",
    "status",
    "purpose",
    "triggers",
    "required_inputs",
    "optional_inputs",
    "output_contract",
    "dependencies",
    "dynamic_data_requirements",
    "authority_boundary",
    "unknown_behavior",
    "provenance",
}


def _frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    if len(parts) != 3 or parts[0].strip():
        raise AssertionError(f"invalid frontmatter delimiters: {path}")
    fields: dict[str, str] = {}
    for line in parts[1].splitlines():
        if not line.strip() or line.startswith(" ") or line.startswith("\t"):
            continue
        key, separator, value = line.partition(":")
        if not separator or not key.strip():
            raise AssertionError(f"invalid frontmatter line {line!r}: {path}")
        fields[key.strip()] = value.strip()
    return fields


class LogisticsSkillContractTests(unittest.TestCase):
    def test_each_skill_has_contract_metadata_and_sections(self) -> None:
        observed = []
        for skill_id in EXPECTED_IDS:
            directory = PACK_ROOT / skill_id.removeprefix("logistics.")
            path = directory / "SKILL.md"
            self.assertTrue(path.is_file(), path)
            metadata = _frontmatter(path)
            observed.append(metadata["id"])
            self.assertTrue(REQUIRED_FRONTMATTER.issubset(metadata), path)
            body = path.read_text(encoding="utf-8")
            self.assertIn("## Purpose", body)
            self.assertIn("## Examples", body)
            self.assertIn("## Provenance", body)
        self.assertEqual(observed, EXPECTED_IDS)

    def test_pack_index_is_small_exact_and_loadable(self) -> None:
        index_path = PACK_ROOT / "skill-pack.json"
        index = json.loads(index_path.read_text(encoding="utf-8"))
        self.assertEqual([item["id"] for item in index["skills"]], EXPECTED_IDS)
        self.assertIsNone(index["loader"])
        self.assertTrue(index["host_neutral"])
        for item in index["skills"]:
            self.assertTrue((PACK_ROOT / item["path"]).is_file(), item)
        self.assertEqual(len(index["authority_invariants"]), 10)

    def test_provenance_records_exact_sources_without_vendoring(self) -> None:
        index = json.loads((PACK_ROOT / "skill-pack.json").read_text(encoding="utf-8"))
        provenance = index["provenance"]
        self.assertEqual(provenance["repository"], "https://github.com/minhnv0807/ai-business-skills")
        self.assertEqual(provenance["commit"], "958bd43b03afbc5afc42dfdb3fb2c087b23309e4")
        self.assertEqual(provenance["version"], "3.7.0")
        self.assertEqual(provenance["license"], "MIT")
        self.assertFalse(provenance["text_reused"])
        referenced = provenance["referenced_skills"]
        self.assertEqual(len(referenced), 6)
        self.assertEqual(
            {item["classification"] for item in referenced},
            {"CONCEPT_ONLY", "TEMPLATE_ADAPTED", "NOT_USED"},
        )
        self.assertFalse((ROOT / "ai-business-skills").exists())


if __name__ == "__main__":
    unittest.main()
