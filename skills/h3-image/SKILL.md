---
name: h3-image
description: MiniMax-H3-Image in Comfiest — native 33.1B H3 image model, 4–16 MP text-to-image and reference editing, 6-step CFG 1, ComfyUI 0.45.
---

# MiniMax-H3-Image — native 4–16 MP T2I and editing

Operating rules live in `../SKILL.md`. MiniMax-H3-Image is Comfy-Org's 33.1B dense single-stream DiT:
the H3 architecture with the audio branch removed. One checkpoint does text-to-image and reference
editing (up to 16 pictures), at a native ~16 MP, with **6 steps at CFG 1** and no negative prompt.

It is **not** the same model as P-H3-Image (`../ph3-image/SKILL.md`). P-H3-Image is PrunaAI's 4 MP
distillation and uses `PH3ImageConditioning`; MiniMax-H3-Image uses `MiniMaxH3ImageConditioning`,
runs at 4–16 MP, and is much stronger at long, exact text. Use P-H3-Image for fast 4 MP iteration; use
H3-Image for 16 MP finals, posters, packaging, and layout-heavy work.

## Files

Files live in `../../workflows/h3-image/` and are API format for `run_workflow`. They are API-first and
have no UI twins.

| File | Task | Nodes | Output | Save prefix |
| - | - | - | - | - |
| `h3-image-t2i-4mp.api.json` | text -> 2048² draft | 8 | 4.2 MP | `H3_IMAGE/T2I_4MP` |
| `h3-image-t2i-16mp.api.json` | text -> 4096² production | 8 | 16.8 MP | `H3_IMAGE/T2I_16MP` |
| `h3-image-edit.api.json` | `<Picture 1>` local edit -> 2048² | 9 | 4.2 MP | `H3_IMAGE/EDIT` |
| `h3-image-edit-2ref.api.json` | object replacement from `<Picture 2>`; follows Picture 1's size | 10 | source size | `H3_IMAGE/EDIT_2REF` |
| `h3-image-edit-4ref.api.json` | identity + garment + prop + setting from 4 refs -> 2048² | 12 | 4.2 MP | `H3_IMAGE/EDIT_4REF` |

The source graphs were verified before sanitization. The public copies were statically validated and
`--print-prompt`-checked, not re-rendered end-to-end.

## Requirements

- **ComfyUI 0.45.0 or newer.** `MiniMaxH3ImageConditioning` first appears in 0.45.0
  (`comfy_extras/nodes_minimax_h3.py`); 0.44.x does not have it. Verify
  `/object_info/MiniMaxH3ImageConditioning` and check that it lists `clip`, `prompt`, `width`, and
  `height`. A 200 response with empty inputs is a stale or partial build, not a working node.
- No custom node pack and no LoRAs.
- 24 GB-class GPU for 16 MP; w4a8 leaves about 11 GB headroom.

## Models

| Role | File | Size |
| - | - | - |
| DiT (default) | `minimax_h3_image_pruned_w4a8.safetensors` | 12.5 GB |
| DiT (alternative) | `minimax_h3_image_pruned_int8_convrot.safetensors` | 21.0 GB |
| text encoder | `qwen3vl_32b_minimax_h3_int8_convrot.safetensors` (type `minimax`) | 27.1 GB, shared with H3 video |
| VAE | `minimax_h3_image_vae_fp16.safetensors` | 1.2 GB |
| prompt expander (optional, not shipped) | `qwen3.5_9b_w4a8_gptq.safetensors` | 7.3 GB |

w4a8 is the default: it fits 16 MP on 24 GB with room for the text-encoder swap. int8 is ~2 s faster
and slightly sharper on the same seed, but it **changes the composition**, not just the detail: the two
builds are 18.0–18.4 dB apart at a fixed seed. Pick one build and stay on it; do not A/B a seed across
builds. bf16 (40 GB) does not fit a 24 GB card, and the nvfp4 text encoder needs Blackwell FP4.

Download sources are in [`COMFY-SETUP.md`](../../COMFY-SETUP.md). Verify filenames with
`/object_info/UNETLoader`, `/object_info/CLIPLoader`, and `/object_info/VAELoader`, not `/models/<folder>`.
The text encoder is shared with H3 video; `--only h3image` alone does not fetch it. Use
`--only h3,h3image`, or install it from the H3 row.

## Graph

```text
UNETLoader (w4a8) -> CLIPLoader (qwen3vl_32b, type minimax) -> VAELoader (h3 image vae fp16)
MiniMaxH3ImageConditioning(clip, vae, prompt, width, height) -> positive + LATENT
ConditioningZeroOut(positive) -> negative
KSampler(6 steps, cfg 1.0, euler, simple, denoise 1.0) -> VAEDecode -> SaveImage
```

Editing adds one `LoadImage` per reference, wired to `MiniMaxH3ImageConditioning.images.image_1`,
`images.image_2`, … in order; the prompt refers to them as `<Picture 1>`, `<Picture 2>`, …. The public
graphs ship 1, 2 and 4 references. For more, add `images.image_5` … `images.image_16`; the node accepts
16, but 16 was not exercised in this release.

`width`/`height` 0 means "use image_1's size after reference scaling, or 2048² when there is no image".
The 2-ref graph uses 0 so it follows `<Picture 1>`; the 1-ref and 4-ref graphs use 2048². Every size must
be a multiple of 32.

## Settings

- **6 steps**, `cfg 1.0`, `euler`, `simple`, denoise 1.0.
- **No negative prompt.** `ConditioningZeroOut` zeroes the negative. Put everything you want to avoid
  into the positive description as a visible property.
- Seed 42 in the public graphs. Change it for a new take; keep it to reproduce.
- 4 MP 2048²: ~18 s on a 4090 with w4a8; 16 MP 4096²: ~26 s; 5472×3072: ~28 s. The first run in a
  process also pays the 27 GB text-encoder swap.
- Native sizes: 4096×4096, 4736×3552, 5024×3360, 5472×3072, 6272×2688, and their portrait rotations.
  The 16 MP model needs no upscaler.

## Text and layout

Text is the model's standout capability. A five-line poster layout came back **exact** at 4096²
(`KYOTO` / `AUTUMN 1936` / `NOVEMBER 3 - 21` / `HIGASHIYAMA DISTRICT` / `OPEN DAILY 9 TO 5`). Krea,
Flux Klein and MOSS all garble at that length.

- Put the exact wording in double quotes and say where it sits and how it is set.
- State the order (`top to bottom`, `left to right`) when it matters.
- If label colours are unspecified, ask for one uniform neutral style; otherwise the model assigns a
  different colour per label.
- Say the language when it is not English.
- For posters, cards, boards, UI, charts and diagrams, build the finished information architecture in
  slots, not a scene containing the requested objects.

Before filling a prompt, read
[`../prompt-writing/minimax-h3-image-prompt-writer/SKILL.md`](../prompt-writing/minimax-h3-image-prompt-writer/SKILL.md).
It encodes the vendor caption spec: subject identity, pose, contact, scale, environment, lighting,
lens/medium, physical plausibility, and "visible, not implied".

## Editing

- `<Picture 1>` is the one being edited; later pictures supply identity, props, materials or composition.
- **Describe the finished image**, not the operation, and state what is preserved: same pose, same fur,
  same position and scale, same camera angle.
- **Local attribute changes work well** — a garment colour, an object swapped, a material changed — and
  keep identity (freckles, hair, eyes, scars). Charcoal -> burgundy turtleneck: 21.2 s, Laplacian 364
  vs 452 for T2I.
- **Object replacement from `<Picture 2>` works structurally.** Bench -> red bicycle in a station scene:
  2752×1536, 27.7 s, 9,293,605 B, Laplacian 2238. The edit path is grittier than T2I; the object lands
  in the right place, but expect reference-latent noise.
- **Whole-scene re-imagining only partly works.** Winter -> summer moved the palette but left 28 % of
  the frame reading as snow-white and came out noisy (Laplacian ~1192 vs 452 for T2I). The reference is
  a strong scene anchor; keep the change local.
- **Adding references re-composes.** The cost is roughly linear (~+11 s per reference), and the output is
  not stable across reference counts: 1↔4 is 20.19 dB at 256 px and 1↔8 is 9.87 dB. A fixed seed does
  not isolate identity across ref counts; judge identity on the faces.
- **Keep the reference set small.** 1–2 references cover identity and a prop. 4 is useful for a
  garment/prop/setting composition. 8 is 5× the wall time of 1 and produces a different image; it is not
  automatically better.
- The public graphs ship **1, 2 and 4** references. Add `images.image_5` … `images.image_16` for more;
  16 was not exercised in this release.
- All image slots default to `example.png`; upload every reference before a run.

Multi-reference cost, same target scene and seed:

| Refs | Wall | Bytes | PSNR vs 1-ref (256 px) |
| - | - | - | - |
| 1 | 20.4 s | 6,134,363 | — |
| 4 | 47.1 s | 6,095,759 | 20.19 dB |
| 8 | 102.3 s | 6,561,145 | 9.87 dB |

## Prompt expander

The official workflow puts a Qwen3.5-9B (or Qwen3.8-27B PE) in front of the model. It rewrites a short
request into the detailed caption and also chooses an aspect ratio. It costs about +37 s at 4 MP and it
**writes the composition**, not just adjectives: the fox test gained sky and moved the subject lower in
frame. Use it for one-liners; hand-write when exact text, counts, layout or canvas matters.

The expander graph and its 7.3 GB model are **not** in this release. The prompt writer covers the
hand-written path, and the official ComfyUI template can be used when you want the expander.

## Verified runs (RTX 4090 24 GB, ComfyUI 0.45.0)

| Test | Size | Build | Wall | Bytes |
| - | - | - | - | - |
| fox | 2048² | w4a8 | 17.9 s | 6,958,408 |
| fox | 2048² | int8 | **13.8 s** | 6,917,295 |
| fox | 4096² | w4a8 | 26.4 s | 24,708,099 |
| poster (exact five-line text) | 4096² | w4a8 | 28.4 s | 23,635,919 |
| portrait | 4096² | w4a8 | 30.7 s | 22,592,167 |
| wide | 5472×3072 | w4a8 | 27.7 s | 33,792,844 |
| edit, charcoal -> burgundy | 2048² | w4a8 | 21.2 s | 5,989,148 |
| edit, winter -> summer | 2048² | w4a8 | 20.7 s | 8,396,623 |
| edit, replace object from `<Picture 2>` | 2752×1536 | w4a8 | 27.7 s | 9,293,605 |
| edit, 4 references | 2048² | w4a8 | 47.1 s | 6,095,759 |
| edit, 8 references | 2048² | w4a8 | 102.3 s | 6,561,145 |

Every run completed first try with no OOM, offload tricks, tiled decode or chunked attention.

## Gotchas

- **0.45.0 is real.** On 0.44.x the node is absent, or present with an empty input schema on a partial
  build. Update ComfyUI and re-query `/object_info/MiniMaxH3ImageConditioning`.
- **Do not mix w4a8 and int8 in a comparison.** A fixed seed is not a controlled A/B across builds.
- **Sizes are multiples of 32.** 4096×2160 is invalid; use 4096×2176 or 5472×3072.
- **No negative prompt / no CFG.** `cfg` stays 1.0; everything you want to avoid must be a visible
  property in the positive caption.
- **Editing is reference-anchored.** A large scene change fights the reference and gets noisy; change
  one attribute at a time.
- **More references re-compose, not just inform.** 1↔4 is 20.19 dB and 1↔8 is 9.87 dB at 256 px. Each
  reference costs ~+11 s; keep the set to 1–2 for identity and a prop, 4 for a full composition.
- **The edit path is noisier than T2I.** Local attribute changes stay clean; object replacement and
  scene changes carry more high-frequency energy (Laplacian 364–2238 vs ~450 for T2I).
- **The expander rewrites the composition.** If exact text or layout matters, hand-write the caption.
- **Outputs are PNGs.** Collect by `prompt_id`; do not change the save prefix.

## Verify before production

```bash
python scripts/validate_workflow.py workflows/h3-image/h3-image-t2i-4mp.api.json --url http://<host>:<port>
python scripts/validate_workflow.py workflows/h3-image/h3-image-t2i-16mp.api.json --url http://<host>:<port>
python scripts/validate_workflow.py workflows/h3-image/h3-image-edit.api.json --url http://<host>:<port>
python scripts/validate_workflow.py workflows/h3-image/h3-image-edit-2ref.api.json --url http://<host>:<port>
python scripts/validate_workflow.py workflows/h3-image/h3-image-edit-4ref.api.json --url http://<host>:<port>
comfy run --workflow workflows/h3-image/h3-image-t2i-4mp.api.json --print-prompt --host <host> --port <port>
```
