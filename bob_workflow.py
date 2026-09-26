"""Replay an incident, ask IBM Bob Shell to repair it, and verify the result.

The baseline runs in a detached Git worktree. Nothing in the caller's checkout
is edited; the result is a report and a reviewable patch in the output folder.
"""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
BASELINE = "847f33f7ad3bc3fadbae125e12789e8e097040f0"
CHECKS = {
    "ci": [sys.executable, "replay.py", "--profile", "ci"],
    "deployment": [sys.executable, "replay.py", "--profile", "deployment"],
    "regression": [sys.executable, "-m", "unittest", "-v"],
}


def command(args, cwd, *, input_text=None):
    return subprocess.run(
        args, cwd=cwd, input=input_text, capture_output=True, text=True, check=False
    )


def checks(workspace):
    results = {}
    for name, args in CHECKS.items():
        result = command(args, workspace)
        results[name] = {
            "command": "python3 " + " ".join(args[1:]),
            "exit_code": result.returncode,
            "output": (result.stdout + result.stderr).strip(),
        }
    return results


def prompt_for(workspace, baseline_results):
    return f"""You are IBM Bob working inside this isolated EnvReplay repository at {workspace}.
Investigate and repair the deployment-only HTTP failure. Read @app.py,
@replay.py, @config/ci.json, @config/deployment.json, and @test_regression.py.
The actual baseline replay outputs follow; these were produced by real HTTP requests:

CI: {baseline_results['ci']['output']}

DEPLOYMENT: {baseline_results['deployment']['output']}

REGRESSION: {baseline_results['regression']['output']}

Trace the code path and explain the root cause. Make a focused application repair;
keep both CI and deployment profiles working. Run both replay commands and the
regression suite, diagnose failures, and review your diff. Do not read any API
key file, print environment secrets, change Git remotes, push, or publish.
Your actual code changes, checks, and final review will be independently
verified by the EnvReplay runner after this session ends.
"""


def redacted_error(value, secret):
    """Keep short diagnostic text while excluding the configured credential."""
    value = value.replace(secret, "[REDACTED]")
    value = re.sub(
        r"(?i)\b(api[-_ ]?key|token|authorization)\s*[:=]\s*\S+",
        r"\1=[REDACTED]",
        value,
    )
    return value.strip()[:1200]


def report_text(report):
    rows = [
        "# EnvReplay: Bob repair verification",
        "",
        f"Bob task ID: `{report['bob_task_id']}`",
        f"Bob executable: `{report['bob_executable']}`",
        f"Bob reported: `{report['bob_status']}`",
        f"Bob Shell exit code: `{report['bob_exit_code']}`",
        f"Independent result: **{report['verdict']}**",
        "Bob error: " + (report["bob_error"] or "none"),
        "",
        "| Check | Before exit | After exit |",
        "| --- | ---: | ---: |",
    ]
    for name in CHECKS:
        rows.append(
            f"| {name} | {report['before'][name]['exit_code']} | "
            f"{report['after'][name]['exit_code']} |"
        )
    rows += [
        "",
        "Changed files: " + (", ".join(report["changed_files"]) or "none"),
        "",
        "This record is generated after a configured executable runs. Verify that it was",
        "the official IBM Bob Shell before presenting it as Bob usage. A success response",
        "alone is insufficient; all independent replay and regression checks must pass.",
        "The patch is in `bob.diff`. Review it before applying it to another branch.",
        "Bob Shell output does not replace the hackathon's required Bob IDE session screenshots.",
    ]
    return "\n".join(rows) + "\n"


def run(args):
    if args.mode == "run":
        if not os.environ.get("BOB_API_KEY"):
            raise RuntimeError("BOB_API_KEY is missing; set it as a private environment secret")
        if not shutil.which(args.bob_bin):
            raise RuntimeError("Bob Shell executable is unavailable; install it from IBM")
    if command(["git", "cat-file", "-e", BASELINE + "^{commit}"], ROOT).returncode:
        raise RuntimeError("Baseline Git commit is missing; fetch repository history")

    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    workspace = Path(tempfile.mkdtemp(prefix="envreplay-bob-"))
    # git worktree add requires an absent path.
    workspace.rmdir()
    added = False
    try:
        add = command(["git", "worktree", "add", "--detach", str(workspace), BASELINE], ROOT)
        if add.returncode:
            raise RuntimeError("Could not prepare baseline worktree: " + add.stderr.strip())
        added = True
        before = checks(workspace)
        if [before[key]["exit_code"] == 0 for key in ("ci", "deployment", "regression")] != [True, False, False]:
            raise RuntimeError("Expected baseline failure was not reproduced; refusing to ask Bob to repair it")
        (output / "before.json").write_text(json.dumps(before, indent=2) + "\n")
        if args.mode == "prepare":
            print("Reproduced baseline: CI passes, deployment and regression fail.")
            print("No Bob session was started. Evidence: " + str(output / "before.json"))
            return 0

        instruction = prompt_for(workspace, before)
        invocation = [
            args.bob_bin, "run", "--mode", "agent", "--format", "json",
            "--max-cost", str(args.max_cost), "--max-turns", str(args.max_turns),
            "--disable-mcp", "--trust",
            "--workspace", str(workspace),
        ]
        if args.accept_license:
            invocation.append("--accept-license")
        bob = command(invocation, workspace, input_text=instruction)
        try:
            response = json.loads(bob.stdout)
        except json.JSONDecodeError:
            response = {}
        bob_error = redacted_error(bob.stderr or (bob.stdout if not response else ""), os.environ["BOB_API_KEY"])
        bob_status = response.get("status", "unavailable")
        task_id = response.get("stats", {}).get("task_id", "unavailable")
        after = checks(workspace)
        changed = command(["git", "status", "--porcelain", "--untracked-files=all"], workspace)
        changed_files = [line[3:] for line in changed.stdout.splitlines()]
        # Include new Bob-created files in the patch without committing or pushing them.
        staged = command(["git", "add", "-N", "."], workspace)
        if staged.returncode:
            raise RuntimeError("Could not stage new files for diff inspection")
        patch = command(["git", "diff", "--binary", "HEAD"], workspace)
        if patch.returncode:
            raise RuntimeError("Could not inspect the Bob worktree diff")
        secret = os.environ["BOB_API_KEY"]
        if any(secret in value for value in (patch.stdout, changed.stdout, json.dumps(after))):
            raise RuntimeError("A result contains the Bob API key; refusing to save it")
        verdict = "PASS" if (
            bob.returncode == 0 and bob_status == "success" and changed_files
            and all(result["exit_code"] == 0 for result in after.values())
        ) else "FAIL"
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "baseline_commit": BASELINE,
            "bob_task_id": task_id,
            "bob_status": bob_status,
            "bob_exit_code": bob.returncode,
            "bob_error": bob_error,
            "bob_executable": shutil.which(args.bob_bin),
            "verdict": verdict,
            "changed_files": changed_files,
            "before": before,
            "after": after,
        }
        (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
        (output / "report.md").write_text(report_text(report))
        (output / "bob.diff").write_text(patch.stdout)
        print(report_text(report))
        print("Evidence directory: " + str(output))
        if bob.returncode and not response:
            print("Bob Shell failed without a JSON result; see the redacted Bob error above.", file=sys.stderr)
        return 0 if verdict == "PASS" else 1
    finally:
        if added:
            command(["git", "worktree", "remove", "--force", str(workspace)], ROOT)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "run"))
    parser.add_argument("--output", default=str(ROOT / "bob_runs" / "latest"))
    parser.add_argument("--bob-bin", default="bob")
    parser.add_argument("--max-cost", type=float, default=1.0)
    parser.add_argument("--max-turns", type=int, default=12)
    parser.add_argument("--accept-license", action="store_true", help="Pass explicit IBM license acceptance to Bob Shell")
    args = parser.parse_args()
    if args.max_cost <= 0 or args.max_turns <= 0:
        parser.error("max-cost and max-turns must be positive")
    try:
        return run(args)
    except RuntimeError as exc:
        print("EnvReplay: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
