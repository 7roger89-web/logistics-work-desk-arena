#!/usr/bin/env python3
"""Offline helper for building the same tariff SQLite used by the app.

The canonical parser/indexer lives in core.tariff_asset. This script is only a
CLI wrapper for operators who want to inspect or benchmark a workbook locally;
it deliberately does not maintain a second XLSX mapping.
"""
from __future__ import annotations

import argparse
import json
import lzma
from pathlib import Path

from core.tariff_asset import build_tariff_asset


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build indexed tariff SQLite from a BIỂU THUẾ XLSX."
    )
    parser.add_argument("source", type=Path, help="Source BIỂU THUẾ .xlsx")
    parser.add_argument(
        "--database",
        type=Path,
        default=Path("tariff.db"),
        help="Destination SQLite path.",
    )
    parser.add_argument(
        "--metadata",
        type=Path,
        default=None,
        help="Optional JSON metadata sidecar.",
    )
    args = parser.parse_args()

    source_bytes = args.source.read_bytes()
    built = build_tariff_asset(
        source_bytes,
        source_filename=args.source.name,
    )

    args.database.parent.mkdir(parents=True, exist_ok=True)
    args.database.write_bytes(lzma.decompress(built["payload_lzma"]))
    print(
        f"Built {int(built['metadata']['indexed_rows']):,} indexed rows: "
        f"{args.database}"
    )

    if args.metadata is not None:
        args.metadata.parent.mkdir(parents=True, exist_ok=True)
        args.metadata.write_text(
            json.dumps(
                built["metadata"],
                ensure_ascii=False,
                indent=2,
                default=str,
            )
            + "\n",
            encoding="utf-8",
        )
        print(f"Metadata: {args.metadata}")


if __name__ == "__main__":
    main()
