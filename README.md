# EnvReplay — Bob-driven deployment repair

EnvReplay gives IBM Bob a reproducible deployment-only failure, then independently checks whether Bob's code change actually repairs it. The sample incident passed in CI but failed behind a deployment base path. The historical Codex-authored fix on `main` is a reference result, **not Bob work**. A Bob run starts from the original failing commit in an isolated Git worktree and produces its own patch and verification report.

## Bob-centered workflow

1. `bob_workflow.py prepare` checks out the original failure and makes real HTTP requests under both configurations. It requires CI to pass and deployment to fail.
2. `bob_workflow.py run` hands the repository paths and actual failure output to **IBM Bob Shell in Agent mode**. Bob investigates, changes the isolated code, runs checks, and reviews its changes. The runner uses a Bobcoin cap and disables external MCP servers.
3. The runner independently repeats both HTTP replays and the regression suite. It only reports `PASS` if Bob returned success, changed files, and all checks now pass. It saves `report.json`, `report.md`, and `bob.diff` for review. It does not push or merge Bob's patch automatically.

This is an **executable integration with Bob Shell**. [Bob repair experiment #6](https://github.com/harshapriyag123/EnvReplay/actions/runs/36223374110) ran the official IBM Bob Shell and independently verified a real repair. Its sanitized [report](evidence/bob-run-6/report.md), [original failing output](evidence/bob-run-6/before.json), and [Bob-generated patch](evidence/bob-run-6/bob.diff) are checked in for review. The hackathon guide separately requires real Bob IDE task-session summary screenshots; this Shell report cannot replace them.

## Incident Room interface

The judge-facing [live Incident Room](https://harshapriyag123.github.io/EnvReplay/) is a responsive, static evidence viewer. It loads sanitized copies of the real configuration files, before/after run report, and Bob patch from `docs/data/`. The four stages are **Symptom → Replay → Bob repair → Verification**. Replay and patch tabs show the actual captured outputs and diff; the evidence section links to the raw files. The page clearly labels the run as archived. It does not execute Python or Bob in a browser.

Run it locally with Python only:

```sh
python3 site/build.py --check
python3 -m http.server 8000 --directory docs
```

Open `http://localhost:8000/`. If the source evidence changes, run `python3 site/build.py` and commit the updated `docs/data/` copies; CI rejects stale copies. No frontend package install, server API, or key is needed.

**Public hosting:** GitHub Pages publishes `docs/` from `main` at https://harshapriyag123.github.io/EnvReplay/. [The Pages deployment succeeded](https://github.com/harshapriyag123/EnvReplay/actions/runs/36224551935). The page contains public-safe evidence only; it does not require Bob credentials.

## Setup and replay

Requires Python 3.10 or newer. From this directory:

```sh
python3 replay.py --profile ci
python3 replay.py --profile deployment
python3 -m unittest -v
python3 demo.py
python3 bob_workflow.py prepare
```

The CI profile requests `/api/health`. The deployment profile models an ingress that exposes the service under `/service`, requesting `/service/api/health`. Before the repair, the application handled only the root path. It now configures each server instance with the selected base path. The replay starts a real local HTTP server on an ephemeral port, sends an HTTP request, prints its response, and returns a failure status when the endpoint does not respond as expected. No external services or credentials are used.

### Run Bob Shell locally

Install [Bob Shell from IBM](https://bob.ibm.com/docs/shell/getting-started/install-and-setup) and review/accept its license in your own session. Export an **Inference** API key as `BOB_API_KEY` in your environment, without committing the value or its downloaded JSON file. Then, from the project root:

```sh
python3 bob_workflow.py run --max-cost 1.0 --max-turns 12
```

The result is in the ignored `bob_runs/latest/` directory. Bob Shell's `bob run` mode pre-approves tool calls; review this repository and the generated patch before using it anywhere else. The API key is passed only as an environment variable, never as a CLI argument or a file in this repository. The runner does not capture Bob's raw transcript or print the key. IBM documents `--mode agent`, JSON output, cost and turn caps, and a workspace argument for this use case.

### Run it from a phone with GitHub Actions

In this repository's **Settings → Secrets and variables → Actions**, create a *repository secret* named `BOB_API_KEY` containing the Inference key. Prefer copying only the value of `apikey` from IBM's downloaded JSON file. If the entire downloaded JSON was pasted into the secret, the runner also extracts its `apikey` field locally before calling Bob Shell; neither format is printed or saved. Do not create a regular variable or upload `envreplay.json`. In the **Actions** tab, select **Bob repair experiment → Run workflow**. Review IBM's [Bob Shell installation and license guidance](https://bob.ibm.com/docs/shell/getting-started/install-and-setup) and check the explicit license-acceptance box only if you accept it. The workflow checks that choice before passing `--accept-license` to Bob. It installs Bob Shell on a temporary Linux runner, invokes the bounded experiment, and uploads an `envreplay-bob-evidence` artifact containing the report and patch when available. It does not alter `main` or expose the key in the report. If Bob reports an invalid or expired key even with the correct secret format, generate a new Inference key in IBM Bob and replace the repository secret without sharing the key in chat.

## Two-minute demo path

1. Open the Incident Room. At **Symptom**, compare the two base paths and the recorded HTTP 200/404 responses.
2. At **Replay**, show `python3 replay.py --profile deployment` exiting 1 before Bob. Switch to **After Bob** and show the same command exiting 0.
3. At **Bob repair**, open the actual task ID and source patch. Explain that run #6 began from the failing commit in an isolated worktree, while the prior reference repair on `main` was authored by Codex.
4. At **Verification**, show CI 0→0, deployment 1→0, and regression 1→0. Expand the exact commands and outputs, then follow the source links to the real report. Show the required Bob IDE task-session summary screenshots separately once captured.

For a live terminal demonstration, run `python3 demo.py` on the repaired `main` checkout. This executes the current replay and regression commands; it is separate from Bob's archived run.

## Architecture

`config/*.json` selects a public base path → `replay.py` starts a matching `app.py` server instance → a real HTTP request checks the expected path and response → `demo.py` presents the preserved baseline beside new command output. The regression suite also checks that unrelated root paths return 404 and malformed base paths are rejected.

The Bob runner checks out the failing Git revision in a detached worktree, probes it, invokes `bob run` against that worktree, probes again, and exports a report and patch. The main checkout stays clean.

The Incident Room is plain HTML, CSS, and JavaScript in `docs/`. `site/build.py` copies only the five allowlisted public evidence and configuration files to `docs/data/`. The browser fetches these files and refuses to present the success story if the report, patch, baseline, or expected HTTP outcomes disagree. GitHub Pages can serve `docs/` directly; no Bob credentials are present in the published files.

## File map

- `app.py`: configurable HTTP service with base-path validation.
- `config/ci.json`, `config/deployment.json`: sanitized environment inputs.
- `replay.py`: deterministic HTTP replay and exit status.
- `test_regression.py`: CI, deployment, isolation, and configuration assertions.
- `evidence/baseline.log`: captured output and exit statuses from the first run.
- `evidence/after.log`: output from the local repaired run.
- `evidence/repair-report.md`: results, attribution, and limitations.
- `evidence/bob-run-6/`: sanitized real Bob Shell report, before/after results, and the generated patch.
- `docs/`: responsive Incident Room and generated public evidence copies for GitHub Pages.
- `site/build.py`: evidence synchronization and drift check.
- `.github/workflows/verify.yml`: CI replay on pushes and pull requests.
- `bob_workflow.py`: isolated Bob Shell execution and independent verification.
- `.github/workflows/bob-repair.yml`: manually triggered experiment with the repository secret.

## IBM Bob hackathon attribution

The reference repair on `main` was made by Codex at the user's request. **It is not evidence of Bob IDE usage.** IBM Bob Shell independently repaired the original failure in the isolated [successful run #6](https://github.com/harshapriyag123/EnvReplay/actions/runs/36223374110). Its patch was preserved, not automatically merged into `main`. Before submitting, capture an actual Bob IDE task-session summary in `bob_sessions/` as required by the hackathon guide. Do not claim a Bob Shell task was an IDE session or submit substitute screenshots. Never commit an API key or `envreplay.json`.
