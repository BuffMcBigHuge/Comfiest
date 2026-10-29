# Comfiest workspace

This directory is the agent working area inside the repository. The canonical rules, routing, and
findings live in [`../skills/SKILL.md`](../skills/SKILL.md).

Read that first. Everything an agent creates goes here; keep `../workflows/` intact. The only
exception is editing Markdown documentation there when the rules require it.

## Layout

```text
work/
├── inbox/      # assets handed over by the user (read-only for agents)
├── scratch/    # modified workflow/API copies (JSON allowed here)
├── uploads/    # assets staged with the exact remote input/ filename
├── outputs/    # downloaded ComfyUI results
├── analysis/   # ASR/librosa scripts, transcripts, reports
├── post/       # edits, grades, muxes, intermediates
├── exports/    # final deliverables for the user
└── logs/       # run-log.md and prompt/job records
```

## Rules

- This directory is inside the repository. Do not move it outside the repository root.
- Organize by project slug: `work/<area>/<project-slug>/...`. Use kebab-case and keep the same slug
  across areas.
- `inbox/` is read-only. Copy user assets to `uploads/` or `scratch/`; do not overwrite originals.
- `uploads/` filenames must match the workflow's `LoadImage` / `LoadAudio` values exactly.
  `upload_file` preserves the filename.
- `scratch/` is the only place for modified workflow JSON. Name it
  `<workflow-stem>__<variant>.json`, for example `tts-fishdrama3__single-clone.json`. Never copy
  scratch files into the `workflows/` tree.
- `outputs/` preserves the remote filename and adds a date + prompt_id folder:
  `outputs/<project>/<YYYY-MM-DD>/<prompt_id>/<original-name>`. The `prompt_id` is the provenance
  anchor for vision.
- **Do not change workflow save prefixes.** Leave `filename_prefix` on `SaveImage`,
  `VHS_VideoCombine`, `SaveAudio`, and `SaveAudioAdvanced` untouched; identify and collect every run
  by its `prompt_id`. Changing prefixes scatters untraceable files through the shared ComfyUI
  `output/` tree.
- `logs/run-log.md` is append-only. Follow the run-log template in `../skills/SKILL.md`.
- Vision is allowed only on the current run's own inputs/outputs, traceable to its own `prompt_id` and
  run-log entry. Never inspect another agent's files or files discovered in ComfyUI folders. See the
  hard rules in `../skills/SKILL.md`.
- Record the output `prompt_id` and input source in the run-log Notes; that is the audit trail for
  vision.
- `exports/` is only for files the user will use; `post/` is working space.

`work/` is for agents working with ComfyUI: generated outputs, uploads, analysis, post, exports, logs,
and scratch copies. Workflow families live in `../workflows/`. The Drama 3 TTS variants are in
`../workflows/fishdrama3/`, not here.
