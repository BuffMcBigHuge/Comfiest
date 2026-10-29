---
name: fish-audio-drama3
description: Fish Audio Drama 3 text-to-speech and voice-cloning workflows in Comfiest — four variants, speaker modes, transcripts, and reference clips.
---

# Fish Audio Drama 3 — TTS workflow family

Operating rules live in `../SKILL.md`. Reference variants of
`../../workflows/fishdrama3/tts-fishdrama3-base.json`, split into the four supported uses. These are
UI-format templates; comfy-cli converts them client-side on submit. The workflow files live in
`../../workflows/fishdrama3/`.

**Public-release note.** The graphs were sanitized for release: voice references use the shared
`example.wav` placeholder and the dialogue is a fox-themed demo. Prompts and transcripts are
placeholders — replace both consistently with your own clips.

| Use | File | Voice slots | `speakers` | Save prefix |
| - | - | - | - | - |
| Single speaker, no reference | `tts-fishdrama3__single-speaker-no-reference.json` | none | `one take per speaker` | `COMFY_WORKFLOWS/FISHDRAMA3_TTS_SOLO_NOREF` |
| Single speaker, clone | `tts-fishdrama3__single-speaker-clone.json` | `voice0` | `one take per line` | `COMFY_WORKFLOWS/FISHDRAMA3_TTS_SOLO_CLONE` |
| Dual speaker, clone | `tts-fishdrama3__dual-speaker-clone.json` | `voice0` + `voice1` | `one take per line` | `COMFY_WORKFLOWS/FISHDRAMA3_TTS_DUAL_CLONE` |
| Dual speaker, clone + no-reference speaker | `tts-fishdrama3__dual-speaker-clone-plus-no-reference.json` | `voice0`; empty `voice1` | `one take per speaker` | `COMFY_WORKFLOWS/FISHDRAMA3_TTS_DUAL_CLONE_NOREF` |

Notes:

- `single-speaker-no-reference` has no voice inputs; the model invents a voice per seed. Requeue with
  a new seed if the take falls silent.
- `single-speaker-clone` keeps `#9 LoadAudio` → `#8 Drama3EncodeVoice` → `voice0` (default
  `example.wav`). Set the clip and the exact transcript.
- `dual-speaker-clone` keeps both chains (both default to `example.wav`). Set both
  clips and exact transcripts.
- `dual-speaker-clone-plus-no-reference` keeps only the voice-0 chain and leaves `voice1` empty. API
  conversion drops the unconnected slot; the text still tags speaker 1, so it is invented per seed.
- All four were conversion-validated with comfy-cli using `comfy run --print-prompt --json` (no
  prompt was queued during that validation). Converted API node counts: 5, 7, 9, 7 in table order.
  The sanitized prompts have not been executed end-to-end.
- The base model and codec are required on every target. Reference clips are not bundled; stage and
  upload your own to every target before a clone run. Prefer a high-RAM target for Drama3: the experts
  file is 38.6 GB of system RAM.
- These files are templates. Do not edit or re-save a shipped file for a run; copy it to
  `../../work/scratch/` first.

## Key settings and pitfalls

- `Drama3Generate` uses autogrow `voices` (up to 16 slots); the files ship two. Grow the input in the
  UI at runtime for more speakers; do not add a JSON.
- Voice slot mapping: `voices.voice0` is speaker 0, `voices.voice1` is speaker 1. A leading
  `<|speaker:N|>` tag in a reference transcript overrides the slot, so strip leading speaker tags from
  reference transcripts.
- `max_frames=600` is about 28 seconds per text chunk (21.5 frames/second). `split_long_text=true`
  chunks long text at about 300 bytes.
- Keep `top_k=0` (no cap), `temperature=1.0`, and `top_p=0.9`; lower `top_k` values stall more often.
- `shorten_long_pauses=true` trims pauses over 0.75 s, cuts leading silence, and keeps 0.15 s after the
  last sound. Disable it only when you need raw timing.
- Keep `experts=in RAM` on 24 GB cards. `in VRAM` needs the full 38.6 GB file in VRAM or two GPUs.
- Drama 3 is heavy: first run loads the file, and expect roughly 20–25 ms per frame on a 3090/4090
  (real time is 46 ms/frame). One job per target. A 64 GB host is tight; 128 GB+ is safer.
- Verify with ASR (words and speaker turns) and librosa (duration/silence), not visual inspection.
- Leave the `SaveAudio` prefix exactly as shipped; collect the run by `prompt_id` instead of renaming
  the remote output folder.
