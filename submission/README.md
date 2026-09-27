# EnvReplay submission kit

These files are draft assets for the IBM Bob 2.0 Hackathon submission. They are
not evidence of submission. Confirm the final form values and upload the MP4,
slides, and cover image before September 27, 2026, 10:00 AM CDT.

| Required item | Prepared here | Remaining action |
| --- | --- | --- |
| Public repository and application URL | [Repository](https://github.com/harshapriyag123/EnvReplay), [Incident Room](https://harshapriyag123.github.io/EnvReplay/) | Paste URLs into submission form |
| Problem and solution statement, IBM Bob usage statement | [`submission-copy.md`](submission-copy.md) | Review and paste, each under 500 words |
| Three-minute video, including 90 seconds of working demo | [`video-script.md`](video-script.md) | Record actual screen and narration, upload MP4 |
| Slide presentation | [`envreplay-pitch.pptx`](envreplay-pitch.pptx) | Review and upload |
| Cover image | [`cover.png`](cover.png) | Review and upload |
| Bob IDE task-session summary PNGs | Missing | Open project in Bob IDE, perform relevant Agent-mode tasks, capture summary for each task, commit under `bob_sessions/` |
| IBM Bob-assisted code/files | Shell run #6 preserved under [`evidence/bob-run-6/`](../evidence/bob-run-6/) | Describe Shell evidence accurately; add new IDE-authored changes if made |

The official [guide](https://lablab-ibm-bob-2-hackathon-guide.s3.us.cloud-object-storage.appdomain.cloud/index.html#upload-bob-task-session-summary) requires Bob IDE as a core component and PNG task-session consumption summaries from each participant. Bob Shell is optional and its existing run does not fulfill that IDE requirement. Never use an Incident Room screenshot or an Actions screenshot as a Bob IDE summary.

The live site shows preserved, sanitized run evidence; it does not execute Bob or Python in a visitor's browser. The original repair already on `main` was authored by Codex. Bob independently repaired the original failing revision in run #6, and its patch remained isolated.
