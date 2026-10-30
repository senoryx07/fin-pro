"""
Build the site and publish it to the `gh-pages` branch for GitHub Pages.

    python scripts/deploy.py

The branch is replaced by a single fresh commit each time, so the daily
data never accumulates in the repository's history.
"""

import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
DIST = FRONTEND / "dist"
BRANCH = "gh-pages"


def run(*command: str, cwd: Path = ROOT) -> str:
    print("$", " ".join(command))

    result = subprocess.run(
        command,
        cwd=cwd,
        check=True,
        text=True,
        capture_output=True,
        shell=sys.platform == "win32" and command[0] == "npm",
    )

    return result.stdout.strip()


def main() -> None:
    remote = run("git", "remote", "get-url", "origin")

    if not (FRONTEND / "public" / "data" / "index.json").exists():
        sys.exit("No site data. Run: python -m backend.app.update")

    run("npm", "run", "build", cwd=FRONTEND)

    # Stops GitHub Pages from running the output through Jekyll.
    (DIST / ".nojekyll").touch()

    git_dir = DIST / ".git"

    if git_dir.exists():
        shutil.rmtree(git_dir)

    run("git", "init", "-q", "-b", BRANCH, cwd=DIST)
    run("git", "add", "-A", cwd=DIST)
    run(
        "git",
        "-c", "user.name=Fin Pro Deploy",
        "-c", "user.email=deploy@finpro.local",
        "commit", "-q", "-m", "Deploy site",
        cwd=DIST,
    )
    run("git", "push", "--force", remote, f"{BRANCH}:{BRANCH}", cwd=DIST)

    shutil.rmtree(git_dir)

    print(f"Published to the {BRANCH} branch of {remote}")


if __name__ == "__main__":
    main()
