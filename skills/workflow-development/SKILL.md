---
name: workflow-development
description: How to adapt, validate, run, and promote ComfyUI workflows in Comfiest — scratch copies, API graphs, MCP submission, output collection, and the public-release checklist.
---

# Workflow development and MCP delivery

The umbrella rules live in `../SKILL.md`; transport and client registration live in
[`MCP-SETUP.md`](../../MCP-SETUP.md). This skill is the working loop: take a UI export or an existing
graph, build a scratch API graph, validate it against a live target, submit it through the MCP, collect
the result, and promote it only after it survives.

```text
inspect -> copy to scratch -> build/patch -> validate -> preview -> submit -> poll -> collect -> promote
```

**The shipped workflow tree is read-only.** Every edit happens in `work/scratch/<project>/`. A graph
moves back into `workflows/` only through the promotion checklist at the end of this file.

## 1. Read the target before touching the graph

1. `server_info()` on the registered server. `comfy_target.host`/`port` is the render box; the
   `hardware` block describes the MCP host and may be a different machine.
2. Query the target directly:
   - `GET /system_stats` — ComfyUI version, VRAM, uptime.
   - `GET /object_info` — every installed class and its input schema, including the loader option
     lists that name model files.
   - `GET /models/<folder>` — secondary only; it can return an empty body even when models are
     installed, and it omits some files (GGUF).
3. `job({ action: "queue" })` — the target must be idle before a heavy run. One active job per target.
4. Check version gates: `MiniMaxH3LatentUpscaleWithModel` needs ComfyUI PR #17412+, the perfect loop
   needs core `SaveVideo` (0.43.0+), charreplace needs the TensorRT depth engine, and so on.

`system_stats` and `free_memory` are local-only tools when a remote target is configured. Use the
target's HTTP endpoints for remote health. `download_model` is local-only too; install models on the
render host itself.

## 2. Inspect the source graph

The workflow JSON is the authority, not the guide or the filename.

- **UI format** has `nodes`, `links`, and often `definitions.subgraphs`. Widgets on a subgraph
  *instance* override the same widgets inside the subgraph. Edit the instance, not the inner node.
  This is the MOSS trap and the Krea/Flux trap in the family sections.
- **API format** is a flat object of `"<id>": {class_type, inputs, _meta}`. Links are `[source_id,
  output_slot]`. It is what the MCP executes most reliably.
- Check `mode` on UI nodes: bypassed/muted branches can still contain decoy loaders and dead model
  names. The effective graph is only what the converted prompt contains.
- Treat a model filename in a UI export as a dependency only if it survives into the effective prompt.
  Inner subgraph loaders, bypassed branches, and `properties.models` metadata can name files the
  target never loads.
- Frontend-only nodes (`Fast Groups Bypasser (rgthree)`, `Label (rgthree)`, `Note`, `MarkdownNote`) do
  not exist on the target. Strip them in the scratch copy if conversion leaves them behind.

A compact UI inspector is three loops: count `node["type"]`, print
`id/type/mode/title/widgets_values`, and print each input's `link -> (source_id, source_slot)` via the
`links` table. Do not dump a 150-node graph into the chat; inspect the branch you are changing.

```python
import json

wf = json.load(open("workflow.json", encoding="utf-8"))
links = {link[0]: link for link in wf.get("links", []) if isinstance(link, list)}
for node in sorted(wf.get("nodes", []), key=lambda n: n["id"]):
    print(node["id"], node["type"], "mode=", node.get("mode", 0), node.get("title", ""))
    print("  widgets:", node.get("widgets_values"))
    for slot in node.get("inputs", []):
        link = links.get(slot.get("link"))
        if link:
            print(f"  {slot['name']} <- {link[1]}:{link[2]}")
```

Convert a UI export without queuing anything:

```bash
comfy run --workflow <workflow.json> --print-prompt --json --host <host> --port <port>
```

The `prompt_preview` event is the API graph ComfyUI would execute. Save that as the starting point if
the source is UI-only. `--print-prompt` does **not** submit a job.

## 3. Copy to scratch

```text
work/scratch/<project-slug>/<workflow-stem>__<variant>.json
```

- Never edit or re-save a file under `workflows/` in place.
- Record the original SHA-256 if you need to prove the shipped file is unchanged.
- Keep the project slug consistent with `work/uploads`, `work/outputs`, and `work/logs`.
- Scratch JSON may use real input filenames. Public graphs use `example.png`, `example.mp4`, and
  `example.wav`.

## 4. Build or patch the API graph

Prefer a small Python builder over hand-editing a large UI JSON. A node is:

```python
"10": {
    "class_type": "PrimitiveStringMultiline",
    "inputs": {"value": "A red fox ..."},
    "_meta": {"title": "Prompt"},
}
```

A link is `["10", 0]`. Keep IDs stable and descriptive; use `_meta.title` for the node name shown in
the UI. Build variants from one function, not from copies of copies.

Common edits and where they live:

| Edit | Node / input |
| - | - |
| Prompt | `PrimitiveStringMultiline.value` |
| Seed | `RandomNoise.noise_seed`, or the sampler's seed widget |
| Size / length | `width`, `height`, `length` on the H3/latent node |
| Steps / schedule | `BasicScheduler.steps` / `scheduler`, or `ManualSigmas.sigmas` |
| Sampler | `KSamplerSelect.sampler_name` |
| LoRA stack | `Power Lora Loader (rgthree)` slots |
| Model files | `unet_name`, `clip_name`, `vae_name`, `lora_name`, `model_name` |
| Save path | `filename_prefix` — **do not change it** |

LoRA stack details:

```json
"5": {
  "class_type": "Power Lora Loader (rgthree)",
  "inputs": {
    "model": ["1", 0],
    "clip": ["2", 0],
    "PowerLoraLoaderHeaderWidget": {"type": "PowerLoraLoaderHeaderWidget"},
    "lora_1": {"on": true, "lora": "minimax\\turbo.safetensors", "strength": 0.8}
  }
}
```

- `lora_N` values are objects, not links. Keep `on`, `lora`, and `strength`.
- Omit unused slots and the `➕ Add Lora` helper; do not leave decoy entries behind.
- `H3AdaLNLoRAFix(mode="port")` goes after the H3 LoRA stack.
- Only functional adapters belong in a public graph. If you need a look, use a scratch copy.

Build rules:

- Model filenames are relative to ComfyUI's model folders and include the subfolder, e.g.
  `minimax\minimax_h3_fl2va_pruned_int8_convrot.safetensors`.
- Do not put absolute paths, drive letters, hostnames, or credentials in a graph.
- Keep `filename_prefix` static. The run's identity is `prompt_id`, not a new folder.
- Remove comparison/debug branches and extra saves before promotion; they double VRAM and runtime.
- If a class is missing, replace it with an installed equivalent or stop. Do not invent a node.

## 5. Validate before submitting

Static check against the live target:

```bash
python scripts/validate_workflow.py work/scratch/<project>/<graph>.api.json \
  --url http://<host>:<port>
```

It checks node classes, required inputs, dynamic combos, link targets, combo values, loader option
lists for model/LoRA files, and save prefixes. It does not submit a job. Fix every error; read the
warnings (placeholders that are not uploaded yet are expected on public graphs).

It reads model availability from `/object_info`, not `/models/<folder>`: `/models` can return an empty
body even when the target has the files, and it omits some formats.

Then preview the exact prompt:

```bash
comfy run --workflow work/scratch/<project>/<graph>.api.json \
  --print-prompt --json --host <host> --port <port>
```

Check the effective class list and model names in `prompt_preview`. For UI files, this is also the
conversion step; if frontend-only nodes remain, strip them in scratch and repeat.

## 6. Submit through the MCP

```js
const run = await tools["comfy-<host>-<port>"].run_workflow({
  workflow_path: "<repo>/work/scratch/<project>/<graph>.api.json",
  wait: false
});
const promptId = run.prompt_id;
```

- The workflow path is read on the MCP machine, not the ComfyUI host. Resolve it to an absolute path
  there.
- There is no per-call target argument. One registration = one target.
- Submit one job per target. Do not queue a batch to "see what happens".
- Store `prompt_id` immediately; it is the only output identity.

## 7. Poll without trusting a single tool

`job({ action: "wait", prompt_id })` can fail at the tool layer while the server job is still running.
`/history/<prompt_id>` is authoritative:

```bash
python scripts/wait_job.py <prompt_id> --url http://<host>:<port> --timeout 3600
```

Success is `status.status_str == "success"` and an `outputs` block. A queue that still lists the job
means it is not done. Do not resubmit because a poll failed; check `/queue` and `/history` first.

## 8. Collect the outputs

Try `fetch_outputs` first:

```js
await tools["comfy-<host>-<port>"].fetch_outputs({
  prompt_id: promptId,
  out_dir: "<repo>/work/outputs/<project>/<YYYY-MM-DD>/<prompt_id>"
});
```

If it returns `download_job_not_found`, falls back to a local address, or the local job state is stuck
at `queued`, download the history URL directly:

```text
http://<comfy-host>:<port>/view?filename=<filename>&subfolder=<subfolder>&type=output
```

`<comfy-host>:<port>` is the target's `COMFYUI_URL` base (not the MCP host); the three values come
from the `outputs[0]` entry. URL-encode them, or let the helper do it:

```bash
python scripts/fetch_output.py <prompt_id> --url http://<host>:<port> \
  --out-dir work/outputs/<project>/<date>/<prompt_id>
```

Then verify:

- File size is non-zero and matches the history metadata.
- `ffprobe` reports the expected streams and durations.
- For video, audio and video stream durations match. `VHS_VideoCombine` uses `-shortest` and can cut
  audio at the last video DTS; the perfect-loop graph uses `CreateVideo -> SaveVideo` for this reason.
- Keep the remote filename. Do not rename it to hide its origin.

Do not pass `inline_images: true`. Collect the local file, verify provenance, then read that copy if
vision is needed.

## 9. Log the run

Append one row to `work/logs/run-log.md` **before** downloading:

| Date | Project | Workflow | Server | prompt_id | Status | Output | Bytes | Notes |
| - | - | - | - | - | - | - | - | - |

Record the staged inputs and their source in Notes. The `prompt_id` + run-log row + output folder are
the provenance chain for vision. Technical verification is size/metadata; vision is creative QA only.

## 10. Promote to the repository

Promotion is a separate, deliberate step. Do not copy scratch files back automatically.

1. **Sanitize.** Remove non-functional LoRAs, replace baked prompts with neutral demo prompts, set
   media defaults to `example.png` / `example.mp4` / `example.wav`, and remove private metadata.
2. **Place it.** UI workflows go in `workflows/<family>/`; API-first graphs go in
   `workflows/<family>/api/` with the `.api.json` suffix. Do not add Markdown to `workflows/`.
3. **Strip debug.** Remove comparison decodes, extra saves, and dead branches. Keep the production
   `filename_prefix` exactly as shipped.
4. **Document.** Update `README.md`, `skills/SKILL.md`, the family subskill, `COMFY-SETUP.md` (models,
   node packs, version gates), and `scripts/download_models.py` / `scripts/install_nodes.py`.
5. **Re-validate the promoted file**, not just the scratch file:
   ```bash
   python scripts/validate_workflow.py workflows/<family>/<graph>.api.json --url http://<host>:<port>
   comfy run --workflow workflows/<family>/<graph>.api.json --print-prompt --json \
     --host <host> --port <port>
   ```
6. **Check the repo.** Every JSON parses, links resolve, media defaults are only `example.*`, no
   non-functional LoRA names remain, and the docs' counts match the tree.
7. **Commit and push.** Report the `prompt_id`, output size, and whether the public graph was actually
   run after sanitization or only statically validated.

### Public-release checklist

- [ ] No non-functional or private LoRAs.
- [ ] Neutral prompts; no private names, paths, hosts, or credentials.
- [ ] Media inputs are exactly `example.png`, `example.mp4`, `example.wav`.
- [ ] `filename_prefix` unchanged.
- [ ] Debug/comparison branches removed.
- [ ] Every model source and custom-node pack is in `COMFY-SETUP.md`.
- [ ] `scripts/validate_workflow.py` and `--print-prompt` pass on a target.
- [ ] `README.md`, umbrella skill, family skill, and counts updated.
- [ ] Commit pushed; run-log entry retained locally.

## 11. Verification recipes

**Streams and exact durations**

```bash
ffprobe -v error -show_entries stream=index,codec_type,duration,nb_frames -of json out.mp4
```

**Loop seam / frame continuity** — compare the seam pair (last frame to first) against the median
adjacent-frame MAE. A seam near the median is a clean loop; a spike is a visible cut. Use the decoded
frames, not thumbnails.

**Audio seam** — compare the end-to-start sample jump against local sample differences, and measure
correlation between protected bridge windows and the anchor core. For loudness, use `ffmpeg` `ebur128`
before normalizing.

**Sharpness A/B** — `ffmpeg` `blurdetect` at a fixed timestamp gives a quick comparative score; it is
global, so depth of field and motion affect it. Pair it with a visual check of the same frames.

**Shipped-artifact proof** — SHA-256 the shipped file before and after scratch work. A changed hash
means someone edited the shipped tree.

## 12. Traps

| Symptom | Cause | Fix |
| - | - | - |
| Edits to an inner subgraph do nothing | Instance widgets override inner nodes | Edit the subgraph instance (`#18` in MOSS, the instance in Krea/Flux). |
| A loader has unexpected models/LoRAs | Decoy or bypassed branch | Ignore it; edit the branch that feeds the sampler. |
| `missing_node_type` for frontend nodes | UI helpers left in an API graph | Strip `Fast Groups Bypasser`, `Label`, `Note`, `MarkdownNote` in scratch. |
| `fetch_outputs` says `download_job_not_found` | Prompt submitted elsewhere or local state cleared | Use `scripts/fetch_output.py` or the `outputs[0]` URL. |
| `job(wait)` errors but the job runs | Tool-layer wait failure | Poll `/history/<prompt_id>` or `scripts/wait_job.py`. |
| `system_stats` describes the wrong GPU | It is a local-only tool | Read the target's `/system_stats` over HTTP. |
| A graph works in the UI but not through MCP | UI-only nodes or instance-only widgets | Convert and inspect `prompt_preview`; use an API graph. |
| Audio is shorter than video | `VHS_VideoCombine` `-shortest` / DTS cut | Use `CreateVideo -> SaveVideo` or verify and mux explicitly. |
| A model "exists" but the loader does not list it | Wrong folder or filename | Check the loader's `/object_info/<Class>` option list, not `/models/<folder>` (which can be empty). |
| `--print-prompt` "ran" but nothing appeared | It only previews; it does not queue | Submit with `run_workflow`; then poll. |
| Dates or `%...%` appear in the save path | A frontend token leaked into `filename_prefix` | Use a static prefix; never invent a new folder. |

## 13. Where to look next

- `../SKILL.md` — hard rules, routing, working directory, MCP behavior, vision provenance.
- `../../MCP-SETUP.md` — transport, registration, target scope, security.
- `../../work/README.md` — scratch/output/log layout.
- `../minimaxh3/SKILL.md` and its subskills — worked examples of UI/API pairs, subgraph overrides,
  loop math, and upscale settings.
