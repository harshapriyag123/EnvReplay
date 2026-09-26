# EnvReplay — deployment failure replay

A small Python standard-library service and executable replay for a failure that passed in CI but broke behind a deployment base path. The initial failing output is preserved in `evidence/baseline.log`; the tested repair output is in `evidence/after.log`.

## Setup and replay

Requires Python 3.10 or newer. From this directory:

```sh
python3 replay.py --profile ci
python3 replay.py --profile deployment
python3 -m unittest -v
python3 demo.py
```

The CI profile requests `/api/health`. The deployment profile models an ingress that exposes the service under `/service`, requesting `/service/api/health`. Before the repair, the application handled only the root path. It now configures each server instance with the selected base path. The replay starts a real local HTTP server on an ephemeral port, sends an HTTP request, prints its response, and returns a failure status when the endpoint does not respond as expected. No external services or credentials are used.

## Two-minute demo path

1. Show `evidence/baseline.log`: CI returned 200, deployment returned 404, and its regression test failed. This is actual captured output from the baseline commit.
2. Run `python3 demo.py`. It displays the original failure, reruns both profiles and the tests against the current checkout, and exits nonzero if any live check fails.
3. Point to `app.py` and `config/deployment.json` to explain why the server now handles `/service/api/health` without also exposing `/api/health` in the deployment profile.
4. Show `evidence/repair-report.md` for the commands, exit statuses, and scope limits. The GitHub Actions workflow reruns checks on pushes and pull requests.

## Architecture

`config/*.json` selects a public base path → `replay.py` starts a matching `app.py` server instance → a real HTTP request checks the expected path and response → `demo.py` presents the preserved baseline beside new command output. The regression suite also checks that unrelated root paths return 404 and malformed base paths are rejected.

## File map

- `app.py`: configurable HTTP service with base-path validation.
- `config/ci.json`, `config/deployment.json`: sanitized environment inputs.
- `replay.py`: deterministic HTTP replay and exit status.
- `test_regression.py`: CI, deployment, isolation, and configuration assertions.
- `evidence/baseline.log`: captured output and exit statuses from the first run.
- `evidence/after.log`: output from the local repaired run.
- `evidence/repair-report.md`: results, attribution, and limitations.
- `.github/workflows/verify.yml`: CI replay on pushes and pull requests.

## IBM Bob hackathon attribution

The repair in this repository was made by Codex at the user's request. **It is not evidence of Bob IDE usage.** For a Bob-centered submission, use Bob IDE with this repository on a real follow-up engineering task, such as adding a second deployment failure, having Bob investigate and implement it, and preserving Bob's actual task session summary screenshots in `bob_sessions/`. Do not claim a Bob run or submit substitute screenshots. Never commit an API key or `envreplay.json`.
