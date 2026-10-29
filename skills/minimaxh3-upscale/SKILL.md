---
name: minimaxh3-upscale
description: MiniMax H3 2K upscale and refine workflows in Comfiest — latent-space 2x upscale, 2-step refiner, t2v and v2v paths, with 2560×1440 output.
---

# MiniMax H3 2K upscale — t2v and v2v

Operating rules live in `../SKILL.md`; the H3 family guide is in `../minimaxh3/SKILL.md`. Latent-space
upscale + Regenerate-2K refine for MiniMax H3. The 768P draft never leaves latent space between
generation and the 2K refine: one VAE decode at the end, and for v2v one VAE encode at the front.

```text
t2v:  prompt -> 768P draft latent --\
                                     +--> H3 latent upscale 2x -> 2-step refine -> decode
v2v:  source -> 768P latent --------/
```

## Files

Files live in `../../workflows/minimaxh3/api/` and are API format for `run_workflow`.

| File | Task | Length | Target | Status |
| - | - | - | - | - |
| `upscale-minimax-2k-t2v.api.json` | prompt -> 2K, 5 s | 124 f | 2560×1440 | verified before sanitization |
| `upscale-minimax-2k-t2v-8s.api.json` | prompt -> 2K, 8 s (temporal split) | 192 f | 2560×1440 | verified before sanitization |
| `upscale-minimax-2k-v2v.api.json` | existing clip -> 2K, 8 s | 192 f | 2560×1440 | verified before sanitization |

**Public-release note.** The draft `Power Lora Loader` is empty in the public t2v graphs; the original
six-LoRA draft preset included style/adult-oriented LoRAs. The functional refine stack stays:
Regenerate-2K refiner, turbo, and sharp. The v2v prompt is generic because its source is a placeholder.
Re-run the sanitized graphs before production.

## Requirements

- ComfyUI with `MiniMaxH3LatentUpscaleWithModel` (PR #17412 or newer).
- `ComfyUI-PlagueKind-Nodes` for `MMH3UltimateUpscale`, `MMH3TemporalSplitParams`,
  `MMH3SpatialSplitParams`, and `H3AdaLNLoRAFix`.
- `ComfyUI-KJNodes` for `MiniMaxChunkFeedForward` (5 s graph only).
- rgthree `Power Lora Loader` and `ComfyUI-VideoHelperSuite`.

## Models

Verify with `/models/<folder>` and the loader combos. Download sources are in
[`COMFY-SETUP.md`](../../COMFY-SETUP.md).

| Role | File |
| - | - |
| refine base | `minimax/minimax_h3_fl2va_pruned_int8_convrot.safetensors` |
| draft (t2v) | `minimax/minimax_h3_fastvideo_vsa_datafree_1300step_4step_int8_convrot.safetensors` |
| text encoder | `qwen3vl_32b_minimax_h3_int8_convrot.safetensors` (type `minimax`) |
| video / audio VAE | `minimax/minimax_h3_video_vae_fp16.safetensors`, `minimax/minimax_h3_audio_vae_fp32.safetensors` |
| latent upscaler | `minimax_h3_latent_upscaler_3d_bf16.safetensors` (in `latent_upscale_models`) |
| refiner | `minimax/minimax_h3_open_regenerate_2k_refiner_rank_16_bf16.safetensors` |
| turbo | `minimax/minimax_h3_fl2v_turbo_4step_v1.2_768p_comfyui_bf16.safetensors` |
| sharp | `minimax/minimax_h3_lms_v1.0_r64.safetensors` |

The rank-16 refiner is Kijai's recommended cut of Sana's Open-H3-Regenerate-2K merge; it is visually
identical to the rank-384 file at 1/38th the size. Turbo is the LightX2V v1.2 adapter. Sharp is the
LMS sharpness adapter; dropping it saves 1.2 GB and loses some detail.

## Effective settings

- t2v graphs: fixed 1344×768 → 2560×1440 (16:9). The v2v graph exposes `DRAFT WIDTH/HEIGHT` and
  `TARGET WIDTH/HEIGHT`; for 9:16 use 768×1376 → 1536×2752 (tiled; verify VRAM).
- Refine: 2-step sigmas `0.7, 0.494118, 0`; Euler; cfg 1; no sigma-shift node is needed with explicit
  sigmas.
- Refiner 1.0, turbo 1.0, sharp 1.0, `H3AdaLNLoRAFix(mode=port)` after the LoRAs.
- 5 s graph: full-frame 2K with `MiniMaxChunkFeedForward(chunks=2)` + core
  `BlockSparseAttention(sol-attn, tau=1.3, min_tokens=12288, sink=exact_kv_and_rows)`.
- 8 s / v2v: `MMH3UltimateUpscale` with temporal `136 f / 17 overlap` and spatial
  `token_budget=70000` auto tiles, keeping every sampling pass at 37 latent frames.
- Audio is pinned from the source/draft (`MMH3UltimateUpscale`; the v2v graph relies on this).
- Output: 2560×1440, 24 fps, h264 CRF 12, source/draft audio.

## v2v inputs

The v2v graph reads `example.mp4` from the target's `input/`:

1. Stage the clip in `../../work/uploads/<project>/` under the exact placeholder name and
   `upload_file` it to the target. Replace the placeholder with the real filename in a scratch copy if
   needed.
2. Edit the prompt to describe the clip (subject, setting, motion, lighting). A generic
   “enhance details while preserving the source” caption works but is weaker.
3. Set `LENGTH` to the source length on the 17k+5 grid (124, 141, 158, 175, 192…), and set
   `DRAFT WIDTH/HEIGHT` to the source aspect (1344×768 landscape, 768×1376 portrait).
4. Set `TARGET WIDTH/HEIGHT` (2560×1440 default).
5. For a source without audio, the graph needs an `EmptyAudio` fallback; the current file assumes an
   audio track.

Preprocessing matches Sana's `--input-video`: force 24 fps, cover-crop to the draft canvas, cap to
`LENGTH`, repeat the last frame if short, VAE-encode, and encode the source audio.

## Verified timings (24 GB RTX 4090)

| Run | Wall |
| - | - |
| t2v 5 s | ~5 min |
| t2v 8 s | ~12 min |
| v2v 8 s | ~7 min |

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

- 2-step σ₀ 0.7 preserves source composition; 3-step σ₀ 0.909 re-composes more and can invent props.
  Use 3-step only when re-composition is acceptable.
- Turbo + sharp are polish; refiner + turbo are what make 2-step work.
- The sharp LoRA is applied as a normal LoRA, not through the author's aligned
  `MiniMaxH3AddGuide` second pass, so treat it as a generic sharpener.
