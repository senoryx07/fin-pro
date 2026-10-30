"""
Nightly job: refresh all data from NSE, then publish the site.

    python scripts/daily_update.py

Run by the "Fin Pro Daily Update" Windows scheduled task (see
scripts/install_schedule.ps1). Output goes to logs/daily-YYYY-MM-DD.log;
the last 30 logs are kept.
"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOGS = ROOT / "logs"
KEEP_LOGS = 30


def run(command: list[str], log) -> int:
    log.write(f"\n$ {' '.join(command)}\n")
    log.flush()

    return subprocess.run(
        command,
        cwd=ROOT,
        stdout=log,
        stderr=subprocess.STDOUT,
    ).returncode


def main() -> int:
    LOGS.mkdir(exist_ok=True)

    started = datetime.now()
    path = LOGS / f"daily-{started:%Y-%m-%d}.log"

    with path.open("a", encoding="utf-8") as log:
        log.write(f"=== Fin Pro daily update, {started:%Y-%m-%d %H:%M} ===\n")

        status = run([sys.executable, "-m", "backend.app.update"], log)

        # Only publish data that refreshed cleanly.
        if status == 0:
            status = run([sys.executable, "scripts/deploy.py"], log)

        log.write(
            f"\n=== {'OK' if status == 0 else f'FAILED ({status})'} "
            f"after {datetime.now() - started} ===\n"
        )

    for old in sorted(LOGS.glob("daily-*.log"))[:-KEEP_LOGS]:
        old.unlink()

    return status


if __name__ == "__main__":
    sys.exit(main())
