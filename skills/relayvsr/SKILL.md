---
name: relayvsr
description: RelayVSR X2 2× pixel-space video super-resolution in Comfiest — one-step Wan + Flash decoder, audio passthrough, H3/LTX finishing pass.
---

# RelayVSR X2 — 2× video super-resolution

Operating rules live in `../SKILL.md`; the H3/upscale guides are in `../minimaxh3-upscale/SKILL.md`
and `../ltx2-5/SKILL.md`. RelayVSR is a one-step distilled, **pixel-space** video super-resolution
model: Wan backbone plus a Flash decoder, no VAE, no CLIP, no text encoder. It is a finishing pass for
H3/LTX output, not a re-generation.

## Files

Files live in `../../workflows/relayvsr/` and `.../api/`.

| File | Format | Task |
| - | - | - |
| `video-upscale-relayvsr-x2.json` | UI | source video → 2× upscale → H.264 MP4 with source audio |
| `api/video-upscale-relayvsr-x2.api.json` | API | same graph for `run_workflow` |

Four nodes: `RelayVSRModelLoader` → `RelayVSRUpscale`, fed by `VHS_LoadVideoFFmpeg`, muxed by
`VHS_VideoCombine`. Use the API file for runs; open the UI file in the editor.

## Run it

```js
const run = await tools["comfy-<host>-<port>"].run_workflow({
  workflow_path: "<repo>/workflows/relayvsr/api/video-upscale-relayvsr-x2.api.json",
  wait: false
});
```

One job at a time per target. The first run loads ~10 GB of Wan weights; expect a long first-frame
stall before the progress bar moves.

## Addresses

| Node | Id | What to change |
| - | - | - |
| `RelayVSRModelLoader` | `1` | `bundle` (directory under `models/relayvsr`), `dtype`, `offload` |
| `RelayVSRUpscale` | `2` | `sr_ratio` (2 for X2), `chunk_len`, `seed` |
| `VHS_LoadVideoFFmpeg` | `3` | `video` (filename in the target's `input/`), `force_rate` |
| `VHS_VideoCombine` | `4` | `frame_rate`, `filename_prefix`, `crf` |

Edit a copy under `work/scratch/`; never write back into `workflows/`. The API file is plain JSON.

## Settings

- **`sr_ratio 2` is mandatory with X2 weights.** The X2 geometry only accepts 2; asking for 4 raises
  `RelayVSR x2 权重仅支持 2 倍放大`.
- **`chunk_len 16`** frames per streaming window. Wan runs on each window's first/last frame; the
  Flash decoder does the rest. Larger windows avoid boundary work but raise VRAM.
- **`offload` on** (default). Wan blocks move to the GPU one at a time; this is the difference between
  running and OOM at 1080p on 24 GB. Disable only on 32 GB+.
- **`dtype bf16`** (default). The weights are bf16-native; use `fp16` only on a card without bf16.
- **`seed` barely matters.** The model is 1-step distilled (sigma 1 → 0, no CFG).
- **Save:** `COMFY_WORKFLOWS/RELAYVSR_X2`, 24 fps, CRF 19, yuv420p, source audio muxed. Keep the
  prefix static.

## Output and audio

- Output is **2× the input**, not 2× a target. 720p → 1440p; there is no resize stage.
- Audio is passed through, not enhanced. `VHS_LoadVideoFFmpeg` audio → `VHS_VideoCombine`; the model
  only touches pixels.
- `VHS_VideoCombine` muxes with `-shortest`. A 193-frame 24 fps stream can come out as 192 frames /
  8.00 s because the mux cuts at the last B-frame DTS. If the exact tail frame matters, use
  `CreateVideo` → `SaveVideo` or trim the audio to the video length.

## Gotchas

- **`force_rate 24` resamples the source.** The shipped graph uses 24 fps and saves at 24. For a source
  at another rate, set `force_rate 0` **and** `VHS_VideoCombine.frame_rate` to the source fps, or the
  clip plays fast/slow.
- **All frames must share one size.** The runtime rejects a batch whose frames differ in H×W; do not
  mix clips in one load.
- **Resolution is not free.** 768×1344 with 16-frame windows needs ~18–19 GB in bf16; at 1080p the Wan
  KV cache alone is ~12 GB. Keep `offload` on for 24 GB.
- **The bundle list is scanned at import.** After adding/moving weights under `models/relayvsr/`,
  restart ComfyUI (or use the loader's advanced `path` field). A saved bundle name that no longer exists
  fails validation.
- **No prompt, no negative, no guidance.** RelayVSR uses a fixed prompt embedding; there is no text
  encoder.
- **Not a re-generator.** It preserves source pixels and suppresses flicker; it cannot recover detail
  that was never in the source. For 2K H3 re-synthesis, use the refiner chain instead.

## Models

| Folder | Files |
| - | - |
| `models/relayvsr/RelayVSR_X2/` | `wan_x2.safetensors` (~10.1 GB), `flash_x2.safetensors` (~128 MB) |

Both files must sit in the **same** directory; the loader matches them by safetensors metadata
(`relayvsr-wan-x2-v1` / `relayvsr-flash-x2-v1`), not filename. Source:
<https://huggingface.co/lightx2v/RelayVSR_X2>. The optional INT8 conv-rotation bundle is produced by
`custom_nodes/Comfyui-Relay-VSR/convert_to_int8_convrot.py` and selected as its own bundle.

Node pack: <https://github.com/bbaudio-2025/Comfyui-Relay-VSR>
(`RelayVSRModelLoader`, `RelayVSRUpscale`), plus `comfyui-videohelpersuite` for load/save. No extra pip
packages.

## H3 → RelayVSR chain

Generate with the H3 1 MP path (768×1376), stage the result in the target's `input/`, then run a copy of
the RelayVSR API graph with `force_rate 0` and `VHS_VideoCombine.frame_rate 48` to preserve the model's
48 fps cadence. The shipped 24 fps default resamples a 48 fps source and drops half the frames.

## Cost

Same 24 GB RTX 4090, same 8 s clip, same 1536×2752 output:

| Pipeline | Output | Frames | Time | s/frame |
| - | - | - | - | - |
| MiniMax-H3 1 MP generation (input) | 768×1376 @ 48 fps | 387 | 186.5 s | 0.48 |
| RelayVSR X2 | 1536×2752 @ 48 fps | 383 | 287.1 s | 0.75 |
| RelayVSR X2 (24 fps equivalent) | 1536×2752 @ 24 fps | 192 | 145.6 s | 0.76 |
| MiniMax-H3 Regenerate-2K refiner | 1536×2752 @ 24 fps | 192 | 514.2 s | 2.68 |

RelayVSR is ~3.5× faster per output frame than the 2K refiner. Against a Lanczos baseline, RelayVSR
stays closer to the source (PSNR 32.3–34.0 dB) than the refiner (28.3–28.7 dB), while both add similar
high-frequency energy.

## Verified runs

Reference runs on a 24 GB RTX 4090, ComfyUI 0.43.0. Public sanitization changed only the input
placeholder and kept the graph settings.

| Input | Output | Note |
| - | - | - |
| 1376×768, 48 fps | 2752×1536, 192 f / 8.00 s | ~145 s including first weight load |
| H3 768×1376, 48 fps | 1536×2752, 383 f / 7.98 s | ~287 s |
| H3 refiner 2K comparison | 1536×2752, 192 f / 8.00 s | ~514 s for the refiner path |

The verified 48 fps H3 run used `force_rate 0` + `frame_rate 48`; the shipped 24 fps default is for
24 fps sources.
