"""
Pack or unpack the SQLite database for storage between CI runs.

    python scripts/db_archive.py pack finpro.db finpro.db.gz
    python scripts/db_archive.py unpack finpro.db.gz finpro.db

Packing takes a consistent snapshot with SQLite's backup API and
vacuums it before compressing.
"""

import gzip
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path


def pack(source: Path, target: Path) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        snapshot = Path(tmp) / "snapshot.db"

        src = sqlite3.connect(source)
        dst = sqlite3.connect(snapshot)
        src.backup(dst)
        dst.execute("VACUUM")
        dst.close()
        src.close()

        with snapshot.open("rb") as raw, gzip.open(target, "wb", 9) as out:
            shutil.copyfileobj(raw, out)

    print(f"Packed {source} -> {target} ({target.stat().st_size / 1e6:.1f} MB)")


def unpack(source: Path, target: Path) -> None:
    with gzip.open(source, "rb") as packed, target.open("wb") as out:
        shutil.copyfileobj(packed, out)

    # Fail early on a corrupt download rather than mid-update.
    result = sqlite3.connect(target).execute("PRAGMA quick_check").fetchone()

    if result[0] != "ok":
        sys.exit(f"Database integrity check failed: {result[0]}")

    print(f"Unpacked {source} -> {target} ({target.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    if len(sys.argv) != 4 or sys.argv[1] not in ("pack", "unpack"):
        sys.exit(__doc__)

    action, source, target = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])

    (pack if action == "pack" else unpack)(source, target)
