#!/usr/bin/env python3
"""Create an empty local tariff lookup database for development.

This script contains no reference tariff data. It only creates the schema queried by
core.utils.fast_search_tariff. Populate a local database from an approved data source
outside Git and configure TARIFF_DB_PATH or Streamlit secrets to point to it.
"""
from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize an empty local tariff lookup database.")
    parser.add_argument("--database", default="data/tariff.db", help="Destination SQLite path.")
    args = parser.parse_args()
    destination = Path(args.database)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(destination) as conn:
        conn.execute(
            '''
            CREATE TABLE IF NOT EXISTS tariff_table (
                "Mã HS" TEXT,
                "Mô tả tiếng Việt" TEXT,
                "Mô tả tiếng Anh" TEXT
            )
            '''
        )
    print(f"Initialized empty tariff lookup database at: {destination}")


if __name__ == "__main__":
    main()
