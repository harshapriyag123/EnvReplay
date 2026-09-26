"""Copy the public-safe source evidence into the GitHub Pages site.

The source files in config/ and evidence/ remain authoritative. Run with
--check in CI to fail when the published copies are stale.
"""

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs" / "data"
SOURCES = {
    "report.json": ROOT / "evidence" / "bob-run-6" / "report.json",
    "before.json": ROOT / "evidence" / "bob-run-6" / "before.json",
    "bob.diff": ROOT / "evidence" / "bob-run-6" / "bob.diff",
    "ci.json": ROOT / "config" / "ci.json",
    "deployment.json": ROOT / "config" / "deployment.json",
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Check published data matches the sources")
    args = parser.parse_args()
    if not args.check:
        DATA.mkdir(parents=True, exist_ok=True)
    stale = []
    for name, source in SOURCES.items():
        expected = source.read_bytes()
        target = DATA / name
        if args.check:
            if not target.is_file() or target.read_bytes() != expected:
                stale.append(name)
        else:
            target.write_bytes(expected)
    if stale:
        print("Published evidence is stale: " + ", ".join(stale), file=sys.stderr)
        print("Run python3 site/build.py and commit the generated docs/data files.", file=sys.stderr)
        return 1
    print("Published evidence matches repository sources" if args.check else "Copied source evidence into docs/data")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
