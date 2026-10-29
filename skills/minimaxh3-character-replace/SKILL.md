---
name: minimaxh3-character-replace
description: Character-replacement workflows built on MiniMax H3 in Comfiest — SAM3 segmentation, a depth-guided motion guide, forced source audio, and three background modes.
---

# Character Replacement with MiniMax H3

Operating rules live in `../SKILL.md`; the H3 family guide is in `../minimaxh3/SKILL.md`. Workflow
files live under `../../workflows/minimaxh3/api/`.

Three API-first workflows that replace the performer in a source video with a different character while preserving the source motion, timing, and audio.

## Files

| ID | API workflow | Inputs | Background source |
| - | - | - | - |
| `charreplace-keepbg` | `ref2video-minimax-charreplace-keepbg.api.json` | source video, character image | source video |
| `charreplace-charbg` | `ref2video-minimax-charreplace-charbg.api.json` | source video, character image | character image |
| `charreplace-refbg` | `ref2video-minimax-charreplace-refbg.api.json` | source video, character image, background image | separate background image |

All three default to **1.0 MP, 124 frames (~5.17 s), 48 fps after RIFE**.

## Stable input names

| Slot | Filename | Used by |
| - | - | - |
| source video | `example.mp4` | all |
| character image | `example.png` | all |
| background image | `example.png` | `charreplace-refbg` only |

Upload the same set to every target that may run the workflow. Every image slot defaults to
`example.png` (use one image or replace individual slots) and the video slot defaults to
`example.mp4`. `VHS_LoadVideo` reads from the ComfyUI `input/` directory; if the filename is not in its
combo list, upload it first.

## How it works

The core trick is a **depth-guided motion guide** plus an optional character-swap LoRA:

```text
VHS_LoadVideo (24 fps, 124 frames)
  -> SAM3_Detect (target: "person")
  -> DepthAnythingTensorrt (depth_anything_v2_vitl-fp16.engine)
  -> ImageCompositeMasked
       keepbg: destination = source frame (original background)
       charbg/refbg: destination = neutral grey EmptyImage
       source = depth frame, mask = SAM3 person mask
  -> ImageScaleToTotalPixels (0.15 MP)
  -> MiniMaxH3ReferenceToVideo.ref_videos.ref_video_0
```

- **Why depth?** The model copies motion from the reference video. A depth map suppresses the source performer's identity and clothing and keeps only geometry/pose, so the target character image drives identity. This tests better than the reference's color inversion. Only the person is replaced by depth; the background is left intact for `keepbg`.
- **Character image** goes to `ref_images.ref_image_0` (`LoadImage` #284).
- **Background image** goes to `ref_images.ref_image_1` (`LoadImage` #2011) for `refbg`.
- **Character-swap LoRA (optional; not shipped):** the original
  `minimax\h3_character_swap_v1.5.safetensors` at strength `1.0` was removed for the public release.
  It was inserted after the family's Power Lora Loader and before `H3AdaLNLoRAFix`. Add it in a scratch
  copy if you need stronger identity transfer; the sanitized graphs run without it.
- **Audio**: the source video's audio feeds both `ref_audios.ref_audio_0` and the forced-audio chain (`VAEEncodeAudio` → zero `SetLatentNoiseMask` → `LTXVConcatAVLatent` → sampler `latent_image`). The output audio matches the source; the mouth follows it.
- **RIFE** is active; output is 48 fps.

## Key settings

| Node | Setting |
| - | - |
| `VHS_LoadVideo` | `force_rate=24`, `frame_load_cap=124`, `skip_first_frames=0`, `select_every_nth=1` |
| `SAM3_Detect` | target text `person`, threshold `0.5`, refine iterations `2`, individual masks off |
| `DepthAnythingTensorrt` | `depth_anything_v2_vitl-fp16.engine` |
| `ImageScaleToTotalPixels` | `nearest-exact`, `0.15` MP, resolution steps `1` |
| `MiniMaxH3ReferenceToVideo` | `ref_image_size=match`, 1.0 MP, 124 frames |
| `LoraLoaderModelOnly` | optional character-swap LoRA (not shipped) |
| sampler | family fastvideo model, 3 steps, RIFE 2× → 48 fps |
| seeds | 9601 keepbg, 9602 charbg, 9603 refbg (change per take) |

## Prompt structure

Each workflow ships a prompt with the model's expected sections. Keep the section names:

```text
subject_definitions:
<Subject 1> is the red fox character from <Picture 1>...
[<Subject 2> is the environment from <Picture 2>...]   # refbg only

summary:
[video editing] Replace the performer in <Video 1> with <Subject 1>...

retention_analysis:
<Subject 1>: fully_preserved - identity, face, hair, body, clothing...
<Subject 2>: fully_preserved - location, background, set, lighting...
<Video 1>: structurally_preserved - camera, framing, actions, timing;
           discard the original performer's appearance.

detailed_description:
[Shot 1] Replace the original performer in <Video 1> entirely with <Subject 1>...
Keep the original framing, camera, background, lighting and grade...
Relight <Subject 1> to match the scene...
Do not copy the original performer's face, hair, clothing or body.

overall_soundscape:
Preserve the original audio and timing from <Video 1>.

non_diegetic_music:
Preserve original music.
```

Background rules:

- **keepbg**: `<Subject 2>` is the environment of `<Video 1>`; keep its location, background, objects, and lighting. `<Picture 1>` provides only `<Subject 1>`.
- **charbg**: `<Subject 1>` appears in the environment shown in `<Picture 1>`; use `<Video 1>` only for motion, timing, and camera; ignore the video background.
- **refbg**: `<Subject 2>` is the environment shown in `<Picture 2>`; use `<Video 1>` only for motion, timing, and camera; ignore the backgrounds of both `<Video 1>` and `<Picture 1>`.

## Run example

```js
const run = await tools["comfy-<host>-<port>"].run_workflow({
  workflow_path: "<repo>/workflows/minimaxh3/api/ref2video-minimax-charreplace-keepbg.api.json",
  wait: false,
});

const job = await tools["comfy-<host>-<port>"].job({
  action: "wait",
  prompt_id: run.prompt_id,
  timeout_seconds: 1800,
});
```

Run one job per target. Parallelize only across different targets. Leave the `VHS_VideoCombine` save
prefix untouched; collect the run by `prompt_id`.

## Tuning

- **Identity fidelity**: use a clean, front-facing character image with the full outfit visible. Try `ref_image_size=max` (slower) if identity drifts.
- **Motion detail**: raise the motion guide to `0.3–0.4` MP for hands/face; it is slower. `0.15` is the default and works for most shots.
- **Multiple people**: set the SAM3 target to `man:1`, `woman in red:1`, etc. In the reference UI, run the mask preview first; the target should be solid white.
- **Background drift**: `keepbg` needs the SAM3 mask to cover the performer cleanly. If the mask misses an arm/hair, the depth guide leaks and the background can warp. Try a higher threshold or a more specific SAM3 prompt.
- **Character image background**: `charbg` uses the character image's background; a busy or inconsistent background will be reproduced. Use `refbg` when you want a specific background that is not in the character image.
- **Length**: `frame_load_cap` and the R2V `length` must agree. 124 frames ≈ 5.17 s; 107 ≈ 4.5 s; 158 ≈ 6.5 s. Keep the source video at least that long.
- **Audio**: the forced-audio chain uses the source video's audio. If the source has no audio, replace the audio source with a `LoadAudio` node and update both `ref_audios.ref_audio_0` and the forced chain's `VAEEncodeAudio` input.

## Verification

The pre-sanitization versions of these workflows completed runs with a source clip and a separate
character image (with the optional swap LoRA installed). The public templates remove that LoRA; treat
the numbers below as historical reference, not a guarantee for the sanitized graphs:

- all outputs: 768×1376, 5.18 s, 48 fps
- output audio vs source: 0.9715 mel correlation
- output vs source frames: SSIM 0.48–0.54 (significant change, not a copy)
- no `freezedetect` or `blackdetect` events (real motion, no black gaps)
- SAM3 mask check: 18.8% white, bbox `209,365–589,1278`; mask sample and clips are recorded in the
  local run log and work tree, which are not shipped with the repository

Technical completion is not creative approval. The user watches and judges identity, background, and motion.

## UI construction

The reference UI (`character_replace_minimax.json`) shows the same nodes in UI form. The two background modes are the `3C · BACKGROUND FROM VIDEO` and `3C · BACKGROUND FROM IMAGE` groups; the optional character-swap LoRA, when used, sits in the `@loras` Power Lora Loader. The public workflows replace the reference's `ImageInvert` with `DepthAnythingTensorrt` using `depth_anything_v2_vitl-fp16.engine`; keep that substitution when rebuilding the UI. Use the API workflows as the runnable source, or open the reference UI and set the same slots/settings. Do not save over the shipped template files.
