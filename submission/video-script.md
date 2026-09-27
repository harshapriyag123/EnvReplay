# Three-minute recording guide

Record a real MP4 screen capture with narration. This file is a script, not a video and not proof of IBM Bob IDE use. Keep the final cut at or under 3:00; devote at least 1:30 to showing the working product. Show genuine Bob IDE task-session evidence only after it exists.

| Time | Screen | Narration |
| --- | --- | --- |
| 0:00–0:20 | Incident Room overview | “CI checks `/api/health` and passes. Deployment adds `/service`, and the original service answers its health check with a 404. This is the kind of configuration difference that a green CI badge can miss.” |
| 0:20–0:55 | Symptom and Replay; select Compare | “These are sanitized profiles and preserved command output from the original failing revision. The deployment command returned HTTP 404 and exit 1. The CI profile passed.” |
| 0:55–1:35 | Bob repair tab and real Bob IDE task, if available | “IBM Bob investigated the repository and failing evidence. This isolated Shell task changed `app.py` and `replay.py`; here is its task ID and saved patch. [Show and describe a separate, genuine Bob IDE task and summary if one has been completed.]” |
| 1:35–2:15 | Verification, expanded commands, raw report | “The runner repeated the checks after Bob's Shell task. CI remained exit 0; deployment and regression changed from exit 1 to exit 0. We inspect the actual outputs and diff instead of accepting an agent's success message alone.” |
| 2:15–2:40 | Terminal reproduction on original revision and current checkout, if recording system has terminal | “The same failure can be reproduced from the original commit with `python3 bob_workflow.py prepare`. The current application handles the configured base path.” |
| 2:40–3:00 | Scope and next step | “The public page is an archived evidence viewer. Bob's Shell patch remained isolated; the main branch's earlier repair was authored by Codex. The prototype focuses on one deterministic failure.” |

Before recording, revise the 0:55–1:35 scene for **actual Bob IDE work**. If no IDE task exists, state that truth; do not show an IDE mockup. The official hackathon requires Bob IDE, so a Shell-only recording leaves a submission eligibility gap.
