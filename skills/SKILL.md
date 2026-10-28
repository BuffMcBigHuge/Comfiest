---
name: comfiest
description: Run the Comfiest local ComfyUI video production suite through the comfy-* MCP servers — photoreal text-to-image, identity-preserving image edits, TTS and voice cloning, song generation, and short video with generated audio. Covers model/workflow routing, template rules, submission and output collection, provenance-scoped vision, and known traps.
---

# Comfiest — Agent Skill

An open, local-first video production suite for ComfyUI: image, voice, music, and video workflows that
run on open weights through the `comfy-*` MCP servers. Read this file before the first run; treat the
shipped workflows as templates; write everything you create under `work/`.

**Scope.** All workflows are local ComfyUI graphs — no partner/cloud nodes, no API keys, no credits.
The suite targets one or more ComfyUI hosts registered as MCP servers; each server process is bound to
one target for its lifetime.

## What is in the repository

| Path | Role |
| - | - |
| `README.md` | Project overview, quick start, model list, and contribution guide. |
| `COMFY-SETUP.md` | Install ComfyUI, custom nodes, models, and the TensorRT depth engine. |
| `skills/SKILL.md` | This file: rules, routing, operating loop, and findings. |
| `skills/*/SKILL.md` | Family and recipe subskills (MiniMax H3, character replacement, Fish Audio). |
| `MCP-SETUP.md` | MCP transport, installation, client registration, and target setup. |
| `scripts/` | `install_nodes.py`, `download_models.py` for machine setup. |
| `workflows/` | Workflow templates; usage notes live in `skills/`. |
| `work/` | Writable agent workspace (scratch, uploads, outputs, analysis, post, exports, logs). |
| `LICENSE` | MIT license for this repository. |

`workflows/minimaxh3/` and `workflows/fishdrama3/` are workflow-family subdirectories. Their usage
notes live in `skills/minimaxh3/`, `skills/minimaxh3-character-replace/`, and
`skills/fish-audio-drama3/`.
`work/` is the only writable area of the repository.

```text
<repo>/
├── README.md
├── LICENSE
├── COMFY-SETUP.md
├── MCP-SETUP.md
├── scripts/
│   ├── install_nodes.py
│   └── download_models.py
├── skills/
│   ├── SKILL.md                    # this file
│   ├── minimaxh3/SKILL.md
│   ├── minimaxh3-character-replace/SKILL.md
│   └── fish-audio-drama3/SKILL.md
├── workflows/
│   ├── *.json                      # root workflows
│   ├── fishdrama3/                 # TTS variants + base
│   └── minimaxh3/                  # H3 base, UI variants, api/ mirrors
└── work/                           # writable workspace; see Working directory
```

## Resolving paths

All paths in this file are relative to the **repository root** — the parent of the `skills/`
directory that contains this file. Workflow paths passed to `run_workflow` are read by comfy-cli
**on the MCP host**, not on the ComfyUI host, so resolve them to absolute paths there.

- Do not copy a drive letter, mount point, or UNC path from another machine; resolve at runtime.
- Where an example needs an absolute path, it is written as `<repo>/workflows/...` or `<repo>/work/...`.
- The same rule applies to `out_dir` and any local file the MCP reads or writes.

If the repository is shared or mounted, confirm the root once per session (for example by listing the
directory) and reuse that absolute prefix for the session.

## Hard rules

### Workflow JSON is read-only

- Never add, edit, reformat, re-save, rename, or delete a `.json` under `workflows/`, including
  `workflows/minimaxh3/`, `workflows/minimaxh3/api/`, and `workflows/fishdrama3/`. Preserve bytes exactly:
  no line-ending, whitespace, or key-order normalization.
- **Maintained additions:** the two `*-forced` UI files, their two API mirrors, and the three
  `charreplace-*` API workflows are maintained rather than one-off templates. Edit them only on an
  explicit user request.
- **Markdown documentation lives in `skills/`.** Inventory and usage notes belong in this file or in
  the family/recipe subskills (`skills/minimaxh3/`, `skills/minimaxh3-character-replace/`,
  `skills/fish-audio-drama3/`). Do not add Markdown to `workflows/`.
- **Runtime edits are allowed; saving is not.** Change widgets and links in the ComfyUI UI for a run,
  but do not save over a workflow file. For a modified graph, write a copy under `work/scratch/` and
  never copy it back into a workflow directory.
- **Do not point file-writing tools at the workflow tree.** `set_workflow_slot`, `vary_workflow`,
  `fetch_template`, `emit_partner_workflow`, and similar tools create or modify JSON; use
  `work/scratch/` for their output.
- **If a workflow JSON change looks necessary, stop and ask the user.** Documentation corrections are
  normal maintenance; workflow files are not.

### Local-only nodes and models

- Never use a node that requires an API key, cloud account, hosted partner model, or external
  service. This excludes `MiniMaxMusicNode` (the API integration, not the local model),
  `ComfyCloud*`, `Sonilo*`, and partner nodes.
- **Music:** YuE2 (`workflows/text2music-yue2.json`) or MiniMax Music 3
  (`workflows/text2music-minimaxmusic3.json`). **Speech:** Fish Audio Drama 3
  (`workflows/fishdrama3/tts-fishdrama3-base.json` and its variants). Do not substitute Chatterbox, F5, Qwen3-TTS,
  VibeVoice, IndexTTS, or a cloud TTS/music service.
- Never pass `confirm_spend=True` without explicit user approval. The workflows here should never
  reach a spending node in the first place.

### One job at a time per target

The `comfy-*` servers may work in parallel with each other, but never submit concurrent jobs to the
same ComfyUI target. Concurrent image submissions and overlapping heavy jobs have taken endpoints
down. Submit, wait for completion, then submit the next job to that target.

### Run on the registered target

- Use the `comfy-*` MCP server that is registered for the intended target. Do not repoint the MCP at a
  local ComfyUI workspace or a discovered checkout unless the user asks.
- Discover the available servers from the client's tool list. In the reference deployment the names
  follow `comfy-<host>-<port>`, and the targets are documented in `MCP-SETUP.md`.
- **There is no per-call target argument.** Each `comfy-mcp` process is bound to one `COMFYUI_URL` at
  start-up; switching targets means using a different registration/process. In Code Mode, dashed server
  names need bracket notation: `tools["comfy-<host>-<port>"]`.
- A server name is a label; the actual target comes from `COMFYUI_URL` at start-up. Do not infer the
  target from the name alone — confirm `comfy_target` and use the target's `/system_stats`.
- `server_info`'s `hardware` block describes the **MCP host**, not the target host. Confirm
  `comfy_target` before generating; use the target's `/system_stats` for GPU and RAM facts.
- Capacity matters for routing: Drama 3 loads 38.6 GB of experts into system RAM; prefer a target with
  enough RAM and confirm with `/system_stats`. All documented workflows assume a 24 GB-class GPU.

### Vision is limited to your own inputs and outputs

Vision is allowed only on media that belongs to the current agent and the current run.

- **Own output:** a file returned by a `prompt_id` from a `run_workflow`, `run_template`, or
  `generate_image` you submitted, recorded in `work/logs/run-log.md` by this session, and downloaded
  into `work/outputs/<project>/<YYYY-MM-DD>/<prompt_id>/`.
- **Own input:** a file you staged in `work/uploads/<project>/`, or a user-supplied file in
  `work/inbox/<project>/` provided for this project. `inbox/` is read-only; copy to `uploads/` if you
  need to modify it. A user-supplied file is an input only when the user provides it for this project;
  never repurpose another agent's file as your input.

Collecting your own output by `prompt_id` is not browsing the remote `output/` folder; it is the only
permitted remote-output path. Provenance is the submission, not the location.

Never use vision on another agent's files; files discovered by browsing a ComfyUI `output/`, `input/`,
or `temp/` directory; files found through `LoadImage`/`LoadAudio` options, `/history`,
`job(action="queue")`, a glob, or a directory scan; previews, thumbnails, screenshots, contact sheets,
or workflow preview images that are not your own output; or any file in a shared `work/outputs/` tree
that you cannot trace to your own `prompt_id` and run-log entry. Do not pass `inline_images=True`;
collect the local copy.

Technical verification requires a `prompt_id`, a completed job, and non-zero output size; vision is
creative QA, not technical verification. If provenance is uncertain, do not use vision — ask the
user. Local ASR/librosa analysis of audio for timing, words, and vocal presence is allowed.

Provenance is **behavioral, not cryptographic**: the run log is shared, so a committed file proves
intent but not exclusivity. If you need hard isolation, add a session-ID column to the run log or use
separate output roots per agent. Legacy files directly under a date folder without a `prompt_id`
subfolder are not eligible for vision.

Prefer local vision for private or sensitive media; do not send it to a cloud vision provider without
explicit approval.

## Quick start

1. **Confirm the tool and target.** `server_info()` on the registered server; check that
   `comfy_target.host`/`port` is the intended target. If the `comfy-*` tools are not connected, read
   `MCP-SETUP.md`.
2. **Check health.** Query the target's `/system_stats` directly; keep one job in flight per target.
3. **Pick a workflow** from the routing table below and read its family section before submitting.
4. **Stage inputs** in `work/uploads/<project>/` with the exact filenames the workflow expects, then
   upload them to every target that may run the job.
5. **Submit** with `wait: false`, then wait explicitly:

   ```js
   const run = await tools["comfy-<host>-<port>"].run_workflow({
     workflow_path: "<repo>/workflows/text2image-krea.json",
     wait: false
   });
   await tools["comfy-<host>-<port>"].job({
     action: "wait",
     prompt_id: run.prompt_id,
     timeout_seconds: 600
   });
   ```

6. **Collect** into `work/outputs/<project>/<YYYY-MM-DD>/<prompt_id>/` with `fetch_outputs`; if the
   local job state lags, download the `outputs[0]` URL directly. Keep the remote filename.
7. **Verify and log.** Check non-zero size, append the run to `work/logs/run-log.md`, and only then
   use vision (if needed) on your own file.

## Choose a workflow

| Task | Model | Workflow | Notes |
| - | - | - | - |
| Photoreal text → image | Krea 2 Turbo | `workflows/text2image-krea.json` | 14-step portrait model; no LoRA; 1024×1280 |
| Identity-preserving image edit | Krea 2 Edit | `workflows/image2image-krea-edit.json` | reference image + instruction; edit conditioning |
| Stylized or detailed text → image | Flux.2 Klein 9B | `workflows/text2image-fluxklein.json` | 4-step RES4LYF; no custom LoRAs after sanitization |
| Reference-based Flux edit | Flux.2 Klein 9B | `workflows/image2image-fluxklein.json` | keeps source pose/size; reference latent |
| Song from style + lyrics | YuE2 3B | `workflows/text2music-yue2.json` | full-song model with vocals; 120 s |
| Song from caption + lyrics | MiniMax Music 3 | `workflows/text2music-minimaxmusic3.json` | caption-driven; tiled audio decode |
| Video from text or references | MiniMax H3 | `workflows/minimaxh3/*.json` + `api/*.api.json` | 8 s, audio, 14 P/V/A variants + 3 charreplace workflows |
| Speech or voice clone | Fish Audio Drama 3 | `workflows/fishdrama3/*.json` | 1–2 speaker TTS; four canonical variants |

How to use the table:

1. Resolve the listed repository-relative path against the repository root and pass the resulting absolute path
   as `workflow_path`.
2. For MiniMax H3, prefer the `api/*.api.json` mirror; image and audio workflows are converted
   client-side from the UI files.
3. Stage `LoadImage`/`LoadAudio` inputs in each target's `input/` first.
4. Save outputs under `work/outputs/<project>/<date>/<prompt_id>/`; verify by metadata/file size.
5. Vision is allowed only on your own inputs/outputs.

Routing constraints:

- One job at a time per target. Krea/Flux are light; Music 3 and MiniMax H3 are heavy; Drama 3 is
  heavy on system RAM.
- The workflow JSON is the final authority on node IDs and model filenames. The family sections call
  out known traps: dead branches, decoy LoRA loaders, optional files that are not installed.

## Working directory

All persistent files an agent creates go under **`work/`**. It lives inside the repository, so the
repository stays self-contained and the workflow tree stays untouched. Transient one-off scripts may use a system
temp directory, but anything the user may need belongs in `work/`.

```text
work/
├── README.md          # pointer to this skill
├── inbox/             # assets handed over by the user (read-only for agents)
├── scratch/           # modified workflow/API copies (JSON allowed here)
├── uploads/           # assets staged with the exact remote input/ filename
├── outputs/           # downloaded ComfyUI results
├── analysis/          # ASR/librosa scripts, transcripts, reports
├── post/              # edits, grades, muxes, intermediates
├── exports/           # final deliverables for the user
└── logs/              # run-log.md and prompt/job records
```

| Artifact | Destination (relative to `work/`) |
| - | - |
| User-provided assets | `inbox/<project-slug>/` |
| Asset to upload to ComfyUI | `uploads/<project-slug>/` |
| Modified workflow or API JSON | `scratch/<project-slug>/` |
| Downloaded ComfyUI output | `outputs/<project-slug>/<YYYY-MM-DD>/<prompt_id>/` |
| ASR/librosa scripts and reports | `analysis/<project-slug>/` |
| Edits, grades, muxes, intermediates | `post/<project-slug>/` |
| Final deliverable | `exports/<project-slug>/` |
| Run log, prompt IDs, byte sizes | `logs/run-log.md` |

Rules:

- **If `work/` lacks a subdirectory, create it.** Never create working folders elsewhere in the repository.
- **Unsure where a file belongs?** Put it under `work/<project-slug>/`, never in `workflows/`.
- **Organize by project slug:** `work/<area>/<project-slug>/...`. Use kebab-case and reuse the same
  slug across areas (`inbox/my-song`, `outputs/my-song/...`).
- **`inbox/` is read-only for agents.** Copy assets to `uploads/` or `scratch/`.
- **`uploads/` uses the exact filename the workflow expects.** `upload_file` preserves the local
  filename; stage it correctly once and upload the same set to every target that may run the workflow.
- **`scratch/` is the only place for modified workflow JSON.** Name it `<workflow-stem>__<variant>.json`.
- **`outputs/` preserves the remote filename and adds date + prompt ID:**
  `outputs/<project>/<YYYY-MM-DD>/<prompt_id>/<original-name>`. The `prompt_id` folder is the
  provenance anchor for vision.
- **Record the `prompt_id` before downloading.** Append the run to `logs/run-log.md`, then
  `fetch_outputs` into the matching folder. If the folder and log entry do not exist, the file is not
  yours for vision purposes.
- **Record input provenance** in the run-log Notes: each staged input and its source (user-provided,
  inbox, or generated by this run).
- **`analysis/` holds scripts and reports, not media masters.** `post/` is working space; `exports/`
  is only for files the user will use.
- **`logs/run-log.md` is append-only.** Log every run with the template below; keep prompt IDs and byte
  sizes as the run's proof.

Run-log template:

| Date | Project | Workflow | Server | prompt_id | Status | Output | Bytes | Notes |
| - | - | - | - | - | - | - | - | - |

## Workflows

> **Release status.** Every workflow was sanitized for the public release: non-turbo LoRAs were
> stripped and baked-in prompts were replaced with fox-themed demo prompts. All UI files were
> conversion-validated against a reference target, but the sanitized graphs have **not** been executed
> end-to-end. Statuses below describe the pre-sanitization configuration and are historical; run one
> job of your own before relying on a workflow.

Each section gives the effective stack, the settings that matter, and the traps that have already
cost runs. Node IDs refer to the shipped graphs.

### Krea 2 — photoreal images and identity edits

Krea 2 is the photoreal/character image family. Turbo produces a still from a prompt; Edit re-renders
a supplied subject into a new scene, pose, or camera angle while preserving identity.

| File | Use | Key behavior |
| - | - | - |
| `workflows/text2image-krea.json` | text → image | 1024×1280; 14 steps; cfg 1; euler/simple; no LoRA |
| `workflows/image2image-krea-edit.json` | image → image | same settings + `Krea2EditModelPatch`; reference image required; identity LoRA removed from the public template |

**Stack:** `krea\kroma-v0.3.1-turbo-opd.safetensors` UNET, `qwen3vl_4b_fp8_scaled.safetensors`
text encoder (type `krea2`), `wan\Wan2_1_VAE_bf16.safetensors` VAE.

**Use it when** the deliverable is a photoreal portrait/character image, or you have one master
reference and need wide/medium/close/detail variants that keep the same person. **Don't use it for**
general graphic design, text-heavy images, or video.

**Inputs:** prompt (`Text Multiline #72`), width `#74`, height `#73`, seed `#75`; the edit also needs
`LoadImage #3071`. **Output:** PNG via `SaveImage`, prefix `COMFY_WORKFLOWS/KREA` or `KREA_EDIT`.
**Status:** both verified.

Effective settings and gotchas:

- Both files: **1024×1280 (portrait)**, 14 steps, cfg 1, `euler`/`simple`, denoise 1, seed
  `436220320311816` (`Seed #75` overrides the KSampler widget). The T2I converted prompt has 15 nodes;
  the edit has 19.
- **T2I:** no reference image, **no active LoRA** (all slots in #3065 are empty).
- **Edit:** the identity LoRA `krea\krea2_identity_edit_v1_2.safetensors` was removed for the public
  release; add it in a scratch copy if identity drift is unacceptable. Active custom nodes:
  `Krea2EditModelPatch #3063`, `Krea2EditGroundedEncode #3066`, `ConditioningKrea2Rebalance #3055`
  (ref_boost 1, fit mode).
- The subgraph's inner UNETLoader still names `krea\krea2_turbo_fp8.safetensors`, which is **not
  installed**. The instance value (`kroma`) wins; do not “fix” the inner loader.
- Output size comes from `PrimitiveInt #74` / `#73`, not from the subgraph `EmptyLatentImage` widget.
  Change both primitives together; 768×1344 gives 9:16.
- Prompts must be explicitly photorealistic: “cinematic photograph, 35mm, natural skin texture, no
  illustration, no 3D render.” “Stylized 3D animated” produces a cartoon look.
- Keep the save prefix static. `%date:...%` tokens are passed through literally and `SaveImage` fails
  with `WinError 123`.
- The edit workflow is the preferred way to derive wide/medium/close/low/detail keyframes from one
  master reference; it preserves identity and background better than independent T2I generations.

### Flux.2 Klein 9B — fast, stylized/detailed images

A distilled Flux.2 Klein model run through the RES4LYF 4-step sampler. It offers a more stylized,
detail-oriented alternative to Krea. The public template ships with no custom LoRAs; the original
production graph used four for realism, anatomy, and skin/detail control. The I2I graph injects a reference latent and follows the source image's dimensions.

| File | Use | Key behavior |
| - | - | - |
| `workflows/text2image-fluxklein.json` | text → image | 1024×1280; 4 steps; cfg 1; SharkSampler |
| `workflows/image2image-fluxklein.json` | image → image | source-size output; reference latent; same edit stack |

**Stack:** `flux\flux-2-klein-9b-fp8.safetensors` UNET, `Qwen3-8B-heretic.Q6_K.gguf` via
`CLIPLoaderGGUF`, `flux2-vae.safetensors` VAE. Custom packs: `ComfyUI-GGUF`, `RES4LYF`,
`rgthree-comfy`, `was-node-suite-comfyui`, `comfyui-easy-use`, `comfyui-various`.

**Use it when** you want a faster 4-step image with a different aesthetic, or a reference-driven edit
whose canvas should match the source. **Don't use it for** video or audio.

Both files use the subgraph **Image Edit (Flux.2 Klein 9B)**. In the T2I file the subgraph's
`reference_image1` input is unconnected, so it runs as text-to-image. In the I2I file,
`LoadImage #710` feeds both the reference conditioning and `GetImageSize`.

Inputs:

- T2I: `Text Multiline #640` (prompt), `PrimitiveInt #2491` (width, default **1024**),
  `PrimitiveInt #2490` (height, default **1280**), `easy seed #601` (see the seed warning).
- I2I: `LoadImage #710`, `Text Multiline #640`, `easy seed #601`. Output size comes from the source
  image, not from the width/height nodes.
- Save: `COMFY_WORKFLOWS/KLEIN` (T2I) and `COMFY_WORKFLOWS/KLEIN_EDIT` (I2I).

Active sampler path and traps:

- The graph contains a standard `SamplerCustomAdvanced` branch and a RES4LYF branch. **The active path
  is the RES4LYF branch:** `ClownSampler_Beta #2484` (`fully_implicit/lobatto_iiib_3s`, eta 0.5,
  bongmath false) → `SharkSampler_Beta #2487` (4 steps, cfg 1, `simple` scheduler, `steps_to_run=-1`,
  `denoise=1`, `sampler_mode=standard`) → `VAEDecode #410` → `SaveImage`.
- The standard branch (`RandomNoise #411` → `SamplerCustomAdvanced #409` from `KSamplerSelect #408`,
  `Flux2Scheduler #418`, `CFGGuider #423`) is **not connected to the output**. Changes there do not
  affect the image.
- **Seed warning:** the top-level `easy seed #601` feeds only `RandomNoise #411` on the unused branch.
  The effective seed is the **SharkSampler `seed` widget**: `528424363836102` in T2I and
  `751621384051185` in I2I. Change that value; changing the easy seed alone does nothing.
- The subgraph has two Power Lora Loaders: **#2489** on the active path and **#424** on the dead
  `CFGGuider` branch. Both were emptied for the public release and now pass MODEL/CLIP through. The
  original production graph loaded four realism/anatomy LoRAs in #2489 (and seven different ones in
  the #424 decoy); add your own to #2489 in a scratch copy if needed.
- `SharkOptions_Beta #2486` uses `noise_type_init=brownian`, `s_noise_init=1`, `denoise_alt=1`, and
  `channelwise_cfg=true`.
- T2I: **1024×1280 (portrait)**, 4 steps, cfg 1. Positive prompt from the top-level text node;
  negative prompt empty. Converted prompt has 25 nodes.
- I2I: canvas follows the source dimensions (`GetImageSize` → subgraph width/height). The reference is
  resized to about 1 MP (`ImageScaleToTotalPixels`, nearest-exact) and injected through
  `ReferenceLatent` for positive and negative conditioning. Converted prompt has 29 nodes.
- The reference latent dominates scene geometry: a prompt asking for a new surface may only relight
  the existing one. Do not treat this workflow as segmentation/compositing.
- The subgraph is named “Image Edit” even in the T2I file; that is expected.
- Keep `SaveImage` prefixes static; no `%date:...%` tokens.

### YuE2 3B — full songs from style + lyrics

Generates a complete song (vocals plus backing) from a style description and lyrics. It uses core
`comfy_extras.nodes_yue2` nodes in a subgraph; ABC structural planning is off in the shipped file, so
it generates directly from style + lyrics.

**File:** `workflows/text2music-yue2.json`. **Model:** `yue2_3b_int8_convrot.safetensors`
(checkpoints). **Output:** FLAC, prefix `COMFY_WORKFLOWS/YUE2_T2M`.

**Use it when** you have lyrics and a musical direction and want a sung track. **Don't use it for**
speech/TTS or short stingers. Tracks can end before `max_duration`; verify duration and vocal presence
with ASR/librosa, not the ABC notation.

Inputs and effective settings:

- Subgraph **Text to Music (YuE2)** inputs: `Style`, `Lyrics`, `mode`, `ABC_planning`, `max_duration`,
  `seed`, `ckpt_name`. Top level exposes Style `#36`, Lyrics `#37`, and ABC `#31` as links; `mode`,
  `max_duration`, `seed`, and `ckpt_name` are widget values on the subgraph node.
- Defaults: `mode=full`, **`ABC_planning=false`**, `max_duration=120`, `seed=0` (fixed),
  `ckpt_name=yue2_3b_int8_convrot.safetensors`. Converted prompt uses 16 nodes.
- `ABC_planning` is an explicit boolean. `ComfySwitchNode` feeds an empty ABC string to
  `YuE2GenerateMusic` when it is off, selecting direct generation; the switch is lazy.
- KSampler: 32 steps, cfg 1, `dpm_2`, `sgm_uniform`, denoise 1. `SeedNode` feeds
  `YuE2GenerateABC`, `YuE2GenerateMusic`, and the KSampler with the same seed.
- `max_duration=120` flows to `YuE2GenerateMusic` and `EmptyYuE2LatentAudio`; the internal node widget
  says 360, but the linked value is 120.
- `YuE2GenerateABC` advanced defaults: `max_abc_tokens=8192`, temperature 0.7, top_p 0.9, top_k 30,
  repetition_penalty 1.005, penalty_window 100.
- `YuE2GenerateMusic` advanced defaults: temperature 1, top_p 0.95, top_k 100,
  repetition_penalty 1.2, cfg_scale 1.0.

Findings:

- Yue2 can produce a full vocal track from a style prompt plus lyrics, but **ABC notation is not a
  reliable indicator of vocal presence**: it has shown vocal rests on tracks that contain audible
  vocals. Verify with ASR or ask the user to listen.
- Tracks can end earlier than `max_duration`. Check the actual duration before planning an edit. If a
  track is short, extend it with a bar-aligned loop or crossfade rather than time-stretching the whole
  song.
- `mode` options are `full` and `melody`; use `full` for songs.
- `SaveAudioAdvanced` supports flac, mp3, and opus. Keep the save prefix static.
- For ASR, load audio with librosa at 16 kHz and pass the NumPy array to faster-whisper. Passing the
  FLAC path directly can fail in PyAV with an incompatible `metadata_errors` argument.
- The old `text2audio-*` files are gone; do not recreate them. The workflow is a subgraph, not custom
  nodes.

### MiniMax Music 3 — caption-driven songs

**File:** `workflows/text2music-minimaxmusic3.json`. This is **not** the `MiniMaxMusicNode` API
integration; it runs the local MiniMax Music 3 model with core `comfy_extras.nodes_minimax_music`
nodes.

Subgraph **Text to Music (MiniMax Music 3)** inputs: `caption`, `lyrics`, `max_duration`, `seed`,
`unet_name`, `clip_name`, `vae_name`, `tiled_decode`.

Models:

- Diffusion: `minimax\minimax_music3_dit_fp16.safetensors` (4.58 GB; the workflow default). The int8
  variant (2.33 GB) is documented upstream for low VRAM but is not assumed installed.
- Text encoder: `minimax_music3_text_encoder_pruned_int8_convrot.safetensors` (8.57 GB).
- VAE: `minimax\minimax_music3_dav.safetensors` (206.7 MB).

Defaults and behavior:

- `max_duration=120`; the model supports up to about 300 s. The node's hard maximum is 360.
- 30 steps, cfg 1.7, `euler`, `simple`, denoise 1.
- Seed: the subgraph instance value is `813991159612730`; the internal `SeedNode` is `randomize`. Fix
  the seed to reproduce a song.
- `tiled_decode=true` selects `VAEDecodeAudioTiled` (tile 1536, overlap 64). The switch is lazy, so
  only the selected decoder runs. Tiled decode cuts VRAM; there is a small seam risk. Disable it only
  when VRAM allows and you want maximum quality.
- Save: `COMFY_WORKFLOWS/MINIMAXMUSIC3_T2M`, MP3 V0.
- The `caption` and `lyrics` defaults are an example; replace them for new songs.
- Converted prompt has 12 nodes.

Findings:

- Caption structure: Global Metadata → Vocal Details → Arrangement. Section tags
  `[intro] [verse] [chorus] [bridge] [outro]` are the executable structural instructions; the lyric
  text conveys mood.
- Longer songs take more time and VRAM. Generate with headroom and trim in post.
- This is a local model; it spends no credits and needs no API key.
- A 120 s request has produced about 85 s of audio; duration is a target, not a guarantee. Check the
  real duration before assuming a full two-minute track.

### Fish Audio Drama 3 — TTS and voice cloning

Local TTS with two speaker slots (autogrow to 16 in the UI). The base workflow is
`workflows/fishdrama3/tts-fishdrama3-base.json`; four canonical variants live in `workflows/fishdrama3/` and should be
preferred for normal runs. The base file is for custom rewiring.

**Stack:** `drama3_fp8experts_bf16.safetensors` (38.6 GB of experts in system RAM) plus
`drama3_codec.safetensors`. Node pack: `ComfyUI-Drama3` (`PedroMarinhoDev/ComfyUI-Drama3`, pinned
`8cb3c64379d4988b9693cae9f3436b8fd54b22ad`). Drama 3 is heavy; prefer a target with ample system RAM —
64 GB is tight, 128 GB+ is safer.

**Use it when** you need dialogue, narration, or a consistent character voice. **Don't use it for**
singing; use YuE2 or Music 3. The reference transcript must match the clip word for word.

Variants:

| Use | File | Voice slots | `speakers` | Save prefix |
| - | - | - | - | - |
| Single speaker, no reference | `workflows/fishdrama3/tts-fishdrama3__single-speaker-no-reference.json` | none | `one take per speaker` | `COMFY_WORKFLOWS/FISHDRAMA3_TTS_SOLO_NOREF` |
| Single speaker, clone | `workflows/fishdrama3/tts-fishdrama3__single-speaker-clone.json` | `voice0` | `one take per line` | `COMFY_WORKFLOWS/FISHDRAMA3_TTS_SOLO_CLONE` |
| Dual speaker, clone | `workflows/fishdrama3/tts-fishdrama3__dual-speaker-clone.json` | `voice0` + `voice1` | `one take per line` | `COMFY_WORKFLOWS/FISHDRAMA3_TTS_DUAL_CLONE` |
| Dual speaker, clone + no-reference speaker | `workflows/fishdrama3/tts-fishdrama3__dual-speaker-clone-plus-no-reference.json` | `voice0`; empty `voice1` | `one take per speaker` | `COMFY_WORKFLOWS/FISHDRAMA3_TTS_DUAL_CLONE_NOREF` |

The base file ships two clone chains; the embedded Markdown note describes the no-voice mode. Use the
variants above for normal runs.

Shared graph:

| Node | Role | Default |
| - | - | - |
| `#2 Drama3Loader` | model | `drama3_fp8experts_bf16.safetensors`, experts in RAM, cache 0, no second GPU |
| `#3 Drama3CodecLoader` | codec | `drama3_codec.safetensors` |
| `#4 Drama3Generate` | text, voices, sampling | 2 voice slots; text uses speakers 0 and 1; seed `808537437152901`, randomize; temperature 1.0, top_p 0.9, top_k 0, max_frames 600, split_long_text true, speakers `one take per line` |
| `#5 Drama3Decode` | decode | `shorten_long_pauses=true` |
| `#6 SaveAudio` | output | `COMFY_WORKFLOWS/FISHDRAMA3_TTS`, FLAC |
| `#9 LoadAudio` → `#8 Drama3EncodeVoice` | clone voice 0 | sample clip + transcript |
| `#11 LoadAudio` → `#10 Drama3EncodeVoice` | clone voice 1 | sample clip + transcript |

Voice mapping and transcripts:

- `voices.voice0` is speaker 0 and `voices.voice1` is speaker 1. A leading `<|speaker:N|>` tag in an
  `EncodeVoice` transcript overrides the slot; remove leading speaker tags from reference transcripts.
- The shipped transcripts may be elided with `...`; replace them with the full exact transcript for a
  good clone.
- Sample reference clips may exist in some targets' `input/`. Never rely on them: stage your own clips
  in `work/uploads/` and upload them to every target that may run the configuration.

Configuration matrix (styles of run):

| Use | Clone chains kept | Voice inputs on `#4` | Text tags | Result |
| - | - | - | - | - |
| Single speaker, no reference | none | none | speaker 0 only | Invented voice, different per seed |
| Single speaker, clone | `#9→#8` | `voice0` | speaker 0 only | Cloned voice |
| Dual speaker, clone | `#9→#8` and `#11→#10` | `voice0` + `voice1` | speakers 0 and 1 | Two cloned voices |
| Dual speaker, clone + no-reference speaker | one chain | one slot | speakers 0 and 1 | One cloned, one invented per seed |

Reproducing a mode from the base file:

1. **Single speaker, no reference:** bypass (`Ctrl+B`) or mute (`Ctrl+M`) `#8`, `#9`, `#10`, `#11`;
   leave both voice slots unconnected; tag every line speaker 0; use `one take per speaker` for one
   consistent invented voice. This is the least stable mode: if a take falls silent, requeue with a new
   seed. Use it for background voices or scratch lines, not a recurring character.
2. **Single speaker, clone:** keep `#9 → #8` and connect `#8` to `voices.voice0`; bypass `#10`/`#11`;
   upload the reference clip to every target, set `#9` to that filename, and set `#8`'s transcript to
   the exact words. Use clean single-speaker speech with no music or overlapping voices.
3. **Dual speaker, clone:** keep all four nodes and connect both chains; set both clips and
   transcripts; write alternating speaker-0/1 lines; keep `one take per line` to prevent voice bleed.
   `one take per line, hearing the line before` adds reactions but can bleed; `one take per speaker`
   groups each speaker's lines; `together` is one script with full bleed.
4. **Dual speaker, clone + no-reference speaker:** keep one clone chain, bypass the other, leave its
   slot unconnected; write both speakers' lines; use `one take per speaker` so the invented speaker's
   lines share one take. Lock the seed once the invented voice is acceptable; if it falls silent,
   requeue with a new seed (a short first line helps). To flip which speaker is cloned, move the chain
   to `voice1`.

Shared rules and pitfalls:

- **Do not save the file after re-wiring.** Bypass or mute instead of deleting so the shipped topology
  is easy to restore; close without saving if you must delete.
- `Drama3Generate` uses autogrow `voices` (up to 16). The file ships two. For three or more speakers,
  grow the input in the UI at runtime; do not add a JSON.
- `max_frames=600` is about 28 seconds per text chunk (21.5 frames per second). `split_long_text=true`
  splits long text into about 300-byte chunks.
- Keep `top_k=0` (no cap), `temperature=1.0`, `top_p=0.9`. Lower `top_k` values stall more often.
- `shorten_long_pauses=true` trims pauses longer than 0.75 s, cuts leading silence, and keeps 0.15 s
  after the last sound. Disable it only if you need raw timing.
- Keep the save prefix static. `SaveAudio` auto-increments and writes FLAC; ComfyUI may report the node
  as deprecated in converted prompts, but it converts and runs.
- Keep `experts=in RAM` on 24 GB cards. `in VRAM` needs the whole 38.6 GB file in VRAM or two GPUs.
- Drama3 is heavy: first run loads the file; expect roughly 20–25 ms per frame on a 3090/4090 (real
  time is 46 ms per frame). One job per target.
- Verify with ASR (words and speaker turns) and librosa (duration/silence); do not visually inspect
  audio media.

### MiniMax H3 — video with generated audio and optional references

Generates an 8-second, 9:16 video with its own synchronized audio from a prompt, optionally conditioned
on subject pictures, a reference video, and standalone audio. The family ships 14 pre-wired UI variants
plus API mirrors, all using the same fastvideo model, single turbo LoRA, 3-step sampling, and RIFE
interpolation to 48 fps. Two `*-forced` variants add the forced-audio latent chain for driving the
mouth from a supplied track. Three API-first `charreplace-*` workflows replace the performer in a
source video with a different character.

**Use it when** you need a short performance/b-roll clip, especially with a character reference or a
previous clip for continuity. **Don't use it for** long-form video or silent clips (every variant
carries an audio stream). Plain audio references condition voice and energy, not phonemes; use the
`*-forced` variants or the character-replacement workflows when the supplied track must drive the
mouth.

**Inputs:** prompt, 1–2 pictures, 0–1 video, 0–1 audio, seed; resolution/aspect and length come from
the settings subgraph. **Output:** h264 MP4 with audio, 48 fps, per-variant prefix.

#### Base template

`workflows/minimaxh3/text2video-minimax-base.json` is the 97-node control surface behind the variants. Its default
resolution resolves to the T2V path, but every reference slot and optional branch is present. Use a
`workflows/minimaxh3/` variant for a ready run; use the base only for a slot the variants do not expose.

Subgraphs: `@settings`, `#1` (sampler), `2nd Pass`, `Load Models & Patches`.

| Slot | Node | Default |
| - | - | - |
| prompt | `PrimitiveStringMultiline #22:11` | fox-themed demo prompt |
| picture_1..6 | `LoadImage #284, #285, #286, #287, #324, #289` | `example.png`, bypassed |
| video_1, video_2 | `LoadVideo #293, #295` → `GetVideoComponents` | `example.mp4`, bypassed |
| video_guide | `VHS_LoadVideo #321` | `example.mp4`, 24 fps cap 22, bypassed |
| audio_1..3 | `LoadAudio #290, #291, #292` | `example.wav`, bypassed |
| first frame | `MiniMaxH3AddGuide #272` (`frame_idx=0`) | bypassed |
| last frame | `MiniMaxH3AddGuide #279` (`frame_idx=-1`) | bypassed |
| 2nd-pass upscale | `MinimaxH3LatentUpscaler3D #243` | bypassed; model may be absent |

The optional 2nd-pass branch also references `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors` and
`minimax_h3_video_vae_int8_convrot.safetensors`; both may be absent. The default path does not use
them. Do not enable those branches without installing the files.

#### Shared stack and settings (all variants)

| Item | Value |
| - | - |
| UNET | `minimax\minimax_h3_fastvideo_vsa_datafree_1300step_4step_int8_convrot.safetensors` |
| Text encoder | `qwen3vl_32b_minimax_h3_int8_convrot.safetensors` (type `minimax`) |
| Video VAE | `minimax\minimax_h3_video_vae_fp16.safetensors` |
| Audio VAE | `minimax\minimax_h3_audio_vae_fp32.safetensors` |
| Resolution | `ResolutionSelector`: 9:16, 0.3 MP, multiple 32 (≈416×736) |
| Length | 8 s (192 frames at 24 fps; the `length` node rounds up to a 17-frame grid) |
| Sampling | 3-step manual sigmas `0.9035, 0.6316, 0.3158, 0.0000`, `er_sde`, `beta` scheduler, cfg 1 |
| Sigma shift | video 6, audio 3 (`MiniMaxH3SigmaShift`) |
| Seed | `easy seed` = `557826801843623` |
| References | `ref_image_size=max`; first picture is `ref_image_0` |
| RIFE | `FL_RIFE` `rife47`, multiplier 2 → 48 fps output |
| Output | `VHS_VideoCombine`, h264/mp4, yuv420p, crf 16, with audio |

Active LoRA (identical in every UI variant and API mirror):

| LoRA | Strength |
| - | - |
| `minimax\minimax_h3_fl2v_turbo_4step_v1.0_768p_comfyui_bf16.safetensors` | 0.8 |

The stack is intentionally reduced to the speed/turbo LoRA: no character or style LoRAs ship
with this suite. The `Power Lora Loader #21` keeps one slot; a bypassed `LoraLoaderModelOnly` node
holds the same turbo LoRA for reference. Add your own LoRAs in a scratch copy, never in the shipped
templates. Verify the model and LoRA on each target with `/models/<folder>` and
`/object_info/LoraLoaderModelOnly` before a run.

#### Variants and UI/API differences

The 12 base UI variants keep the full 97-node graph with unused reference branches bypassed; the two
forced-audio files are 78-node derivatives. The 14 family API mirrors are pre-slimmed (39–46 nodes)
with the same models, LoRAs, refs, settings, seed, and save prefix; they contain no
`Fast Groups Bypasser`/`Label` nodes and are the preferred MCP execution files. The three
`charreplace-*` API workflows are separate 56–57 node graphs with the SAM3/mask motion-guide chain.

| Variant | UI file | API file | Refs (P/V/A) | Save prefix | Historical status |
| - | - | - | - | - | - |
| `t2v` | `workflows/minimaxh3/text2video-minimax-t2v.json` | `workflows/minimaxh3/api/text2video-minimax-t2v.api.json` | 0 / 0 / 0 | `MINIMAX_T2V` | verified |
| `1p` | `workflows/minimaxh3/ref2video-minimax-1p.json` | `workflows/minimaxh3/api/ref2video-minimax-1p.api.json` | 1 / 0 / 0 | `MINIMAX_1P` | verified (production) |
| `2p` | `workflows/minimaxh3/ref2video-minimax-2p.json` | `workflows/minimaxh3/api/ref2video-minimax-2p.api.json` | 2 / 0 / 0 | `MINIMAX_2P` | input-verified |
| `1v` | `workflows/minimaxh3/ref2video-minimax-1v.json` | `workflows/minimaxh3/api/ref2video-minimax-1v.api.json` | 0 / 1 / 0 | `MINIMAX_1V` | input-verified |
| `1p1v` | `workflows/minimaxh3/ref2video-minimax-1p1v.json` | `workflows/minimaxh3/api/ref2video-minimax-1p1v.api.json` | 1 / 1 / 0 | `MINIMAX_1P1V` | verified |
| `1p1a` | `workflows/minimaxh3/ref2video-minimax-1p1a.json` | `workflows/minimaxh3/api/ref2video-minimax-1p1a.api.json` | 1 / 0 / 1 | `MINIMAX_1P1A` | verified (production) |
| `1v1a` | `workflows/minimaxh3/ref2video-minimax-1v1a.json` | `workflows/minimaxh3/api/ref2video-minimax-1v1a.api.json` | 0 / 1 / 1 | `MINIMAX_1V1A` | generated |
| `1p1v1a` | `workflows/minimaxh3/ref2video-minimax-1p1v1a.json` | `workflows/minimaxh3/api/ref2video-minimax-1p1v1a.api.json` | 1 / 1 / 1 | `MINIMAX_1P1V1A` | generated |
| `2p1v` | `workflows/minimaxh3/ref2video-minimax-2p1v.json` | `workflows/minimaxh3/api/ref2video-minimax-2p1v.api.json` | 2 / 1 / 0 | `MINIMAX_2P1V` | generated |
| `2p1a` | `workflows/minimaxh3/ref2video-minimax-2p1a.json` | `workflows/minimaxh3/api/ref2video-minimax-2p1a.api.json` | 2 / 0 / 1 | `MINIMAX_2P1A` | generated |
| `2p1v1a` | `workflows/minimaxh3/ref2video-minimax-2p1v1a.json` | `workflows/minimaxh3/api/ref2video-minimax-2p1v1a.api.json` | 2 / 1 / 1 | `MINIMAX_2P1V1A` | generated |
| `1p1a-yue2` | `workflows/minimaxh3/ref2video-minimax-1p1a-yue2.json` | `workflows/minimaxh3/api/ref2video-minimax-1p1a-yue2.api.json` | 1 / 0 / 1 (YuE2 FLAC) | `MINIMAX_1P1A_YUE2` | verified |
| `1a-forced` | `workflows/minimaxh3/ref2video-minimax-1a-forced.json` | `workflows/minimaxh3/api/ref2video-minimax-1a-forced.api.json` | 0 / 0 / 1 (forced) | `MINIMAX_1A_FORCED` | verified (lip-sync) |
| `1p1a-forced` | `workflows/minimaxh3/ref2video-minimax-1p1a-forced.json` | `workflows/minimaxh3/api/ref2video-minimax-1p1a-forced.api.json` | 1 / 0 / 1 (forced) | `MINIMAX_1P1A_FORCED` | verified (lip-sync) |

**Character replacement (API-first):** `charreplace-keepbg` keeps the source background;
`charreplace-charbg` uses the character image's background; `charreplace-refbg` takes a separate
background image. They use SAM3 person segmentation, a depth-guided motion guide
(`DepthAnythingTensorrt`, `depth_anything_v2_vitl-fp16.engine`), forced source audio, and RIFE. The
optional `h3_character_swap_v1.5` LoRA was removed for the public release; add it in a scratch copy for
stronger identity transfer. See `skills/minimaxh3-character-replace/SKILL.md` and the three
`api/ref2video-minimax-charreplace-*.api.json` files. They are not UI/API pairs.

Reference placeholders: every image slot uses `example.png`, every video slot `example.mp4`, and every
audio slot `example.wav`.

Status meanings:

- **verified:** a completed run with output bytes is recorded in the run log. “verified (production)”
  means a real project run used the variant. “verified (lip-sync)” means a forced-audio variant passed
  an audio-match test (≈0.965 mel correlation on a music/vocal segment).
- **input-verified:** conversion and input wiring were checked, but no completed run is recorded.
- **generated:** the variant was built and inspected; neither a run nor input wiring is recorded.
- **template:** the base control surface, not a production run file.
- **unverified:** no completed run is recorded for the current file.

Run one job before production for any `generated` or `unverified` file.

#### MiniMax H3 findings

- **RIFE is mandatory.** Keep `FL_RIFE` and the 48 fps target active on every variant. Output is
  48 fps.
- **Resolution comes from the settings subgraph.** `Resolution Selector` uses the outer `megapixels`
  value, not the loader widgets. `0.3` MP (default) = **416×736** for 9:16; `1.0` MP = **768×1376**
  (multiple-of-32 rounding). For a 768×1344 master, crop 16 px top and bottom.
- **Every variant carries an audio stream**, including `1p` and b-roll. Ignore or mute it in post and
  use the master track.
- **Fix the final switches.** `Final Images` and `Final Audio` must not select `any_01` from the
  bypassed upscale path. Disconnect `any_01` so the active single-pass decoders are selected.
  Otherwise RIFE receives a latent dict and fails with `'dict' object has no attribute 'shape'`.
- **Strip UI-only nodes** from API graphs (`Fast Groups Bypasser`, `Label`).
- **First-frame conditioning:** activate `ImageResizeKJv2`, `GetImageSize`, and `MiniMaxH3AddGuide`
  with the keyframe in `LoadImage`. The API graph then carries a `MiniMaxH3AddGuide` node fed by the
  keyframe and the model latent. This is a much stronger identity/location anchor than reference
  images alone.
- **Reference tags:** the R2V node presents references as `<Picture i>`, `<Video k>`, and `<Audio j>`
  (1-based per type). Use those tags in the prompt to bind instructions to the right reference.
- **`ref_image_size` is a quality/speed switch.** `max` uses the reference pipeline's 2048 px short
  edge and can be several times slower; `match` scales to the generation's pixel area. Use `max` for
  identity-critical shots and `match` for b-roll or iteration.
- **Video-reference carry:** to keep style and lighting continuous, upload a previous clip as
  `video_1` and use `ref_videos.ref_video_0`. Disconnect `ref_video_audios.ref_video_audio_0` so the
  video contributes frames/style, not competing audio. Keep the character keyframe as `picture_1`.
- **Audio reference is not a lip-sync driver.** `ref_audios.ref_audio_N` is standalone reference audio;
  `ref_video_audios.ref_video_audio_N` is the soundtrack of a reference video. Both are encoded as
  reference tokens that condition the model. MiniMax H3 generates its own audio and video latents, so
  the mouth follows the generated audio, not the supplied clip. Replacing the generated audio with an
  external track leaves the mouth synced to the old generated audio. Verify by extracting the clip
  audio and comparing ASR or spectra with the reference.
- **Forced audio latent (working lip-sync method).** Replace the generation's audio latent with the
  target audio before sampling:
  1. `MiniMaxH3ReferenceToVideo` LATENT (joint AV) → `LTXVSeparateAVLatent` → `video_latent`.
  2. `LoadAudio` → `VAEEncodeAudio` with the **audio VAE** → `audio_latent`.
  3. `SolidMask` value `0` (32×32) → `SetLatentNoiseMask` on the audio latent.
  4. `LTXVConcatAVLatent(video_latent, masked_audio_latent)` → the sampler's `latent_image`.

  The zero noise mask freezes the audio latent; the sampler generates video against the real audio.
  The output audio matches the input and the mouth follows it. Keep `MiniMaxH3AddGuide` on the model's
  original AV latent for first-frame conditioning; only the sampler's starting latent is replaced.
  Apply it per performance shot with the exact segment; the concat node trims or zero-pads audio to
  the video length. The `*-forced` variants implement this chain and passed a music/vocal lip-sync
  test. They default to 1.0 MP (768×1376) and 8 s.
- **Fixed seeds:** the `easy seed` node is fixed per shot. Reuse it when comparing variants; vary it
  per shot for different motion.
- **Length is a 24 fps frame count, not seconds.** `length` steps by 17 and the trained range is
  roughly 124–362 frames (~5–15 s). RIFE doubles the result to 48 fps. Generate with headroom and trim
  to the edit timeline; the returned duration can be quantized.
- **Input slots:** the family uses stable filenames for pictures, video, and audio; the Yue variant
  uses its own stable audio name. The variant table lists each variant's refs.

## MCP behavior and findings

### Workflow format

- The MCP accepts both API-format and UI-export JSON, but complex UI exports can fail because
  ComfyUI cannot execute frontend-only helpers. The shipped UI files were conversion-validated against
  a reference target; re-check after a ComfyUI or node-pack upgrade.
- Convert a UI export to API format with
  `comfy run --print-prompt --json --host <host> --port <port>` and parse the `prompt_preview` event.
  This prints a converted prompt; it does not modify the source file.
- Strip `Fast Groups Bypasser (rgthree)` and `Label (rgthree)` before submitting; the target rejects
  them with `missing_node_type`. `MarkdownNote` and `Note` are frontend-only and absent from
  `/object_info`; conversion usually drops them. Conversion does **not** always drop Fast
  Groups/Label — inspect the `prompt_preview` classes before submitting a UI file.
- `Power Lora Loader (rgthree)` is a backend node and is accepted. Its per-slot `lora_N` objects are
  preserved in the converted prompt; do not replace it with a plain `LoraLoaderModelOnly`.
- Subgraph workflows (`definitions.subgraphs`) are supported; the MCP expands them client-side. Do not
  hand-edit `definitions.subgraphs`.
- Prefer the existing API-format files for execution, especially for MiniMax H3. For UI-only
  workflows, convert first and check the `prompt_preview`; if it retains frontend-only nodes, copy the
  workflow to `work/scratch/` and strip them there.

### Submission and scheduling

- Submit with `run_workflow({ workflow_path, wait: false })`, then wait with
  `job({ action: "wait", prompt_id })`.
- **`job(action="wait")` can fail at the tool level while the server job is still running.** Treat
  `/history/<prompt_id>` and `/queue` as authoritative. Poll them directly; a `status_str` of
  `success` in history is the completion signal.
- One active job per target. Parallel work is allowed only across different targets.
- Check `/system_stats` before starting after a crash or restart. Outputs persist across restarts.
- Do not fire a batch of submissions at one target. The queue may accept them, but model loading and
  concurrent GPU work have taken endpoints down.

### Output collection

- Download results into `work/outputs/<project>/<YYYY-MM-DD>/<prompt_id>/` and keep the remote
  filename. Do not leave the only copy on the ComfyUI host.
- Try `fetch_outputs` first. If it returns `download_job_not_found`, the prompt ID was submitted by a
  different machine/agent or the local state was cleared; download the `outputs[0]` URL directly.
- comfy-cli can leave local job state at `queued` after the server reports `completed`; in that case
  `fetch_outputs` may fall back to a local address and fail. Download the `outputs[0]` URL from the
  `job` result directly into the run's `prompt_id` folder and size-check the file.
- Do not pass `inline_images: true`; collect the local copy, verify provenance, then read that copy if
  vision is needed.

### Uploads

- Stage assets in `work/uploads/<project>/` first. `upload_file` preserves the local filename, so use
  the exact stable name you want in the remote `input/` directory.
- It supports images, video, and audio. TTS reference clips must be uploaded to every target that may
  run the configuration.
- Workflow paths are read on the MCP machine, not the ComfyUI host; resolve them to absolute paths
  there.

### Discovery

- `search_models`, `nodes`, `validate_workflow`, and template `local_check` describe the local
  comfy-cli workspace, not the targets.
- Use the target's HTTP endpoints for live checks:
  - `/object_info/<Class>` for node availability and input options.
  - `/models/<folder>` for model files.
  - `/system_stats` for version, package versions, VRAM, and uptime.
- `/object_info` option lists are authoritative; they can reveal files in model paths that `/models`
  does not list. Example: `Qwen3-8B-heretic.Q6_K.gguf` appears in `CLIPLoaderGGUF` options but not
  under `/models/text_encoders`.
- `/object_info/Drama3Generate` shows the autogrow voice slots (max 16) and speaker-mode options.
  `/object_info/LoadAudio` lists the input clips; sample clips differ between targets, so upload your
  own.

### Shared targets and tool scope

A ComfyUI target has no per-agent identity, ownership, or access control. Agents pointed at the same
target share its queue, history, `input/`, `output/`, local `work/outputs`, and comfy-cli job records
for the same OS user. Separate MCP processes do not isolate them.

- `job({ action: "queue" })` merges the target's `/queue` and roughly the last 10 `/history` entries;
  it can show other agents' `prompt_id`s, statuses, and output counts. Use it for your own job and
  queue health, not to enumerate other work.
- `job({ action: "status", prompt_id })` reads `/history/<prompt_id>` and can return another job's
  output metadata if you know its ID.
- `fetch_outputs` is scoped by the local comfy-cli state file, not ownership: it works for a prompt ID
  this machine submitted and returns `download_job_not_found` otherwise. Download the output URL
  directly in that case.
- `/queue`, `/history`, and `/view?filename=...` bypass the MCP entirely. ComfyUI has no built-in
  authentication; rely on network isolation, not on the MCP for access control. `/history/<prompt_id>`
  also includes the prompt graph and input values, so treat prompt text as visible to anyone with
  target access.
- Do not cancel or collect a job without checking its `prompt_id` and provenance.

| Remote-aware tools (follow `COMFYUI_URL`) | Local-only tools |
| - | - |
| `run_workflow`, `run_template`, `generate_image`, `job`, `upload_file`, `fetch_outputs` | `system_stats`, `free_memory`, `launch_comfyui`/`stop_comfyui`/`install_node`, `download_model`, `search_models`, `nodes`, `validate_workflow`, template `local_check` |

## Local tooling and post-production

Tooling lessons that apply to any host:

- Use a real ffmpeg build for metadata, concat, audio muxing, and drawtext. The MCP venv's
  `imageio-ffmpeg` binary is a reliable fallback when the system has none; do not assume a specific
  install path.
- Windows drawtext: `font='Arial'` works. A `fontfile` path needs correct escaping; the wrong form
  fails with “No option name near …”.
- Run Python analysis scripts from a clean directory. A stray `inspect.py` (or similar) in the current
  directory shadows the standard library module and breaks imports.
- Use a dedicated analysis venv with `librosa`, `faster-whisper`, and `Pillow` (titles). Do not
  install analysis dependencies into the MCP venv.
- Remote outputs persist on disk even when the ComfyUI HTTP server is down; job state can still list
  queued/completed jobs.

Post-production:

- Analyze the selected track's tempo/beats before choosing shot lengths. Place cuts on beats or bars.
- Avoid a uniform clip length. Mix short cuts and longer holds; generate varied source durations, then
  trim/punch-in/speed-ramp in post.
- Provide each generated clip the **exact audio segment** for its section when the model accepts audio
  reference, then use the full track in the final mux. Audio reference conditions voice/energy; it
  does not force the output waveform or guarantee lip-sync.
- **Audio-offset alignment preserves the model's own A/V relationship, not an external track.** If the
  model generated its own audio, placing the clip at its source segment start keeps the generated
  mouth aligned to the generated audio. Replacing that audio with a different track breaks phoneme
  sync. Use the forced audio latent or a dedicated lip-sync pass if the final track must drive the
  mouth.
- Use a previous clip as a video reference for later performance shots to reduce lighting and style
  drift. Intercut performance with b-roll for texture.
- Apply one consistent grade, grain, vignette, and fades across all sources; individual clips may
  differ in lighting.
- **Measure loudness before normalizing.** If the track is already near −14 LUFS, apply a small
  negative gain to bring the true peak below −1 dBFS instead of running `loudnorm`, which can pump.
- **Use a transparent PNG for titles with fades.** Render the card with Pillow and overlay it with
  `fade=alpha=1`; this avoids drawtext escaping and gives predictable typography.
- Verify the final by metadata and decode check. The agent may inspect its own outputs for QA, but the
  user watches/listens and judges.

## Verification and provenance

A workflow is technically verified when:

1. `run_workflow` returns a `prompt_id`.
2. `job(action="wait")` (or `/history/<prompt_id>`) reports `completed`/`success` with no error.
3. At least one output URL is returned and the downloaded file has non-zero size.

Vision is creative QA, not technical verification. Use vision only on your own inputs and outputs as
defined in the hard rules. Record the `prompt_id` and local paths before inspecting. If the active
model cannot accept images, use a local vision model or ask the user; do not claim to have inspected a
file you could not open.

Technical completion does not verify lip-sync. If the final audio is an external track, either force
the audio latent and verify the output audio matches the source (ASR/spectra), or check the generated
audio against the intended segment and treat lip-sync as a separate acceptance criterion.

Record results in the run log (`work/logs/run-log.md`) with the `prompt_id`, output path, and bytes.
The run log is local to a deployment and is not shipped with the repository; the statuses in this file
summarize the evidence that travels. Update the status cells in this file when a workflow becomes
verified. Technical verification is not
creative approval; the user judges the result.

Current run-record gaps (portable summary):

- YuE2 has a short test-copy record only; re-run at full length before production.
- In `workflows/fishdrama3/`, only `single-speaker-no-reference` has a completed run; the other three
  variants are conversion-validated only.
- The H3 `1v1a`, `1p1v1a`, `2p1v`, `2p1a`, and `2p1v1a` variants are generated-only.
- Flux Klein T2I/I2I, Krea, Music 3, the two `-forced` H3 variants, and the three `charreplace-*`
  workflows have completed runs recorded in the local run log.

Before production:

- Run one sanitized job per family; conversion is not execution.
- Stage `example.png` / `example.mp4` / `example.wav` on every target that may run the workflow.
- Drama 3 clone modes need the reference clips uploaded to every target and a high-RAM host.
- Charreplace needs the TensorRT depth engine built on the target GPU.
- Re-run YuE2 at the full 120 s length; its earlier record used a short test copy.

## Common issues and fixes

| Symptom | Likely cause | Fix |
| - | - | - |
| `missing_node_type` for `Fast Groups Bypasser (rgthree)`, `Label (rgthree)`, `MarkdownNote`, or `Note` | Frontend-only nodes in an API graph | Strip them in a scratch copy. Never edit the template file. `Power Lora Loader (rgthree)` is a backend node and stays. |
| `'dict' object has no attribute 'shape'` in MiniMax H3 | RIFE received a latent dict because `Final Images`/`Final Audio` selected the bypassed upscale path | Select the active single-pass decoders; disconnect `any_01`. |
| `SaveImage` fails with `WinError 123` | `%date:...%` or another unresolved frontend token in the save prefix | Use a static save prefix. |
| Job state stays `queued` after the server reports `completed` | Local job-state lag | Download the `outputs[0]` URL from the `job` result and size-check it. |
| `fetch_outputs` errors connecting to a local address | Local state missing; tool fell back to a local ComfyUI URL | Use the remote output URL from `job` directly. |
| `fetch_outputs` returns `download_job_not_found` | The `prompt_id` was submitted by another machine/agent, or local state was cleared | Download the output URL directly; only inspect files tied to your own `prompt_id`. |
| A file in `work/outputs` or the target's `output/` looks interesting, but you did not submit its job | It belongs to another agent or an older run | Do not use vision. Only inspect files traceable to your own `prompt_id` + run-log entry. |
| `Qwen3-8B-heretic.Q6_K.gguf` looks missing from `/models/text_encoders` | GGUF files are not listed in that folder | Check `/object_info/CLIPLoaderGGUF`; use `CLIPLoaderGGUF`, not `CLIPLoader`. |
| `server_info` shows a local GPU that is not the target host | `hardware` describes the MCP host; `comfy_target` describes the target | Route on `comfy_target`; use the target's `/system_stats` for the actual host. |
| `system_stats`/`free_memory` reports the wrong GPU | Those tools are not redirected by `COMFYUI_URL`; they describe the local comfy-cli install | Query `http://<target>/system_stats` for the target host. `free_memory` cannot free a remote or another process. |
| `download_model` refuses | `COMFYUI_URL` is set | Install the model on the target host; do not bypass with `COMFY_MCP_REMOTE_SHARED_MODELS` unless storage really is shared. |
| `launch_comfyui` / `stop_comfyui` / `install_node` affects the wrong install | Those tools are local-only | Do not use them for remote targets; manage the target host directly. |
| Same tools appear twice | Two server names point at the same command | Remove the duplicate registration. |

## Maintaining this skill

This file is the repository's operating skill. Keep it portable and current.

- **Stay portable.** No absolute paths, no drive letters, no hostnames or IPs, no personal install
  paths, no dates, no run history. Deployment specifics belong in `MCP-SETUP.md`; run evidence
  belongs in `work/logs/run-log.md`.
- **Update after every run or failure:** status cells, findings, and the common-issues table. Prefer a
  bullet or table row over prose.
- **Document new workflows with maintainer approval.** Read the JSON, inspect the live target
  (`/object_info`, `/models`, `/system_stats`), then document file name, task, model behavior, node
  packs, effective settings, inputs, save prefix, status, and gotchas.
- **Test variants safely.** Change widgets/links in ComfyUI or write a copy under `work/scratch`, run
  it, and record the result. Never create API variants in the workflow directories.
- **Recompute checksums only when a workflow JSON legitimately changes** (an approved maintainer
  edit). Never modify a file to make it match an external record.
- **Keep family notes with their family.** `skills/minimaxh3/SKILL.md` and
  `skills/fish-audio-drama3/SKILL.md` hold family-specific detail; this file holds routing and rules.

## Target requirements

> A machine with nothing installed yet? Follow [`COMFY-SETUP.md`](../COMFY-SETUP.md) first. It covers
> ComfyUI, PyTorch/CUDA, every custom-node pack, every model file, and the TensorRT depth engine.

- ComfyUI 0.42.0 or newer.
- ComfyUI frontend 1.57.1 or newer.
- `comfy-aimdo` >= 0.6.0, `comfy-kitchen` >= 0.2.40, `comfyui-workflow-templates` >= 0.11.96.
- Node packs: `rgthree-comfy`, `ComfyUI-GGUF`, `RES4LYF`, `was-node-suite-comfyui`,
  `comfyui-easy-use`, `comfyui-various`, `ComfyUI-KJNodes`, `ComfyUI-VideoHelperSuite`,
  `ComfyUI-Drama3`, `comfyui-krea2edit`, `ComfyUI-ConditioningKrea2Rebalance`,
  `comfyui-plaguekind-nodes`, `ComfyUI_Fill-Nodes`, `ComfyUI-Spectrum-MiniMax-H3`,
  `ComfyUI-Impact-Pack`, `ComfyUI-SAM3`, `ComfyUI-Depth-Anything-Tensorrt`.
  Optional: `ComfyUI-Frame-Interpolation` (the H3 graphs use Fill-Nodes `FL_RIFE`) and the latent
  upscaler pack.
- Models: see the family sections. Verify each target with `/models/<folder>` and
  `/object_info/<Class>` rather than assuming the reference deployment's inventory.
- Optional bypassed models that may be absent and are **not** on any effective path:
  `minimax_h3_latent_upscaler_3d_bf16`, `minimax_h3_video_vae_int8_convrot`,
  `qwen3vl_32b_minimax_h3_nvfp4_awq`, `krea2_turbo_fp8` (inner loader), and
  `krea2bypass_balanced`/`krea2filterbypass3` (disabled slots).
- RAM/VRAM: all documented workflows assume a 24 GB-class GPU. Drama 3 loads 38.6 GB of experts into
  system RAM; prefer a target with ample RAM and confirm with `/system_stats`.

## Family notes

- `README.md` — quick start, model list, contribution guide.
- `skills/minimaxh3/SKILL.md` — variant matrix and lip-sync guidance.
- `skills/minimaxh3-character-replace/SKILL.md` — character-replacement setup and run examples.
- `skills/fish-audio-drama3/SKILL.md` — TTS variant index and reference requirements.
- `work/README.md` — workspace rules and the pointer to this file.
