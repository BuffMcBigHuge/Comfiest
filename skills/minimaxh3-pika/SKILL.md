---
name: minimaxh3-pika
description: Pika H3 Flex is the default MiniMax H3 generation path in Comfiest — 6-step LCM, 24 fps, text/first-last/reference modes, and the official Comfy-Org adapters.
---

# Pika H3 Flex — default H3 generation

Operating rules live in `../SKILL.md`; the fastvideo H3 family is in `../minimaxh3/SKILL.md`.
Pika H3 Flex is MiniMax-H3 post-trained by Pika Labs and shipped as two ComfyUI LoRA adapters. It is
the **default H3 generation path** in this repository: 6 steps, 24 fps, native audio, and stronger
text, signage, edge, and reference identity than the fastvideo stack.

Use the fastvideo variants in `../minimaxh3/SKILL.md` for fast drafts; use Pika for finals.

## Files

Files live in `../../workflows/minimaxh3/api/` and are API format for `run_workflow`.

| File | Mode | Inputs | Output |
| - | - | - | - |
| `pika-h3-t2v.api.json` | T2VA | text | 736×416, 124 f, 24 fps, audio |
| `pika-h3-fl2va.api.json` | FL2VA | text + first/last image | same |
| `pika-h3-ref2va.api.json` | Ref2VA | text + reference image | same |

The graphs are 14–16 nodes and have no UI twin. Edit a copy under `work/scratch/` if you need a
different size, seed, prompt, or input; never change the shipped save prefix.

## Model stack

| Role | File |
| - | - |
| T2V / FL2VA base | `minimax/minimax_h3_fl2va_pruned_int8_convrot.safetensors` |
| Ref2VA base | `minimax/minimax_h3_ref2va_pruned_int8_convrot.safetensors` |
| T2V / FL2VA adapter | `minimax/pika/pika_h3_flex_fl2va_v1_bf16.safetensors` |
| Ref2VA adapter | `minimax/pika/pika_h3_flex_ref2va_v1_bf16.safetensors` |
| Text encoder | `qwen3vl_32b_minimax_h3_int8_convrot.safetensors` (type `minimax`) |
| Video VAE | `minimax/minimax_h3_video_vae_fp16.safetensors` |
| Audio VAE | `minimax/minimax_h3_audio_vae_fp32.safetensors` |

Use the **Comfy-Org** 1.96 GB adapters, not the rank-56 community resize. Match the adapter to the
base: fl2va adapter on the fl2va base, ref2va adapter on the ref2va base.

## Sampling contract

Do not improvise this schedule; it is the official 6-NFE contract.

```text
LoRA strength       1.0
CFG                 1.0 (BasicGuider)
Sampler             lcm
Sigmas              1.0, 0.972973, 0.923077, 0.8, 0.571429, 0.333333, 0.0
Sigma-shift node    none — the shift is baked into the sigma list
Extra turbo LoRA    none — the adapter is already distilled
Output              24 fps, no RIFE
```

The seven sigmas are the Pika knots after video-shift 12. Do not drop below seven values. Do not stack
Lightning, fastvideo, or another turbo adapter; it breaks the output. `BasicScheduler` with 8 steps and
`er_sde` is the fastvideo stack, not this contract.

## Modes and inputs

- **T2V (`pika-h3-t2v`)**: `6.prompt`; no media input.
- **FL2VA (`pika-h3-fl2va`)**: `6.first_frame` and `6.last_frame` are `LoadImage` nodes defaulting to
  `example.png`. Replace them with the endpoint images; both are optional in the node, but the graph
  wires both.
- **Ref2VA (`pika-h3-ref2va`)**: `6.ref_images.ref_image_0` is a `LoadImage` defaulting to
  `example.png`; `ref_image_size=max` for identity work. Add more references as
  `ref_images.ref_image_N` if the graph is extended.

Stage media in `work/uploads/<project>/` under the exact filename and `upload_file` it to the target.
`upload_file` preserves the name.

## Prompt format

Pika expects the structured H3 prompt, not a one-line caption.

**T2V / FL2VA**

```text
integrated_multimodal_description: [Shot 1] ...
overall_soundscape: ...
non_diegetic_music: N/A
```

FL2VA adds an alignment line before the description:

```text
How the reference pictures align with the target video — Picture 1 (from Shot 1) aligns with the
0.00-second mark; Picture 2 aligns with the 5.17-second mark.
```

**Ref2VA** uses the reference structure:

```text
subject_definitions:
<Subject 1> is ... from Picture 1; retain ...
<Subject 2> is ... from Picture 1; use only as ...
summary:
[reference generation] ...
retention_analysis:
<Subject 1> (appears in [Shot 1]): fully_preserved - ...
<Subject 2> (appears in [Shot 1]): weak_reference - ...
detailed_description:
[Shot 1] ...
overall_soundscape: ...
non_diegetic_music: N/A
```

Retention markers: `fully_preserved`, `partially_preserved`, `attribute_transfer`, `weak_reference`,
`removed`. Audio markers: `fully_copy`, `partially_copy`, `reference`, `weak_reference`. Labels are
`<Subject N>`, `<Picture N>`, `<Video N>`, `<Audio N>`; dialogue uses `<d>[Chinese] ...</d>`.

Practical prompt notes: camera amplitude is advisory, so give a stopping point; “wide shot” alone
renders as medium, so describe the subject small in a large space; fine contact constraints are
unreliable; short text on props survives camera moves.

## Output and save prefixes

- `COMFY_WORKFLOWS/PIKA_T2V`
- `COMFY_WORKFLOWS/PIKA_FL2VA`
- `COMFY_WORKFLOWS/PIKA_REF2VA`

Collect by `prompt_id` into `work/outputs/<project>/<date>/<prompt_id>/`. Do not change the prefix.

## Performance and quality

Reference measurements on a 24 GB RTX 4090, 736×416, 124 frames:

| Pipeline | NFE | Warm wall |
| - | - | - |
| fastvideo stack | 8 | ~22.5 s |
| Pika H3 Flex | 6 | ~23.4 s |
| native H3 | 20 | ~57–86 s |

Pika is **not faster** than the fastvideo stack; the rank-128 adapter's per-step cost offsets the
2-step saving. It is ~2.5–3.5× faster than undistilled 20-step H3. Its advantage is quality: in
same-seed street A/B tests it was sharper on two of three scenes and dramatically better on Japanese
signage and night-scene coherence; the fastvideo stack held prompt literalism better in the daytime
market scene.

## Limits

- Local ceiling is **768p**; 1080p/2K/4K are hosted-API only. For 2K, keep the existing latent-upscale
  chain; Pika is not a direct 2K generator.
- 24 fps native; no RIFE. A 48 fps deliverable needs the usual ×2 step.
- The adapter is trained for 5–15 s on the `17n+5` frame grid; 124 frames is 5.17 s.
- Licence: MiniMax H3 Community License; review territorial/commercial terms before client delivery.
- The public graphs are statically validated with placeholder media, not rendered after sanitization.

## Verify before production

```bash
python scripts/validate_workflow.py workflows/minimaxh3/api/pika-h3-t2v.api.json \
  --url http://<host>:<port>
comfy run --workflow workflows/minimaxh3/api/pika-h3-t2v.api.json --print-prompt \
  --host <host> --port <port>
```

Check `/object_info/UNETLoader` and `/object_info/LoraLoaderModelOnly` include the two bases and the
two adapters. If only a rank-56 adapter is installed, install the official 1.96 GB file instead.

## Public sources

- Adapters: <https://huggingface.co/Comfy-Org/MiniMax-H3/tree/main/loras>
- Bases: <https://huggingface.co/Comfy-Org/MiniMax-H3/tree/main/diffusion_models>
- Pika project and prompt guide: <https://github.com/Pika-Labs/Pika-H3-Flex>
- Comfy tutorial: <https://docs.comfy.org/tutorials/video/pika/pika-h3-flex>
