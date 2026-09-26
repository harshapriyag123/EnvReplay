# EnvReplay — baseline milestone

A small Python standard-library service and an executable replay for a production-only path mismatch. This is the **unrepaired baseline**, deliberately kept failing for investigation in IBM Bob IDE.

## Setup and replay

Requires Python 3.10 or newer. From this directory:

```sh
python3 replay.py --profile ci
python3 replay.py --profile deployment
python3 -m unittest -v
```

The CI profile requests `/api/health`. The deployment profile models an ingress that exposes the service under `/service`, requesting `/service/api/health`. The application currently handles only the root path. The replay starts a real local HTTP server on an ephemeral port, sends an HTTP request, prints its response, and returns a failure status when the endpoint does not respond as expected. No external services or credentials are used.

## File map

- `app.py`: deliberately incomplete service to investigate and repair.
- `config/ci.json`, `config/deployment.json`: sanitized environment inputs.
- `replay.py`: deterministic HTTP replay and exit status.
- `test_regression.py`: CI and deployment assertions; deployment initially fails.
- `evidence/baseline.log`: captured output and exit statuses from the first run.

## Next milestone (perform inside IBM Bob IDE)

Ask Bob Agent mode to inspect this repository and `evidence/baseline.log`, identify the cause, make a focused repair, run both replay profiles and the regression suite, review the diff, and save relevant Bob task session summary screenshots in `bob_sessions/`. After this verified repair, add the evidence report and a two-minute judge demo path. No Bob sessions have been run as part of this baseline.
