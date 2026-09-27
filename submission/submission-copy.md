# Submission form copy

## Title

EnvReplay

## Short description

CI passes, deployment fails. EnvReplay reproduces a real configuration-specific HTTP 404, gives IBM Bob the failing evidence, and independently checks its repair.

## Problem and solution statement (under 500 words)

A passing CI run can hide a deployment failure when the deployed application uses a different base path. In EnvReplay's sample Python service, CI requests `/api/health` and receives HTTP 200. The deployment profile adds `/service` and requests `/service/api/health`. On the original revision, the server does not honor that prefix and responds with HTTP 404.

EnvReplay makes this gap reproducible before anyone edits application code. Its replay command starts the service locally, sends a real HTTP request using either sanitized configuration, prints the response and exits nonzero when the health check fails. A regression test catches the deployment failure. The repair workflow checks out the original failing commit in an isolated worktree, collects baseline outputs, supplies them to IBM Bob, then reruns both replays and the regression suite independently. It requires changed files and passing exit codes before reporting success. The resulting patch and JSON report remain reviewable.

In the preserved Bob Shell run #6, CI stayed green (exit 0 to 0), deployment changed from HTTP 404 and exit 1 to HTTP 200 and exit 0, and regression changed from exit 1 to 0. The public Incident Room lets a judge inspect the configuration difference, actual commands and outputs, Bob's patch, and source evidence. The current site presents an archived run; visitors can reproduce the checks locally. It does not invoke IBM Bob in the browser.

The sample has one deliberately bounded incident. Teams could adapt the replay and independent gate to other deployment configuration mismatches, but this prototype does not claim to handle them.

## IBM Bob usage statement (under 500 words)

IBM Bob Shell ran in Agent mode against an isolated checkout of EnvReplay's original failing revision in GitHub Actions run #6. It received the repository files, two sanitized configurations, actual failing HTTP replay output, and regression failures. The recorded Bob task ID is `0a1c9ea43c93eb037a283ffe760d0825`. Bob changed `app.py` so the health route incorporates the configured base path and changed `replay.py` to pass that base path to the server. After Bob exited, `bob_workflow.py` independently ran CI, deployment, and regression checks in Bob's worktree. It saved the full results and Bob-generated diff under `evidence/bob-run-6/`.

The reference repair on the repository's `main` branch was authored earlier by Codex. Bob independently solved the same failure in an isolated worktree; its patch was not merged into `main`. The Incident Room uses only preserved sanitized evidence and does not represent an interactive Bob IDE session.

The hackathon separately requires IBM Bob IDE as a core component and genuine task-session summary screenshots. Do not submit this statement as proof of IDE use unless relevant IDE work has actually been performed and its screenshots committed to `bob_sessions/`. Add a concise account of that IDE task here after it happens, including the task performed, files changed, checks run, and screenshot filenames. Do not attribute earlier Codex changes or Shell-only activity to the IDE.

## URLs

- Repository: https://github.com/harshapriyag123/EnvReplay
- Application: https://harshapriyag123.github.io/EnvReplay/
- Bob Shell run #6: https://github.com/harshapriyag123/EnvReplay/actions/runs/36223374110
- Report: https://github.com/harshapriyag123/EnvReplay/blob/main/evidence/bob-run-6/report.md

## Suggested tags

IBM Bob, developer tools, debugging, deployment, testing, Python, GitHub Pages
