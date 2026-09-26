# Deployment path repair — verified evidence

## Symptom and cause

`config/ci.json` exposed `/api/health`, while `config/deployment.json` exposed `/service/api/health`. The original `app.py` matched only the root path. The first deployment replay made a real HTTP request and received 404. See the preserved, unedited `baseline.log` in this folder.

## Focused change

The service now accepts a validated public base path per server instance. `replay.py` supplies the selected profile when starting the server, so CI and production-like requests exercise different actual routes. The repair also prevents a prefixed deployment from silently serving the root route.

## Before and after

| Command | Baseline | Repaired local run |
| --- | --- | --- |
| `python3 replay.py --profile ci` | HTTP 200, exit 0 | HTTP 200, exit 0 |
| `python3 replay.py --profile deployment` | HTTP 404, exit 1 | HTTP 200, exit 0 |
| `python3 -m unittest -v` | 1 failure, exit 1 | 4 passed, exit 0 |
| `python3 demo.py` | Not available | exit 0; plays baseline and reruns live checks |

The new output is captured in `after.log`. The before result was generated **before** the repair and retained verbatim; `demo.py` reads that file rather than inventing the failure.

## Attribution and limits

Codex made and tested this repair at the user's request. IBM Bob was not run for it, and no Bob task summary screenshot exists. This example models a reverse-proxy public prefix by configuring the application; it does not start a real reverse proxy, deploy a public app, or reproduce a live cloud incident. The demo shows an illustrative developer workflow, not measured time savings across a team.
