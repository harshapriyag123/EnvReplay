"""Replay the repair story from recorded baseline and live commands."""

from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def main():
    baseline = (ROOT / "evidence" / "baseline.log").read_text()
    print("ENVREPLAY | deployment incident", flush=True)
    print("BEFORE | original captured deployment failure", flush=True)
    print("\n".join(baseline.splitlines()[:5]), flush=True)
    commands = [
        [sys.executable, "replay.py", "--profile", "ci"],
        [sys.executable, "replay.py", "--profile", "deployment"],
        [sys.executable, "-m", "unittest", "-v"],
    ]
    failed = False
    for command in commands:
        print(f"\nLIVE | {' '.join(command)}", flush=True)
        result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
        print(result.stdout, end="", flush=True)
        print(result.stderr, end="", flush=True)
        print(f"exit code: {result.returncode}", flush=True)
        failed |= result.returncode != 0
    print("\nRESULT | " + ("FAIL" if failed else "PASS"), flush=True)
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
