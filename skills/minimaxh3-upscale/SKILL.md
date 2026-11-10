---
name: minimaxh3-upscale
description: MiniMax H3 2K upscale and refine workflows in Comfiest — latent-space 2x upscale, 2-step re-synthesis refiner or 3-step IC fidelity refiner, t2v and v2v paths, with 2560×1440 output.
---

# MiniMax H3 2K upscale — t2v, v2v, and IC

Operating rules live in `../SKILL.md`; the H3 family guide is in `../minimaxh3/SKILL.md`. Latent-space
upscale + Regenerate-2K refine for MiniMax H3. The t2v path keeps the 768P draft latent and decodes
once at the end. The v2v and IC paths take a decoded source/draft, VAE-encode it at the front, and keep
the rest in latent space.

Pika H3 Flex is a 768P generator; use this chain when you need 2K. The Pika adapters are not part of
the refiner stack.

Two refiners ship:

- **2-step re-synthesis** — faster and punchier; the model re-reads the frame and can invent structure.
- **3-step IC fidelity** — a 0.2 GB rank-21 IC LoRA plus LMS Sharp; stays close to the draft and keeps
  the draft audio bit-aligned.

```text
t2v:  prompt -> 768P draft latent --\
                                     +--> H3 latent upscale 2x -> 2-step refine -> decode
v2v:  source -> 768P latent --------/

ic:   Pika 768P draft mp4 -> VAE encode -> latent upscale 2x -> 3-step IC refine on ref2va
      -> decode -> mux the draft audio
```

## Files

Files live in `../../workflows/minimaxh3/api/` and are API format for `run_workflow`.

| File | Task | Length | Target | Status |
| - | - | - | - | - |
| `upscale-minimax-2k-t2v.api.json` | prompt -> 2K, 5 s | 124 f | 2560×1440 | verified before sanitization |
| `upscale-minimax-2k-t2v-8s.api.json` | prompt -> 2K, 8 s (temporal split) | 192 f | 2560×1440 | verified before sanitization |
| `upscale-minimax-2k-v2v.api.json` | existing clip -> 2K, 8 s | 192 f | 2560×1440 | verified before sanitization |
| `upscale-minimax-2k-ic.api.json` | Pika 768P draft -> 2K IC fidelity | 124 f | 2560×1440 | verified before sanitization |

**Public-release note.** The draft `Power Lora Loader` is empty in the public t2v graphs; the original
six-LoRA draft preset included style/adult-oriented LoRAs. The functional refine stack stays:
Regenerate-2K refiner, turbo, and sharp. The v2v and IC prompts are generic because their sources are
placeholders, and the IC graph defaults to `example.mp4` plus a neutral scene description. Re-run the
sanitized graphs before production.

**Draft stack.** The t2v 2K graphs embed the fastvideo 4-step preset for a single-graph run; they are
the older fast path. For the cleanest 2K and for the IC graph, generate a Pika H3 Flex 1344×768 draft
first. The fastvideo preset is not a reference draft: it carries ~7× the Laplacian of a Pika draft when
stripped to the motion/dareties pair, and ~3× even with its full six-LoRA stack.

## Requirements

- ComfyUI 0.44.0 or newer. The IC graph needs core `BlockSparseAttention`, `ModelAttentionBackend`,
  `ComfyMathExpression`, `TrimAudioDuration`, and `MiniMaxH3ReferenceToVideo`; `MiniMaxH3LatentUpscaleWithModel`
  is also required (PR #17412 or newer).
- `ComfyUI-PlagueKind-Nodes` for `MMH3UltimateUpscale`, `MMH3TemporalSplitParams`,
  `MMH3SpatialSplitParams`, and `H3AdaLNLoRAFix`.
- `ComfyUI-KJNodes` for `MiniMaxChunkFeedForward` and `ImageResizeKJv2` (5 s and IC graphs).
- rgthree `Power Lora Loader` and `ComfyUI-VideoHelperSuite`.

The IC path adds **no custom node pack**. Its four published `OpenH3IC*` helper nodes and the
`LynnRealH3VAELoader`/`sol_h3_vae` fast decoder are not required; the graph uses core nodes and the
packs above.

## Models

Verify with the loader's `/object_info/<Class>` option list (for example `LatentUpscaleModelLoader.model_name`
and `LoraLoaderModelOnly.lora_name`); `/models/<folder>` can be empty even when the file is installed.
Download sources are in [`COMFY-SETUP.md`](../../COMFY-SETUP.md).

| Role | File |
| - | - |
| refine base (2-step) | `minimax/minimax_h3_fl2va_pruned_int8_convrot.safetensors` |
| refine base (IC) | `minimax/minimax_h3_ref2va_pruned_int8_convrot.safetensors` |
| draft (t2v) | `minimax/minimax_h3_fastvideo_vsa_datafree_1300step_4step_int8_convrot.safetensors` |
| text encoder | `qwen3vl_32b_minimax_h3_int8_convrot.safetensors` (type `minimax`) |
| video / audio VAE | `minimax/minimax_h3_video_vae_fp16.safetensors`, `minimax/minimax_h3_audio_vae_fp32.safetensors` |
| latent upscaler | `minimax_h3_latent_upscaler_3d_bf16.safetensors` (in `latent_upscale_models`) |
| refiner (2-step) | `minimax/minimax_h3_open_regenerate_2k_refiner_rank_16_bf16.safetensors` |
| turbo (2-step) | `minimax/minimax_h3_fl2v_turbo_4step_v1.2_768p_comfyui_bf16.safetensors` |
| sharp (both) | `minimax/minimax_h3_lms_v1.0_r64.safetensors` |
| IC LoRA | `minimax/minimax_h3_open_regenerate_2k_ic_lora_avg_rank_21_bf16.safetensors` (0.2 GB) |

The rank-16 refiner is Kijai's recommended cut of Sana's Open-H3-Regenerate-2K merge; it is visually
identical to the rank-384 file at 1/38th the size. Turbo is the LightX2V v1.2 adapter. Sharp is the
LMS sharpness adapter; dropping it saves 1.2 GB and loses some detail.

The IC LoRA is Kijai's rank-21 resize of the full 5.9 GB Open-H3-Regenerate-2K-IC file (199,951,344 B).
It is an SVD resize at 0.99 Frobenius retention, not a retrain, and it is a drop-in replacement: 42.9 dB
from the full-rank arm, 0.08 dB apart on PSNR-to-draft.

**Do not "fix" Kijai's alphas.** The file writes small signed residual `alpha` scalars and folds the
scale into `lora_B`; ComfyUI's `alpha / lora_A.shape[0]` is intentionally not 1.0. The shipped rank-16
2K refiner uses the same convention.

## Effective settings

- t2v graphs: fixed 1344×768 → 2560×1440 (16:9). The v2v and IC graphs expose `DRAFT WIDTH/HEIGHT` and
  `TARGET WIDTH/HEIGHT`; for 9:16 use 768×1376 → 1536×2752 (tiled; verify VRAM).
- 2-step refine: sigmas `0.7, 0.494118, 0`; Euler; cfg 1; no sigma-shift node is needed with explicit
  sigmas.
- 2-step stack: refiner 1.0, turbo 1.0, sharp 1.0, `H3AdaLNLoRAFix(mode=port)` after the LoRAs.
- IC refine: `up3` sigmas `0.834942, 0.696852, 0.468753, 0`; Euler; cfg 1.
- IC stack: LMS Sharp 1.0 → rank-21 IC 1.0 → `H3AdaLNLoRAFix(mode=port)` → `MiniMaxH3SigmaShift(12, 3)`
  → `MiniMaxChunkFeedForward(chunks=2)` → `BlockSparseAttention(sol-attn, tau=1.3, min_tokens=12288)`.
  No HyperFlow.
- 5 s graph: full-frame 2K with `MiniMaxChunkFeedForward(chunks=2)` + core
  `BlockSparseAttention(sol-attn, tau=1.3, min_tokens=12288, sink=exact_kv_and_rows)`.
- 8 s / v2v: `MMH3UltimateUpscale` with temporal `136 f / 17 overlap` and spatial
  `token_budget=70000` auto tiles, keeping every sampling pass at 37 latent frames.
- Audio is pinned from the source/draft (`MMH3UltimateUpscale`; the v2v graph relies on this).
- Output: 2560×1440, 24 fps, h264 CRF 12, source/draft audio.

## IC fidelity refiner

`upscale-minimax-2k-ic.api.json` is the Open-H3-Regenerate-2K-IC path. It is a second pass: run a 768P
**Pika H3 Flex** draft first, collect the MP4, then feed it back as the source. Copy
`pika-h3-t2v.api.json` to `work/scratch/`, set `6.width=1344` and `6.height=768`, keep the 6-step
contract, and run it; the shipped 736×416 default is not the verified draft size. The IC graph reads
`example.mp4` from the target's `input/`.

```text
draft mp4 -> VHS_LoadVideo 24 fps -> cover-crop 1344x768 -> pad/trim to 124
          -> VAEEncodeTiled -> MiniMaxH3LatentUpscaleWithModel 2560x1440
          -> MiniMaxH3ReferenceToVideo(<Video 1> = draft, target size)
          -> freeze the empty audio rows -> concat with the upscaled video latent
          -> ref2va + LMS Sharp + rank-21 IC + AdaLN fix + SigmaShift(12/3)
          -> ChunkFeedForward(2) + BlockSparseAttention(sol-attn)
          -> euler, up3 3-step -> decode -> mux the draft audio
```

- **The conditioning path is the difference.** The draft is fed as `<Video 1>` through
  `MiniMaxH3ReferenceToVideo` at the *target* resolution, so the model sees it as a reference. The
  existing 2-step graph re-noises an upscaled latent instead.
- **HyperFlow is not used.** The earlier config used HyperFlow + LMS + IC, but the only ComfyUI
  HyperFlow conversion has a fused-QKV alpha bug and needs a file patch. Dropping HyperFlow costs
  0.27–0.35 dB PSNR, makes the image slightly sharper and steadier, and removes a 3.9 GB download and
  the patch. Ship the no-HyperFlow stack.
- Sigmas: `0.834942, 0.696852, 0.468753, 0` (`up3`), euler, cfg 1. Do **not** use `up4`
  (`0.923077, 0.834942, 0.696852, 0.468753, 0`); it was only tested on the earlier void draft and is
  unnecessary now.
- `ref_image_size=match` is the tested setting; `max` was not tried.
- 124 frames is the tested length. 192 is grid-valid (`n % 17 == 5`) but was not run through IC.
  `TrimAudioDuration.duration` is pinned to `5.1666667` for 124 f at 24 fps; if you change `LENGTH`,
  change that duration to `LENGTH / 24` as well (or the audio and video will diverge).
- Feed a **Pika H3 Flex 6-step draft**, not the fastvideo 4-step preset. On the same prompt and seed,
  the fastvideo 4-step draft carried ~7× the Laplacian of a clean Pika draft (2046 vs 284) and ~2× the
  gradient; even with its full six-LoRA stack it was 3× the Laplacian and 1.6× the flicker. See
  [`../minimaxh3-pika/SKILL.md`](../minimaxh3-pika/SKILL.md).
- **No new node pack.** The published graph's `OpenH3ICDraft`, `OpenH3ICPrompt`, `OpenH3ICSigmas`,
  `OpenH3ICComposeLatent`, `LynnRealH3VAELoader`, and `sol_h3_vae` are replaced with core 0.44 nodes,
  KJNodes, and VideoHelperSuite. Every class is already in the Comfiest install.
- **Decode is the slow tail.** The graph uses the standard fp16 H3 video VAE, roughly 40 s of each run.
  `MiniMaxH3ReferenceToVideo` also re-encodes the reference clip for its `minimax_refs` blocks, so the
  draft is VAE-encoded twice per run.

### IC results (Pika draft, RTX 4090, 2560×1440, 124 f, 24 fps)

| Metric | IC rank-21, no HF | IC full-rank + HF | Existing 2-step |
| - | - | - | - |
| PSNR vs draft | 32.37 dB | **32.72 dB** | 29.07 dB |
| PSNR vs lanczos 2K | 33.22 dB | **33.64 dB** | 29.17 dB |
| Laplacian variance | 119.7 | 116.9 | 183.1 |
| Gradient energy | 13.10 | 13.20 | 15.54 |
| Optical flow px/frame | 3.08 | 3.16 | 3.40 |
| Flicker MAD | **7.57** | 7.65 | 8.71 |
| Wall time | **306.9 s** | 391.0 s | 282.8 s |

All IC arms beat the existing 2-step refiner by 3.3–3.6 dB, with lower flicker and far less added
high-frequency energy. The IC file choice moves the output by ~42.9 dB (drop-in equivalent); HyperFlow
on/off moves it by ~40.4 dB. IC detail bands on the Pika draft: **+40 % fine, +1 % medium, −1 % coarse**;
the existing refiner adds +74 % / +27 % / +16 %.

IC costs ~24 s more than the existing 2-step path on a 5 s clip. It keeps the draft audio bit-aligned
(corr 0.9999, lag 0); the existing v2v graph round-trips audio through the audio VAE and shifts it
~55 ms. Use IC for lip-sync, music, or any cut where the audio must stay in sync.

**Neither refiner restores detail absent from the source.** IC stays closer to the draft but cannot
invent resolution that was never captured.

Use IC when the shot must stay faithful to the draft: faces, product, signage, anything where
re-composition is a defect. Keep the existing 2-step refiner when you want more perceived sharpness,
do not mind the model re-reading the frame, and want the fastest path.

## v2v inputs

The v2v and IC graphs read `example.mp4` from the target's `input/`:

1. Stage the clip in `../../work/uploads/<project>/` under the exact placeholder name and
   `upload_file` it to the target. Replace the placeholder with the real filename in a scratch copy if
   needed.
2. Edit the prompt to describe the clip (subject, setting, motion, lighting). The IC graph already
   carries the official enhancement prefix; replace only the `Scene description` line.
3. Set `LENGTH` to the source length on the 17k+5 grid (124, 141, 158, 175, 192…), and set
   `DRAFT WIDTH/HEIGHT` to the source aspect (1344×768 landscape, 768×1376 portrait). On the IC graph,
   also set `TrimAudioDuration.duration` to `LENGTH / 24`.
4. Set `TARGET WIDTH/HEIGHT` (2560×1440 default).
5. For a source without audio, the graph needs an `EmptyAudio` fallback; the current files assume an
   audio track.

Preprocessing matches Sana's `--input-video`: force 24 fps, cover-crop to the draft canvas, cap to
`LENGTH`, repeat the last frame if short, VAE-encode, and encode the source audio.

## Verified timings (24 GB RTX 4090)

| Run | Wall |
| - | - |
| t2v 5 s | ~5 min |
| t2v 8 s | ~12 min |
| v2v 8 s | ~7 min |
| IC v2v 5 s (124 f) | ~5.1 min |

## v2v length and cadence

- The 17k+5 length grid has a **floor of 124 frames**. A 3.6 s take at 24 fps is 89 frames, below the
  trained range. The graph pads by repeating the last frame, so set
  `LENGTH = max(124, grid(source_frames))` and trim the duplicated tail in the edit.
- Output is **24 fps**. A 30 fps timeline gets cadence judder unless the edit decodes frames rather
  than seeks the video.
- Portrait 9:16 verified: `768×1376` draft → `1536×2752` target; both sides are multiples of 32.

## Source resolution — where the refiner stops

The refiner can sharpen and add plausible micro-texture, but it cannot recover high-frequency detail
that was never in the source. The v2v path also resizes the source to the 1344×768 draft canvas before
the VAE encode, and the 2-step refine keeps only 30% of that latent (σ₀ 0.7).

| Source | Source pixels | Result |
| - | - | - |
| 736×416 | 0.31 MP | strong improvement; sign edges, faces, fruit, reflections recover |
| 384×224 | 0.086 MP | obvious sharpening, but structure is invented and detail stays soft; clearly worse than 0.3 MP |

**Use ≥0.3 MP sources for faithful v2v upscaling.** 0.086 MP is a regeneration/stylization input, not
an upscale. If the source is that small, generate at a higher resolution or use a restoration model
(SeedVR2 is installed) instead of the H3 refiner.

## 4K

Do not attempt a 4K DiT pass on 24 GB with this pipeline:

- 3840×2160 is rejected — 2160 is not a multiple of 32, and H3 patchifies 2×2 latent tokens.
- 3840×2176 is grid-valid, but the 20 GB model staging cycles per tile and the job never settles.
- Practical ceiling is 2560×1440. For 4K, refine at 2K, then upscale the 2K latent/video to 4K without
  another DiT pass, or use a pixel-space restoration upscaler.

## Quality notes

- **Existing 2-step refiner:** σ₀ 0.7 preserves source composition; its 3-step σ₀ 0.909 variant
  re-composes more and can invent props. Use that variant only when re-composition is acceptable.
- **IC 3-step refiner:** `up3` is a fidelity pass, not a re-synthesis. It holds ~32.4 dB PSNR to a Pika
  draft and adds energy almost only in the finest band. The trade-off is a slightly less punchy image
  than the existing refiner and ~24 s more wall time.
- **Draft quality dominates.** A noisy draft is not fixable by the refiner. Use Pika H3 Flex 6-step for
  any 768P draft; a fastvideo 4-step draft carries ~7× the Laplacian and ~2× the gradient.
- Turbo + sharp are polish; refiner + turbo are what make the 2-step path work.
- **Identity and detail:** the refiner holds faces, hair, wardrobe, and background across a batch and
  adds real micro-detail. Laplacian variance on a fixed 1080-wide output went 17.6 → 44.5 on the same
  clip. It also raises micro-contrast and saturation, so grade a refined batch against its unrefined
  neighbours, not against the source.
- **It is not a faithful enlargement.** Pores and knit texture can be invented by the existing refiner.
  IC stays closer to the draft but still cannot restore detail that was never captured. Refining
  speakers while leaving b-roll unrefined makes the b-roll look soft; run the same refiner on every clip
  in a cut.
- **Wrong source tree = silent re-cast.** A refiner handed the wrong clip can re-cast the scene while
  size, decode, and duration checks still pass. Confirm the source path and spot-check identity before
  a batch.
- The sharp LoRA is applied as a normal LoRA, not through the author's aligned
  `MiniMaxH3AddGuide` second pass, so treat it as a generic sharpener.
