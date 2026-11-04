---
name: ph3-image
description: P-H3-Image in Comfiest — PrunaAI's distilled MiniMax-H3 image model, native ComfyUI 0.44, 4 MP text-to-image and multi-reference edits.
---

# P-H3-Image — native image generation and editing

Operating rules live in `../SKILL.md`. P-H3-Image is PrunaAI's image generation/editing distillation of
MiniMax-H3. It is **native ComfyUI**: `PH3ImageConditioning` lives in
`comfy_extras/nodes_minimax_h3.py`, and the `minimax` CLIP/VAE paths are core. Support landed in
**ComfyUI 0.44.0**; 0.43.x does not have the node. No custom nodes, no LoRAs.

## Files

Files live in `../../workflows/ph3-image/`.

| File | Format | Nodes | Images | Save prefix |
| - | - | - | - | - |
| `ph3-image-edit-4img.api.json` | API | 29 | 4 (subject + 3 refs) | `PH3_EDIT_4IMG` |
| `ph3-image-edit-4img.json` | UI | 30 | 4 | `PH3_EDIT_4IMG` |
| `ph3-image-edit-5img.api.json` | API | 31 | 5 | `PH3_EDIT_5IMG` |
| `ph3-image-t2i.json` | UI | 20 | — | `PH3_T2I` |

The API files are the agent path; the 4-ref UI converts to 29 API nodes. There is no T2I API mirror in
this release — convert the UI file if you need one.

## Models — w4a8 only on 24 GB

| Component | File |
| - | - |
| Diffusion | `p-h3-image_w4a8.safetensors` (13.4 GB) |
| Text encoder | `p-h3-image_text_encoder_w4a8.safetensors` (3.6 GB) |
| Prompt upsampler | `p-h3-image_prompt_upsampler_w4a8.safetensors` (6.7 GB) |
| VAE | `p-h3-image_vae_int8_convrot.safetensors` (3.1 GB) |

The w4a8 set is the 24 GB option. bf16 needs ~55 GB of weights / ~56 GB peak; int8 is ~30 GB / ~31 GB
peak. The bf16 prompt upsampler (19.3 GB) is not shipped; w4a8 is the safe choice. Source:
<https://huggingface.co/PrunaAI/P-H3-Image-Comfy>. The optional 2 GB image LoRA is not included.

Put the files in `models/diffusion_models/`, `models/text_encoders/`, and `models/vae/` with no
subfolders — the graphs load them by exact filename. ComfyUI 0.44 caches folder listings; `GET
/object_info` clears that cache, so you do not need a restart after adding weights.

## Edit graph

- **`image_1` is the subject and sets the canvas** (`ImageScaleToTotalPixels`, 4 MP, multiple of 32).
  Extra references go to `PH3ImageConditioning` at native size; it scales each internally.
- `BatchImagesNode` feeds the prompt upsampler: `image_1` at 1 MP, every ref `ResizeAndPadImage`d to
  that canvas. `StringFormat` builds one `<Picture N>` block per image.
- `TextGenerate` (thinking off for edits) writes the structured edit brief; `ComfySwitchNode` can
  bypass it. The upsampler is doing real work — keep it on.
- `PH3ImageConditioning` autogrow keys are `images.image_1..image_9` (9 max). `BatchImagesNode` keys
  are `images.image0..N`.
- Sampling: 8-step `ManualSigmas`
  `1.0, 0.984753, 0.967905, 0.951688, 0.925372, 0.881923, 0.810083, 0.528718, 0.0`,
  `euler`, `BasicGuider`, cfg 1, `MiniMaxH3SigmaShift` 1.0/1.0.
- Every image slot defaults to `example.png`; **set all of them**. Never mix reference counts across a
  batch.

Prompt format: bind each image with `<Picture 1>`, `<Picture 2>`, ... and say what changes. Keep
identity on `<Picture 1>`. The shipped public prompts are generic so they work with any reference set;
replace them with the actual subject/setting/garment mapping.

## T2I graph

The UI T2I graph is 20 nodes and saves at `PH3_T2I`. It uses the same w4a8 stack and 8-step schedule;
`TextGenerate` runs with thinking on. 4 MP / 2048×2048 is the tested default.

## Verified runs

Reference runs on a 24 GB RTX 4090, ComfyUI 0.44.0:

| Run | Output | Size | Time |
| - | - | - | - |
| T2I 4 MP | `PH3_T2I_00001_.png` 2048×2048 | 6,677,120 B | 21.4 s |
| 4-image edit | `PH3_EDIT_4IMG_00001_.png` 1824×2304 | 5,431,544 B | 56.9 s cold |
| 5-image edit | `PH3_EDIT_5IMG_00001_.png` 1824×2304 | 5,706,589 B | 93.6 s warm |
| 4-image edit (UI) | `PH3_EDIT_4IMG_00002_.png` 1824×2304 | 5,302,960 B | ~57 s |

## Findings and limits

- **Multi-reference works.** 4 and 5 images composed in one pass; identity (face shape, freckles,
  hair) is preserved when `image_1` is the subject. The node accepts up to 9 images.
- **Small garment details drift.** The 5-ref coat gained buttons and a second pocket not in the
  reference. Treat hardware details as approximate.
- **Text is not reliable.** Signage is suggestive, not legible.
- **Cost.** 4 MP T2I ~21 s; 4-ref edit ~57 s cold; 5-ref edit ~94 s warm. Each extra reference adds
  vision/latent tokens and upsampler work.
- **VRAM.** 4 MP fits on one 24 GB card with headroom; 8 MP was not tested.
- **QA crops beat contact sheets.** A small contact sheet can misread a tile; crop the region and
  inspect at full size before trusting a caption.
- **All frames/slots must be valid.** Do not mix reference counts or leave an `example.png` slot in a
  production run.
- Outputs are PNGs; collect by `prompt_id`. If `fetch_outputs` fails, use the direct `/view` URL (see
  [`../workflow-development/SKILL.md`](../workflow-development/SKILL.md)).

## Requirements

- ComfyUI **0.44.0 or newer** — verify `/object_info/PH3ImageConditioning`.
- w4a8 model set above; no custom node pack, no LoRA.
- 24 GB-class GPU for 4 MP; 8 MP is untested on 24 GB.
