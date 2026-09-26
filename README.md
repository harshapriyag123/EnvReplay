# EnvReplay — Bob-driven deployment repair

EnvReplay gives IBM Bob a reproducible deployment-only failure, then independently checks whether Bob's code change actually repairs it. The sample incident passed in CI but failed behind a deployment base path. The historical Codex-authored fix on `main` is a reference result, **not Bob work**. A Bob run starts from the original failing commit in an isolated Git worktree and produces its own patch and verification report.

## Bob-centered workflow

1. `bob_workflow.py prepare` checks out the original failure and makes real HTTP requests under both configurations. It requires CI to pass and deployment to fail.
2. `bob_workflow.py run` hands the repository paths and actual failure output to **IBM Bob Shell in Agent mode**. Bob investigates, changes the isolated code, runs checks, and reviews its changes. The runner uses a Bobcoin cap and disables external MCP servers.
3. The runner independently repeats both HTTP replays and the regression suite. It only reports `PASS` if Bob returned success, changed files, and all checks now pass. It saves `report.json`, `report.md`, and `bob.diff` for review. It does not push or merge Bob's patch automatically.

This is an **executable integration with Bob Shell**. It has not yet been run against a real Bob account in this environment. A command transcript or test stub is not proof of Bob usage. The hackathon guide separately requires real Bob IDE task-session summary screenshots; this Shell report cannot replace them.

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

In this repository's **Settings → Secrets and variables → Actions**, create a *repository secret* named `BOB_API_KEY` containing the Inference key. Do not create a regular variable or upload `envreplay.json`. In the **Actions** tab, select **Bob repair experiment → Run workflow**. Review the [IBM Bob Shell license](https://bob.ibm.com/docs/shell/getting-started/install-and-setup) and check the explicit license-acceptance box only if you accept it. The workflow also prints the license in its runner log before the Bob run. It installs Bob Shell on a temporary Linux runner, invokes the bounded experiment, and uploads an `envreplay-bob-evidence` artifact containing the report and patch when available. It does not alter `main` or expose the key in the report. The runner needs access to IBM's download and inference endpoints, which could not be tested here.

## Two-minute demo path

1. Show `evidence/baseline.log`: CI returned 200, deployment returned 404, and its regression test failed. This is actual captured output from the baseline commit.
2. Run `python3 demo.py`. It displays the original failure, reruns both profiles and the tests against the current checkout, and exits nonzero if any live check fails.
3. Point to `app.py` and `config/deployment.json` to explain why the server now handles `/service/api/health` without also exposing `/api/health` in the deployment profile.
4. Show `evidence/repair-report.md` for the commands, exit statuses, and scope limits. The GitHub Actions workflow reruns checks on pushes and pull requests.

For a real Bob demo, run the **Bob repair experiment**, download its artifact, and show the actual Bob task ID, its independent before/after checks, and the generated `bob.diff`. Explain that it runs from the original failing commit. Only show an actual Bob run after the workflow succeeds; the historical report is not Bob evidence.

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
- `.github/workflows/verify.yml`: CI replay on pushes and pull requests.
- `bob_workflow.py`: isolated Bob Shell execution and independent verification.
- `.github/workflows/bob-repair.yml`: manually triggered experiment with the repository secret.

## IBM Bob hackathon attribution

The reference repair on `main` was made by Codex at the user's request. **It is not evidence of Bob IDE usage.** The Bob workflow is ready to execute but has not run against IBM Bob here. Before submitting, capture an actual Bob IDE task session summary in `bob_sessions/` as required by the hackathon guide. Do not claim a Bob Shell task was an IDE session or submit substitute screenshots. Never commit an API key or `envreplay.json`.
