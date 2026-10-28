---
name: minimaxh3
description: MiniMax H3 video workflows in Comfiest — 14 reference-permutation variants, 8-second audio-video clips, resolution/timing, forced-audio lip-sync, and execution notes. Use for text-to-video, reference-to-video, or H3 lip-sync work.
---

# MiniMax H3 Family

> Operating rules live in `../SKILL.md`. Workflow JSON in `../../workflows/minimaxh3/` is a
> **template**: do not edit or re-save a shipped file for a run. Copy it to `../../work/scratch/`
> first. Scratch files and outputs go in `../../work/`.

MiniMax H3 generates an 8-second, 9:16 clip with synchronized generated audio from text and optional
picture/video/audio references. Every variant uses the same fastvideo stack, a single turbo LoRA,
3-step sampling, and RIFE to 48 fps.

## Files

- `../../workflows/minimaxh3/*.json` — UI-format workflows. Open these in ComfyUI.
- `../../workflows/minimaxh3/text2video-minimax-base.json` — the 97-node base/control surface. Use it
  only for slots the variants do not expose; it is not a production run file.
- `../../workflows/minimaxh3/api/*.api.json` — pre-slimmed API workflows for `run_workflow`.
- `../minimaxh3-character-replace/SKILL.md` — SAM3 + depth-guided motion guide + character-replacement
  guide.

## Variant matrix

Each UI file has a matching API mirror; the character-replacement workflows are API-first. File names
below are relative to `../../workflows/minimaxh3/`.

| ID | UI file | Inputs | Historical status |
| - | - | - | - |
| `t2v` | `text2video-minimax-t2v.json` | text only | verified (RIFE) |
| `1p` | `ref2video-minimax-1p.json` | `picture_1` | verified (production) |
| `2p` | `ref2video-minimax-2p.json` | `picture_1`, `picture_2` | input-verified |
| `1v` | `ref2video-minimax-1v.json` | `video_1` | input-verified |
| `1p1v` | `ref2video-minimax-1p1v.json` | `picture_1`, `video_1` | verified (RIFE) |
| `1p1a` | `ref2video-minimax-1p1a.json` | `picture_1`, `audio_1` | verified (production) |
| `1p1a-yue2` | `ref2video-minimax-1p1a-yue2.json` | `picture_1`, Yue2 audio | verified (RIFE, 2 s test) |
| `1v1a` | `ref2video-minimax-1v1a.json` | `video_1`, `audio_1` | generated |
| `1p1v1a` | `ref2video-minimax-1p1v1a.json` | `picture_1`, `video_1`, `audio_1` | generated |
| `2p1v` | `ref2video-minimax-2p1v.json` | `picture_1`, `picture_2`, `video_1` | generated |
| `2p1a` | `ref2video-minimax-2p1a.json` | `picture_1`, `picture_2`, `audio_1` | generated |
| `2p1v1a` | `ref2video-minimax-2p1v1a.json` | `picture_1`, `picture_2`, `video_1`, `audio_1` | generated |
| `1a-forced` | `ref2video-minimax-1a-forced.json` | `audio_1` + forced audio latent | verified (lip-sync) |
| `1p1a-forced` | `ref2video-minimax-1p1a-forced.json` | `picture_1`, `audio_1` + forced audio latent | verified (lip-sync) |

“Historical status” describes the configuration before sanitization. Run your own job before relying
on a variant.

**Forced-audio variants.** `1a-forced` and `1p1a-forced` replace the sampler's starting audio latent
with an encoded reference track (`LoadAudio` → `VAEEncodeAudio` → zero `SetLatentNoiseMask` →
`LTXVConcatAVLatent` → sampler `latent_image`) so the output audio follows the supplied track. They
default to 1.0 MP and 8 s. Save prefixes: `MINIMAX_1A_FORCED` and `MINIMAX_1P1A_FORCED`.

All variants use the original 8-second length (192 frames at 24 fps, then RIFE to 48 fps). Generate
with headroom and trim to the edit timeline; the requested duration can be quantized.

For the `*a` variants, `a` means an **audio reference**, not an audio-driven lip-sync track; the model
generates its own audio and the mouth follows that. The `*-forced` variants are the exception.

## Input slots

| Slot | Default filename | Loader |
| - | - | - |
| `picture_1` | `example.png` | `LoadImage` #284 |
| `picture_2` | `example.png` | `LoadImage` #285 |
| `video_1` | `example.mp4` | `LoadVideo` #293 → `GetVideoComponents` #294 |
| `audio_1` | `example.wav` | `LoadAudio` #290 |

`upload_file` preserves the local filename. Every image slot defaults to `example.png`, every video
slot to `example.mp4`, and every audio slot to `example.wav`. Upload the file once per type, or replace
individual slots with your own names.

`1a-forced` uses `audio_1` only; `1p1a-forced` uses `picture_1` + `audio_1`. Both read the audio through
the same `LoadAudio` #290 slot and force it into the sampler's audio latent.

## Running a variant

Use the API file, not the UI file, for MCP execution (resolve `<repo>` to the repository root):

```js
const run = await tools["comfy-<host>-<port>"].run_workflow({
  workflow_path: "<repo>/workflows/minimaxh3/api/ref2video-minimax-1p1v.api.json",
  wait: false,
});

const job = await tools["comfy-<host>-<port>"].job({
  action: "wait",
  prompt_id: run.prompt_id,
  timeout_seconds: 600,
});
```

Run one job per target. Parallel work is allowed only across different targets. Download the output URL
and size-check it; do not visually inspect it unless it is your own output and provenance is recorded.

To inspect a workflow, open the UI file in ComfyUI. The rgthree `Fast Groups Bypasser` nodes are
present for editing; the API files omit them. Do not save over the template file; work on a copy in
`../../work/scratch` if you need to change it.

## Resolution and timing

- The `Resolution Selector` is driven by the outer `megapixels` widget on the settings subgraph, not
  by the `width`/`height` widgets on the R2V node.
- `0.3` MP (default) = **416×736** for 9:16.
- `1.0` MP = **768×1376**. For a 768×1344 master, crop 16 px top and bottom. 1.0 MP is roughly three
  times heavier than 0.3 MP; a 24 GB card handles it with one job per target.
- `length` is a frame count at 24 fps, not seconds; it steps by 17 and the trained range is roughly
  124–362 frames. RIFE doubles the result to 48 fps.
- All variants produce an audio stream, including `1p` b-roll. Discard it in post and use the master
  track.

## Compatibility fixes applied to every variant

1. **RIFE is active on every variant.** `FL_RIFE` (#310) and the 48 fps target (#168) are active.
   The earlier `'dict' object has no attribute 'shape'` failure was not a RIFE incompatibility:
   `Final Images` was selecting a bypassed upscale latent, so RIFE received a latent dict instead of
   decoded images.
2. **Final switches fixed.** `Final Images` (#267) and `Final Audio` (#261) must select the active
   single-pass decoders (#259 / #258), not `any_01` from the bypassed upscale path. Disconnect
   `any_01`.
3. **UI-only nodes stripped from API.** `Fast Groups Bypasser (rgthree)` and `Label (rgthree)` are
   frontend helpers; the target rejects them with `missing_node_type`.

## Continuity techniques

- **First-frame conditioning:** activate `ImageResizeKJv2` (#274), `GetImageSize` (#276), and
  `MiniMaxH3AddGuide` (#272) with the keyframe in `LoadImage` (#284). The API graph then carries a
  `MiniMaxH3AddGuide` node fed by the keyframe and the model latent.
- **Reference tags:** use `<Picture i>`, `<Video k>`, and `<Audio j>` in the prompt to bind instructions
  to the numbered references; the node presents them in that order.
- **`ref_image_size`:** `max` uses the reference pipeline's 2048 px short edge (slower, stronger
  identity); `match` scales to the generation's pixel area.
- **Video-reference carry:** upload a previous clip as `video_1` and use `ref_videos.ref_video_0`.
  Disconnect `ref_video_audios.ref_video_audio_0` so the video contributes style/motion but not
  competing audio. Keep the character keyframe as `picture_1`.
- **Fixed seeds:** the `easy seed` node (#16) is fixed per shot. Reuse it when comparing variants;
  vary it per shot when you want different motion.
- **One job per target:** submit and wait on one target before sending the next job to that target.

## Lip-sync

- `ref_audios.ref_audio_N` is “standalone reference audio”; `ref_video_audios.ref_video_audio_N` is the
  soundtrack of a reference video. Both are reference conditioning, encoded as audio latents — not a
  forced output waveform.
- MiniMax H3 samples its own audio and video. The mouth follows the generated audio. Supplying a vocal
  segment does not guarantee it will rap those words; it may generate different words and timing.
- **Prompting it as the final soundtrack is not enough.** An A/B test with a TTS line and the same
  seed/keyframe showed the explicit “this IS the clip's audio” prompt changed the generated audio's
  content — it picked up a word from the source — but the output was still a new performance with
  different timing. Treat prompt wording as a content steer, not an audio passthrough.
- **Forced audio latent (working method).** Replace the generation's audio latent with the target
  audio before sampling:
  1. `MiniMaxH3ReferenceToVideo` LATENT (joint AV) → `LTXVSeparateAVLatent` → `video_latent`.
  2. `LoadAudio` → `VAEEncodeAudio` with the **audio VAE** → `audio_latent`.
  3. `SolidMask` value `0` (32×32) → `SetLatentNoiseMask` on the audio latent.
  4. `LTXVConcatAVLatent(video_latent, masked_audio_latent)` → the sampler's `latent_image`.
  The zero noise mask keeps the audio fixed; the sampler generates video against the real audio. The
  output audio matches the input and the mouth follows it. Keep `MiniMaxH3AddGuide` on the model's
  original AV latent for first-frame conditioning; only the sampler's starting latent is replaced.
  This is the Endless MiniMax H3 `Use Custom Audio` technique. It works with music/vocal segments, not
  just clean speech.
- Apply the forced latent per performance shot, with the exact audio segment and a clip length at
  least as long as the segment. `LTXVConcatAVLatent` trims or zero-pads the audio to the video length.
- Audio-driven gallery workflows (LTX-2.3 Image Audio to Video, Wan2.2-S2V, InfiniteTalk, HuMo) and
  dedicated lip-sync passes (Wav2Lip, LatentSync) remain alternatives.
- The audio-reference variants (`1p1a`, `1p1a-yue2`, `1v1a`, `1p1v1a`, `2p1a`, `2p1v1a`) are not
  lip-sync variants by themselves; use `1a-forced` or `1p1a-forced` for the forced-audio chain. A
  lip-sync pass works best on frontal close/medium shots; wide and profile shots may not have enough
  face detail.

## Character replacement (API-first)

Three API workflows replace the performer in a source video with a different character. They combine
SAM3 person segmentation, a depth-guided motion guide (`DepthAnythingTensorrt` with
`depth_anything_v2_vitl-fp16.engine`), and the forced source audio. Full instructions:
`../minimaxh3-character-replace/SKILL.md`.

The original character-swap LoRA (`h3_character_swap_v1.5`) was removed for the public release. The
graphs keep the segmentation, depth guide, and forced-audio chain; add the LoRA in a scratch copy if
you need its stronger identity transfer. Sanitized outputs are untested.

| ID | API file | Inputs | Background |
| - | - | - | - |
| `charreplace-keepbg` | `api/ref2video-minimax-charreplace-keepbg.api.json` | source video, character image | source video |
| `charreplace-charbg` | `api/ref2video-minimax-charreplace-charbg.api.json` | source video, character image | character image |
| `charreplace-refbg` | `api/ref2video-minimax-charreplace-refbg.api.json` | source video, character image, background image | separate background image |

Stable inputs: `example.mp4`, `example.png`, and for `refbg`
`example.png`. The workflows default to 1.0 MP, 124 frames (~5.17 s), and 48 fps after
RIFE. The output audio is forced from the source video.

## Model / LoRA stack

- UNET: `minimax\minimax_h3_fastvideo_vsa_datafree_1300step_4step_int8_convrot.safetensors`
- CLIP: `qwen3vl_32b_minimax_h3_int8_convrot.safetensors`
- Video VAE: `minimax\minimax_h3_video_vae_fp16.safetensors`
- Audio VAE: `minimax\minimax_h3_audio_vae_fp32.safetensors`

Active LoRA (same preset in every UI variant and API mirror):

| LoRA | Strength |
| - | - |
| `minimax\minimax_h3_fl2v_turbo_4step_v1.0_768p_comfyui_bf16.safetensors` | 0.8 |

`Power Lora Loader #21` keeps one slot. The bypassed `LoraLoaderModelOnly` node holds the same turbo
LoRA for reference. Verify the models and LoRA on each target with `/models/<folder>` and
`/object_info` before a run.

## Verification

The repository does not ship a verification manifest. The public templates were conversion-validated
against a reference target but not executed end-to-end. Technical completion is not creative approval;
the user judges the result.

## Runtime notes

- Video generation is heavy; submit with `wait: false` and poll `job(action="wait")`.
- If `job(action="wait")` returns a tool-level error, the server job may still be running. Poll
  `/history/<prompt_id>` and `/queue` directly; `status_str: "success"` is the completion signal.
- RIFE is mandatory in this family; do not bypass `FL_RIFE` or the 48 fps target.
- Intercut generated clips with b-roll and use a consistent grade in post.
