---
name: ltx2-5
description: LTX-2.5 22B distilled video family in Comfiest — text-to-video, identity-reference-to-video, and image-to-video with joint generated audio, 512×960, 8.04 s.
---

# LTX-2.5 — video with joint audio

Operating rules live in `../SKILL.md`; the H3 families are in `../minimaxh3/SKILL.md` and
`../minimaxh3-pika/SKILL.md`. LTX-2.5 22B distilled generates **video and audio in one pass** — the
audio is model output, not a supplied track — and muxes both into an H.264 MP4.

Three API-first graphs cover text, identity reference, and first-frame conditioning. There are no UI
mirrors; open the JSON when you need the wiring.

## Files

Files live in `../../workflows/ltx/api/` and are API format for `run_workflow`.

| File | Task | Conditioning | Output |
| - | - | - | - |
| `ltx2-5-t2v.api.json` | text → video | prompt only | 512×960, 8.04 s, stereo |
| `ltx2-5-ref2v.api.json` | reference subject → video | prompt + one identity image | 512×960, 8.04 s, stereo |
| `ltx2-5-i2v.api.json` | image → video | prompt + first frame | 512×960, 8.04 s, stereo |

The graphs are 44–47 nodes. Every touchable node carries `_meta.title` (`prompt`, `width`, `height`,
`frames`, `frame rate`, `seed`, `reference image`, `first frame`, `save video`).

## Model stack

| Folder | File |
| - | - |
| `checkpoints/ltx` | `ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors` |
| `text_encoders` | `gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors` |
| `vae/ltx` | `ltx-2.5-video-vae-conv-bf16.safetensors`, `ltx-2.5-audio-vae-bf16.safetensors` |
| `latent_upscale_models` | `ltx-2.5-latent-spatial-upscaler-x2-bf16-1.0.safetensors` |
| `loras/ltx` | `Best_FaceID_v1.0_LoRA.safetensors` (ref2v only) |

`CLIPLoader` uses type `ltxv` with the Gemma 4 12B encoder; it is not interchangeable with the
Krea/Qwen3-VL encoder. `Best_FaceID_v1.0_LoRA` is applied in ref2v only, at strength 1.0; it is a no-op
without a reference and is deliberately absent from t2v/i2v. Source:
<https://huggingface.co/Alissonerdx/LTX-Best-Face-ID>.

## Effective settings

- **Resolution.** The graph asks for 512×960 but samples at 256×480: `EmptyImage` → `ImageScaleBy 0.5`
  → `GetImageSize` → `EmptyLTXVLatentVideo`, then `LTXVLatentUpsampler` ×2 before the refiner. Width
  and height primitives are the **final** size; keep them even multiples of 64.
- **Frames.** 193 → 25 latent frames → 8.04 s at 24 fps. Length must be `8n+1`; 197 decodes as 193
  because the refinement pass drops the partial tail. Use 193 or 201.
- **First pass:** 8 steps, `euler_ancestral_cfg_pp`, `LTXVScheduler` (max_shift 2.05, base_shift 0.95,
  stretch on, terminal 0.1), cfg 1.
- **Refiner:** 4 steps, `euler_cfg_pp`, manual sigmas `0.85, 0.7250, 0.4219, 0.0`, cfg 1.
- **Seed:** fixed at `432312402084296` in all three. Change the `easy seed` node, not the `RandomNoise`
  widgets.
- **Save:** `COMFY_WORKFLOWS/LTX/t2v`, `.../ref2v`, `.../i2v`; 24 fps, CRF 19, yuv420p, audio muxed.
  Never change the prefix.

## Addresses

| | `t2v` | `ref2v` | `i2v` |
| - | - | - | - |
| prompt | `44` | `46` | `45` |
| width | `41` | `43` | `42` |
| height | `42` | `44` | `43` |
| frames | `43` | `45` | `44` |
| frame rate | `40` | `42` | `41` |
| seed | `39` | `41` | `40` |
| image | — | `47` | `46` |
| save prefix | `6` | `6` | `6` |

Edit a copy under `work/scratch/`; never write back into `workflows/`. The API files are plain JSON:
`inputs.value` on the prompt node, `inputs.image` on `LoadImage`, `inputs.frame_rate` on the save node.

## Inputs

- **t2v:** prompt only. The shipped prompt is a red fox at golden dawn.
- **ref2v:** `47.image` defaults to `example.png`; upload a subject image under the exact filename.
  `LTXIdentityOverlapConditioning #36` prepends the reference as separate tokens; this is reference
  conditioning, not i2v.
- **i2v:** `46.image` defaults to `example.png`; `LTXVImgToVideoInplace #34` writes it into the first
  latent frames with a noise mask of `1 - strength`. `strength 1.0` is a full first-frame lock.

`upload_file` preserves the filename; stage images in `work/uploads/<project>/` and upload the same file
to every target that may run the job.

## Reference conditioning (`ref2v`)

`LTXIdentityOverlapConditioning` (ComfyUI-BFSNodes) widgets:
| Widget | Default | Meaning |
| - | - | - |
| `source_id` | `2` | training-time source phase segment |
| `phase_scale` | `1` | strength of that phase |
| `ref_resize_mode` | `match_target` | center-crop + resize to the video size; `match_target_letterbox` fits the whole ref (use for mismatched aspect); `native_resolution` encodes at the ref's own bucket |
| `layout` | `overlap` | coordinate convention the checkpoint was trained with; `strata`/`st_drc`/`sidecar` are different conventions, not quality knobs |
| `reference_guidance_scale` | `1` | >1 adds a third forward pass per step and amplifies the reference; start at 2–4 if identity decays |
| `reference_temporal_offset_latents` | `0` | 0 = historical frame-0 placement |

**Text and reference compete.** Naming garments or hair in the prompt lets the text outvote the
reference. For identity work, keep the prompt vague about clothing and let the reference carry it.

## Image-to-video (`i2v`)

`LTXVImgToVideoInplace` encodes the image and writes it into the first latent frames. The image is
bilinear-resized to the latent size internally, so any aspect works, but the video's aspect wins.
The first frame is **conditioned, not pasted**: the VAE round trip and sampler can reinterpret fine
detail. Use this to continue an image, not to reproduce it exactly.

## Gotchas

- **`VHS_VideoCombine.frame_rate` must equal the model's frame rate.** The source template carried 8
  against a 24 fps model, which would have produced a 24 s video over 8 s of audio. The shipped graphs
  use 24.
- **`LTXVScheduler` reads the concat AV latent.** Both video and audio latents are required before the
  first sampler; do not remove the `LTXVEmptyLatentAudio` → `LTXVConcatAVLatent` edge.
- **Dead nodes were removed** (two `BasicScheduler`s and one `ManualSigmas`). Do not re-add them.
- **22B int8 + Gemma 12B does not fit 24 GB at once.** `PathchSageAttentionKJ`,
  `LTXVChunkFeedForward (2, 4096)`, and `LTX2AttentionTunerPatch` exist for that reason. Expect weight
  streaming and a slower first run; do not drop them on a 24 GB target.
- **Audio is generated, never driven.** There is no external track and no lip-sync guarantee beyond
  what the prompt implies. For a specific track, drive the audio latent instead.
- **No UI mirror.** The graphs are API-first; the source UI subgraph versions are not shipped.

## Model sources

All from <https://huggingface.co/Lightricks/LTX-2.5>:

- `diffusion_models/ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors`
- `text_encoders/gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors`
- `vae/ltx-2.5-video-vae-conv-bf16.safetensors`
- `vae/ltx-2.5-audio-vae-bf16.safetensors`
- `latent_upscale_models/ltx-2.5-latent-spatial-upscaler-x2-bf16-1.0.safetensors`
- `Best_FaceID_v1.0_LoRA.safetensors` from <https://huggingface.co/Alissonerdx/LTX-Best-Face-ID>

Node packs: core `comfy_extras.nodes_lt*`, `ComfyUI-VideoHelperSuite`, `ComfyUI-KJNodes`,
`ComfyUI-BFSNodes` (identity conditioning), `rgthree-comfy`, `comfyui-easy-use`.

## Verified runs

Reference runs on a 24 GB RTX 4090, ComfyUI 0.43.0. Public sanitization changed the input placeholders;
the model stack and settings are unchanged.

| Graph | Output | Bytes | Note |
| - | - | - | - |
| `t2v` | `t2v_00002-audio.mp4` | 3,281,741 | red fox, golden dawn; 512×960, 8.04 s |
| `ref2v` | `ref2v_00001-audio.mp4` | 2,368,508 | identity + wardrobe carried into a snowy forest |
| `i2v` | `i2v_00001-audio.mp4` | 2,389,672 | first frame locked; smile and hair motion |

A full run is ~90 s on the reference 4090 including the 22B load. The i2v satchel strap came back with
a floral print instead of woven tan; that is the “conditioned, not pasted” behaviour, not a bug.

Validate before production:

```bash
python scripts/validate_workflow.py workflows/ltx/api/ltx2-5-t2v.api.json --url http://<host>:<port>
comfy run --workflow workflows/ltx/api/ltx2-5-t2v.api.json --print-prompt --host <host> --port <port>
```
