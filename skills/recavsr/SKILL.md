---
name: recavsr
description: ReCaVSR in Comfiest — one-step streaming 4× video super-resolution on Wan2.2, 16.9 MP on 24 GB, audio and frame rate preserved.
---

# ReCaVSR X4 — one-step streaming video super-resolution

Operating rules live in `../SKILL.md`. ReCaVSR is USTC's one-step streaming diffusion VSR built on
Wan2.2 TI2V-5B. It reads a clip in blocks (21 frames, then 8), runs one denoising step per block, reuses
the previous block's latents and a cache of past keys/values, and decodes each block as it is generated
with its own FlashDecoder. Length costs disk, not memory.

**4× is the trained path.** 2× and 1.5× are documented and work, but the model gains the most at 4×.
For a 2× pixel-space pass, RelayVSR X2 is the smaller/faster option; see
[`../relayvsr/SKILL.md`](../relayvsr/SKILL.md).

## Files

Files live in `../../workflows/recavsr/`.

| File | Format | Nodes | Save prefix |
| - | - | - | - |
| `video-upscale-recavsr-x4.json` | UI | 5 | `COMFY_WORKFLOWS/RECAVSR_X4` |
| `api/video-upscale-recavsr-x4.api.json` | API | 4 | `COMFY_WORKFLOWS/RECAVSR_X4` |

The UI file is for ComfyUI; the API file is the agent/MCP path. The source graphs were verified before
sanitization. The public copies were conversion-validated and statically validated, not re-rendered
end-to-end.

## Requirements

- **ComfyUI 0.44.0 or newer.**
- **`ComfyUI-ReCaVSR`** — a required custom-node pack (GPL-3.0, registry `comfyui-recavsr`,
  <https://github.com/PedroMarinhoDev/ComfyUI-ReCaVSR>). It is installed by
  `scripts/install_nodes.py`; restart ComfyUI after installing.
- The pack's `requirements.txt` installs `triton` (attention kernels) and `opencv-python-headless`
  (reference frame resize). Both have fallbacks: without Triton the attention runs in PyTorch; without
  OpenCV the resize is bilinear. `kernels fast` worked on Windows in testing.
- int8 needs an NVIDIA GPU of compute capability 7.5 or newer (RTX 20 series up); elsewhere ComfyUI
  dequantizes the weights, which saves memory but not time. `fast` kernels need CC 8.0 for the fused
  decoder attention, with an eager fallback.

## Models

Files go in `models/recavsr/` (the loader scans that folder; `recavsr:` can also be set in
`extra_model_paths.yaml`).

| Role | File | Size |
| - | - | - |
| transformer (default) | `transformer_int8_convrot.safetensors` | 6.27 GB |
| transformer (alternative) | `transformer.safetensors` (bf16) | 10.6 GB |
| FlashDecoder | `flashdecoder.safetensors` | 229 MB |
| prompt embedding | `prompt.safetensors` | 4.2 MB |

The int8 file is the default: 1.75–1.8× faster than bf16 on the transformer, about 4 GB less VRAM, and
47–48 dB from bf16. The bf16 transformer is not in the ComfyUI manifest; download it manually from
[`kopper/ReCaVSR`](https://huggingface.co/kopper/ReCaVSR) if you want it.

**`decoder: vae` is not shipped.** It needs ComfyUI's `wan2.2_vae.safetensors` in `models/vae/`, decodes
the whole video at the end, and is 25–40× slower. FlashDecoder is the tested path. The optional VAE is
not in the manifest.

`ReCaVSRLoader.transformer` lists **every** file in `models/recavsr`, including `flashdecoder` and
`prompt`. Pick `transformer_int8_convrot.safetensors`; the other two are not transformer models.

## Graph

```text
LoadVideo -> ReCaVSRUpscale -> SaveVideo
ReCaVSRLoader -> ReCaVSRUpscale.model
```

- `LoadVideo` reads the source clip; `SaveVideo` stores the returned VIDEO.
- The node reads a VIDEO block by block and keeps the input's **audio and frame rate**. `SaveVideo` does
  not re-encode; do not add a second encode.
- `images` input instead of `video` is supported but holds every frame in RAM and produces no audio.
  Use the VIDEO path.

## Settings

| Input | Default | Notes |
| - | - | - |
| `scale` | 4 | Trained for 4×; 2× and 1.5× documented. Any size is padded to a multiple of 32 and cropped back. |
| `color_fix` | `none` | `adain` matches each frame's mean/variance to the input; `wavelet` puts the input's low frequencies under the output's detail. Costs 1–3 s; geometry is unchanged. |
| `seed` | 42 | The one-step noise. Change it for a new run; identical inputs are cached. |
| `decoder` | `flashdecoder` | `vae` needs `wan2.2_vae` and is 25–40× slower. |
| `kernels` | `fast` | `exact` is the reference path; `fast` is 7–24% faster and 49–50 dB from exact. |
| `kv_offload` | false | Keeps attention history in RAM. The node enables it automatically when the output would not fit. |
| `encoder` | `auto` | HEVC NVENC, then H.264 NVENC, then x264; the first that opens at the output size. |
| `fps` | 30 | Ignored for a VIDEO input, which keeps its own frame rate. |

## Cost

Throughput is linear in output pixels: **`seconds ≈ frames × output_MP × 0.030`** on an RTX 4090 with
int8 + fast + FlashDecoder. Examples:

| Clip | Output | Warm |
| - | - | - |
| 8 s, 48 fps, 416×736 source | 1664×2944 (4.9 MP) | 57.3 s |
| 8 s, 48 fps, 768×1376 source | 3072×5504 (16.9 MP) | 195.5 s |
| 5.2 s, 24 fps, 672×384 source | 2688×1536 (4.9 MP) | 17.3 s |
| 5.2 s, 24 fps, 960×480 source | 3840×1920 (7.4 MP) | 26.3 s |
| 5.2 s, 24 fps, 672×384 source, 2× | 1344×768 | 8.1 s |

Cold runs pay 33–87 s of Triton kernel build plus weight load for that output size. Compare warm to
warm.

## Quality

Against a bicubic 4× of the same frame, ReCaVSR adds 3.5–6× the high-frequency energy at 4× and 2.3× at
2×. On H3 clips it is recovering detail the 0.3 MP/1 MP renders lack, not just sharpening. The numbers
are Laplacian/gradient, not a signed-off perceptual judgement: check a 1:1 crop before a final.

## Verified runs (RTX 4090 24 GB, int8 + fast + FlashDecoder)

| Source | Output | Frames | Warm |
| - | - | - | - |
| H3 416×736, 48 fps | 1664×2944 | 383 | 57.3 s |
| H3 768×1376, 48 fps | 3072×5504 | 383 | 195.5 s |
| 960×480, 24 fps | 3840×1920 | 124 | 26.3 s |
| 672×384, 24 fps | 2688×1536 | 124 | 17.3 s |
| 672×384, 24 fps, 2× | 1344×768 | 124 | 8.1 s |
| 672×384, 24 fps, 4× + adain | 2688×1536 | 124 | 20.4 s |
| 672×384, 24 fps, 4× + wavelet | 2688×1536 | 124 | 18.3 s |

All runs completed on 24 GB. 3072×5504 (16.9 MP) is above the card's own tested 5376×3072 (16.5 MP)
and still fits via the node's 4-frame input projection. Output has H.265 video + AAC audio in the H3
case; audio and frame rate are preserved.

## H3 chain

Use ReCaVSR as the finishing pass, not an iteration tool:

- 0.3 MP H3 draft (416×736, 48 fps) → 4× 1664×2944 in ~57 s per 8 s clip. Good for iterating the final.
- 1 MP H3 source (768×1376, 48 fps) → 4× 3072×5504 in ~195 s. Use only for the final.
- For a cheaper 2× pass, use RelayVSR X2. ReCaVSR's 4× path gains more detail.
- Upscale each shot as its own clip when the cut matters; ReCaVSR treats a clip as one shot and
  shimmers briefly after a scene cut.

## Gotchas

- **ComfyUI caches identical node inputs.** Re-running the same graph with the same seed returns the
  cached result in 0.2 s without executing. Change the seed for a real repeat timing.
- **The loader lists all three files.** Pick `transformer_int8_convrot.safetensors`.
- **Cold overhead scales with output size.** Triton builds kernels per size; warm runs are the real
  throughput.
- **Scene cuts shimmer.** The node carries recycled latents and attention history across the cut. Split
  shots for clean results.
- **`decoder: vae` is slow and untested here.** It needs `wan2.2_vae.safetensors` and holds the whole
  video at once; it can tile at 4K.
- **The pack is not universal.** A target without `ComfyUI-ReCaVSR` cannot run this graph. Verify
  `/object_info/ReCaVSRLoader` and `/object_info/ReCaVSRUpscale` first.
- **Do not re-encode the output.** The node encodes block by block; `SaveVideo` only stores it.
- **Images input is not the production path.** It holds every frame in RAM and drops audio; use VIDEO.

## Verify before production

```bash
python scripts/validate_workflow.py workflows/recavsr/api/video-upscale-recavsr-x4.api.json \
  --url http://<host>:<port>
comfy run --workflow workflows/recavsr/video-upscale-recavsr-x4.json --print-prompt \
  --host <host> --port <port>
```

Check `/object_info/ReCaVSRLoader` and `/object_info/ReCaVSRUpscale`, then run a short clip and confirm
the output keeps audio and frame rate.
