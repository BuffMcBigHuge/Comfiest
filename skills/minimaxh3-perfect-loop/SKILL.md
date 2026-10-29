---
name: minimaxh3-perfect-loop
description: MiniMax H3 perfect-loop workflow in Comfiest — seamless text-to-video loops with synchronized audio, a 154-frame 6.42 s output, and a 308-frame ×2 seam check.
---

# MiniMax H3 perfect loop — T2AV

Operating rules live in `../SKILL.md`; the H3 family guide is in `../minimaxh3/SKILL.md`.
`../../workflows/minimaxh3/api/perfect-loop-minimax-h3.api.json` generates a seamless
text-to-video loop with synchronized audio. It adapts the supplied `Perfect Looper (MiniMax-H3)
V1-hotfix` workflow to the node classes and models used by this repository.

The default output is **154 frames at 24 fps = 6.4167 s**, plus a 308-frame ×2 copy for checking the
stitch. Scope is text-to-looping-video (T2AV); there are no image, video, or audio file inputs.

```text
anchor pass (56 f) -> trim 8/8 -> 40-frame core ----\
                                                     +-> bridge pass (192 f) -> take 114 middle frames
40-frame core --------------------------------------/          |
                                                               +-> concat = 154-frame loop
```

## Files

Files live in `../../workflows/minimaxh3/api/` and are API format for `run_workflow`.

| File | Task | Length | Output |
| - | - | - | - |
| `perfect-loop-minimax-h3.api.json` | prompt -> seamless loop | 154 f | 6.4167 s, 416×736, 24 fps, stereo audio |

The same graph also writes an `_X2` MP4 (308 f / 12.834 s) for checking the stitch; it is not a
separate workflow file.

**Public-release note.** The stack keeps only the two functional adapters: LightX2V Turbo at 0.8 and
the 8-step motion enhancer at 0.5. The supplied preset's style/anatomy LoRAs are not shipped. The
loop math, node graph, sampler settings, and save prefixes are unchanged. The original graph was
verified end to end; the public graph has been re-validated with `--print-prompt` but not re-rendered
after the LoRA reduction, so check the seam before production.

## Loop math

| Stage | Value |
| - | - |
| Anchor length | 56 frames (`5 + 17×3`) |
| Trim from anchor start/end | 8 frames each |
| Anchor core | 40 frames |
| Bridge target | 192 frames (`5 + 17×11`) |
| Frames protected at each bridge end | 39 |
| Generated middle | 114 frames (`192 - 2×39`) |
| Final loop | 154 frames (`40 + 114`) |
| Duration | 6.4167 s at 24 fps |
| ×2 check | 308 frames / 12.834 s |

`39` is the clean default: it is an exact H3 video run and lands on an exact 40 Hz audio boundary
(65 audio steps), so the protected picture and sound cover the same physical interval. Other exact
H3 runs (`5, 22, 56, ...`) are possible, but re-check the audio seam. The bridge target must be
`5 + 17k`, and the two protected windows must not overlap: `2 × preserve_frames < target length`.

## Graph layout

| ID | Node | Role |
| - | - | - |
| 1–9 | loaders, LoRA stack, `H3AdaLNLoRAFix`, `H3SLAAttention`, `BasicScheduler`, `KSamplerSelect` | Shared H3 stack |
| 10 | `PrimitiveStringMultiline` | Prompt |
| 11–16 | `MiniMaxH3ReferenceToVideo` 56 f -> sample -> decode video/audio | Anchor pass |
| 17 | `GetImageRangeFromBatch` start 8, 40 frames | Anchor core video |
| 18 | `TrimAudioDuration` start 0.333333 s, 1.666667 s | Anchor core audio |
| 19 | `EmptyMiniMaxH3LatentAV` 416×736, 192 f | Bridge target |
| 20 | `MiniMaxH3ContexMaskedAVBridge` | Protect core tail at start and core head at end |
| 21–26 | `MiniMaxH3ReferenceToVideo` 192 f -> sample -> decode | Bridge pass |
| 27 | `GetImageRangeFromBatch` start 39, 114 frames | Bridge middle video |
| 28 | `TrimAudioDuration` start 1.625 s, 4.75 s | Bridge middle audio |
| 29–30 | `ImageBatch`, `AudioConcat` | 154-frame loop picture + audio |
| 31, 37 | `CreateVideo` -> `SaveVideo` | Final MP4 |
| 32–34, 38 | `ImageBatch` ×2, `AudioConcat` ×2, `CreateVideo` -> `SaveVideo` | ×2 seam check |

The protected bridge windows are dropped. The loop starts on anchor-core frame 0; the generated
middle follows the 40-frame core, and the bridge's generated tail leads back into frame 0.

## Models and sampling

- UNET: `minimax/minimax_h3_fastvideo_vsa_datafree_1300step_4step_int8_convrot.safetensors`
- Text encoder: `qwen3vl_32b_minimax_h3_int8_convrot.safetensors` (type `minimax`)
- Video VAE: `minimax/minimax_h3_video_vae_fp16.safetensors`
- Audio VAE: `minimax/minimax_h3_audio_vae_fp32.safetensors`
- Turbo adapter: `minimax/minimax_h3_fl2v_lightx2v_v0.1_dareties_v4_step600_comfy_fro_fulladaln.safetensors`
- Motion enhancer: `minimax/minimax-h3_fl2v_8Step_motion_enhancer.safetensors`
- `H3AdaLNLoRAFix(mode=port)` after the LoRA stack
- `H3SLAAttention` is present but **disabled** (dense pass)
- 8 steps, `beta` schedule, `er_sde` sampler, cfg 1
- **No RIFE** — the loop is authored at 24 fps

The bridge is `MiniMaxH3ContexMaskedAVBridge`, not the supplied workflow's
`MiniMaxH3MaskedAVBridge` (which is not installed here). Its `start_frames` and `end_frames` both
receive the 40-frame core; `start_audio` and `end_audio` both receive the core audio;
`preserve_frames=39`; `crop=disabled` because the core is already on the target canvas.

## Controls

These are plain node widgets in the API file. Edit a copy under `../../work/scratch/` if you need
different values.

| Control | Node | Default |
| - | - | - |
| Prompt | `10` | fox / winter loop prompt |
| Width, height | `11`, `21` (must match `19`) | 416×736 |
| Anchor length | `11` | 56 |
| Bridge length | `19`, `21` | 192 |
| Anchor trim | `17` start_index | 8 frames |
| Core audio trim | `18` start_index / duration | 0.333333 s / 1.666667 s |
| Preserve frames | `20` | 39 |
| Bridge middle | `27` start_index / num_frames | 39 / 114 |
| Middle audio trim | `28` start_index / duration | 1.625 s / 4.75 s |
| Anchor seed | `12` | 608531924772021 |
| Bridge seed | `22` | 987654321098765 |
| Save prefix | `37` / `38` | `COMFY_WORKFLOWS/MINIMAX_PERFECT_LOOP` / `_X2` |

If you change the anchor length, trim, bridge length, or preserve value, recompute the core/middle
start and duration and keep every frame count on the 24 fps H3 grid.

## Prompt format

Keep the three-part structure visible in node `10`:

```text
integrated_multimodal_description: [Shot 1] Continuous video, continuous single shot, no video cuts.
Looping video. Video loops seamlessly at the end.
<subject, setting, camera, lighting>
overall_soundscape: <ambient sound and effects>
non_diegetic_music: N/A
```

The seam is authored by the graph, not by the prompt; the loop instruction only reinforces it. Change
the subject and setting, but keep the single-shot and seamless-loop lines, and describe the audio in
`overall_soundscape` because the graph generates synchronized sound.

## Saving: use CreateVideo -> SaveVideo

The final two outputs deliberately use core `CreateVideo` -> `SaveVideo`, not `VHS_VideoCombine`.
`VHS_VideoCombine` uses ffmpeg `-shortest` with copied H.264 B-frames and cuts audio at the last
video **DTS** instead of the last PTS. In testing it produced 6.336 s of audio against 6.417 s of
video, about 81 ms short, which leaves an audible gap at the loop point. `SaveVideo` produced exact
6.417 s audio and video on both the single loop and the ×2 file. If you replace the save path,
verify with `ffprobe` that the audio and video stream durations match before calling the loop
finished.

## Requirements

- ComfyUI 0.43.0 or newer for core `CreateVideo`/`SaveVideo`.
- `ComfyUI-MiniMaxH3-Context-Loop` for `MiniMaxH3ContexMaskedAVBridge`
  (<https://github.com/ethanfel/ComfyUI-MiniMaxH3-Context-Loop>).
- `ComfyUI-KJNodes` for `GetImageRangeFromBatch`.
- The H3 family nodes, models, and VAEs listed above; `rgthree-comfy`.
- A 24 GB-class GPU for the default 192-frame bridge at 0.3 MP.

## Model sources

Download paths and folder layout are in [`COMFY-SETUP.md`](../../COMFY-SETUP.md).

| Role | Public source |
| - | - |
| Text encoder, video/audio VAEs | <https://huggingface.co/Comfy-Org/MiniMax-H3> |
| fastvideo UNET | <https://huggingface.co/Kijai/MiniMax-H3-experimental> |
| LightX2V 4–8 step Turbo (public substitute) | <https://huggingface.co/HAOOOOOOO51/Minimax_h3_fl2v_lightx2v_turbo_4to8step_v0.1-v1.0_768p_v4_step600_dareties_fro095_pruned> |
| 8-step motion enhancer | <https://huggingface.co/rzgar/minimax-h3_fl2v_8Step_motion_enhancer> |

The verified run used a full-AdaLN conversion of the LightX2V v0.1 4–8 step adapter. The published
file above is the author's pruned-backbone release of the same Turbo A conversion; it drops the 51
AdaLN pairs and keeps the backbone factors. The downloader renames it to the filename the graph
expects, and `H3AdaLNLoRAFix(mode=port)` handles either form. Re-check the seam after substituting.

## Reference run

One 416×736 run on a 24 GB RTX 4090, ComfyUI 0.43.0:

- prompt id `393f6f45-c962-48b3-903d-9b453f5b0719`
- `MINIMAX_PERFECT_LOOP_00001_.mp4` — 154 f, 6.417 s, 2,152,590 bytes
- `MINIMAX_PERFECT_LOOP_X2_00001_.mp4` — 308 f, 12.834 s, 4,305,751 bytes

Technical checks from that run:

- Video loop seam MAE `0.07002` vs median adjacent-frame MAE `0.07112` (46th percentile).
- Internal core-to-middle join MAE `0.07425` (60th percentile).
- Audio loop end-to-start sample jump `0.00046 / 0.00055` per channel (43rd/49th percentile of
  local sample differences).
- Bridge protected head/tail vs anchor core: correlation `0.924` / `0.971`, MAE `0.0041` / `0.0023`.

## Known limits

- **T2AV only.** Looping an existing 24 fps video is not implemented; it would need a
  `LoadVideo` -> `GetVideoComponents` -> resize/trim branch feeding the same 56-frame anchor contract.
- **No UI wrapper.** This is an API-first graph, like the 2K upscale and charreplace additions.
- **Loop quality varies by seed.** One seed was tested; vary either seed and re-check the seam if
  the first result is weak.
- **AAC padding.** The MP4 audio stream is exactly 6.417 s. Extracted WAVs can carry a small
  decoder-padding tail; measure the container stream, not a decoded WAV tail alone.
- **Audio join.** If the internal core-to-middle audio join is audible, a short crossfade in post is
  the simplest fix; there are no fade nodes in the graph.
