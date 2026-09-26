# EnvReplay — Bob-driven deployment repair

EnvReplay gives IBM Bob a reproducible deployment-only failure, then independently checks whether Bob's code change actually repairs it. The sample incident passed in CI but failed behind a deployment base path. The historical Codex-authored fix on `main` is a reference result, **not Bob work**. A Bob run starts from the original failing commit in an isolated Git worktree and produces its own patch and verification report.

## Bob-centered workflow

1. `bob_workflow.py prepare` checks out the original failure and makes real HTTP requests under both configurations. It requires CI to pass and deployment to fail.
2. `bob_workflow.py run` hands the repository paths and actual failure output to **IBM Bob Shell in Agent mode**. Bob investigates, changes the isolated code, runs checks, and reviews its changes. The runner uses a Bobcoin cap and disables external MCP servers.
3. The runner independently repeats both HTTP replays and the regression suite. It only reports `PASS` if Bob returned success, changed files, and all checks now pass. It saves `report.json`, `report.md`, and `bob.diff` for review. It does not push or merge Bob's patch automatically.

This is an **executable integration with Bob Shell**. [Bob repair experiment #6](https://github.com/harshapriyag123/EnvReplay/actions/runs/36223374110) ran the official IBM Bob Shell and independently verified a real repair. Its sanitized [report](evidence/bob-run-6/report.md), [original failing output](evidence/bob-run-6/before.json), and [Bob-generated patch](evidence/bob-run-6/bob.diff) are checked in for review. The hackathon guide separately requires real Bob IDE task-session summary screenshots; this Shell report cannot replace them.

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

1. Open [Bob repair experiment #6](https://github.com/harshapriyag123/EnvReplay/actions/runs/36223374110) and the [verified report](evidence/bob-run-6/report.md): Bob task `0a1c9ea43c93eb037a283ffe760d0825` ran on the isolated original failing commit. CI was 0 before and after; deployment and regression each changed from exit code 1 to 0.
2. Show the actual [baseline HTTP output](evidence/bob-run-6/before.json) and the [Bob-generated change to `app.py` and `replay.py`](evidence/bob-run-6/bob.diff). The missing `/service` prefix caused a 404 under deployment configuration.
3. Run `python3 demo.py` to repeat the live checks on the reference repair currently on `main`. Explain that this main-branch repair was independently authored by Codex; the Bob patch lives in the run artifact and checked-in evidence.
4. Show the required Bob IDE task-session summary screenshots separately once captured. The Shell run is authentic but does not establish an IDE session.

## Architecture

`config/*.json` selects a public base path → `replay.py` starts a matching `app.py` server instance → a real HTTP request checks the expected path and response → `demo.py` presents the preserved baseline beside new command output. The regression suite also checks that unrelated root paths return 404 and malformed base paths are rejected.

The Bob runner checks out the failing Git revision in a detached worktree, probes it, invokes `bob run` against that worktree, probes again, and exports a report and patch. The main checkout stays clean.

## File map

- `app.py`: configurable HTTP service with base-path validation.
- `config/ci.json`, `config/deployment.json`: sanitized environment inputs.
- `replay.py`: deterministic HTTP replay and exit status.
- `test_regression.py`: CI, deployment, isolation, and configuration assertions.
- `evidence/baseline.log`: captured output and exit statuses from the first run.
- `evidence/after.log`: output from the local repaired run.
- `evidence/repair-report.md`: results, attribution, and limitations.
- `evidence/bob-run-6/`: sanitized real Bob Shell report, before/after results, and the generated patch.
- `.github/workflows/verify.yml`: CI replay on pushes and pull requests.
- `bob_workflow.py`: isolated Bob Shell execution and independent verification.
- `.github/workflows/bob-repair.yml`: manually triggered experiment with the repository secret.

## IBM Bob hackathon attribution

The reference repair on `main` was made by Codex at the user's request. **It is not evidence of Bob IDE usage.** IBM Bob Shell independently repaired the original failure in the isolated [successful run #6](https://github.com/harshapriyag123/EnvReplay/actions/runs/36223374110). Its patch was preserved, not automatically merged into `main`. Before submitting, capture an actual Bob IDE task-session summary in `bob_sessions/` as required by the hackathon guide. Do not claim a Bob Shell task was an IDE session or submit substitute screenshots. Never commit an API key or `envreplay.json`.
