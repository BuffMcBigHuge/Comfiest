---
name: sam3
description: Native SAM3 masking for Comfiest — text-prompted image and video mattes with core ComfyUI nodes, prompt grammar, coverage checks, and alpha compositing.
---

# SAM3 — native detection and masking

Use this when you need a matte, not a full character-replacement graph. SAM3 takes an image or video
plus a short text target and returns a clean luma matte. All three graphs are API-first and use core
`comfy_extras.nodes_sam3`; no custom SAM3 node pack is needed.

```text
image/video -> SAM3_Detect (or SAM3_VideoTrack -> SAM3_TrackToMask)
            -> GrowMaskWithBlur -> MaskToImage -> matte
```

The video graphs use `ComfyUI-VideoHelperSuite`; the feather node is `GrowMaskWithBlur` from
`ComfyUI-KJNodes`. The SAM3 chain itself is core-only.

## Files

Files live in `../../workflows/sam3/api/` and are API format for `run_workflow`.

| File | Task | Input | Output |
| - | - | - | - |
| `sam3-mask-video.api.json` | per-frame detect + segment | one video | luma matte video |
| `sam3-mask-image.api.json` | per-image detect + segment | one image | matte PNG + inverted-background QA preview |
| `sam3-track-video.api.json` | SAM3 memory tracker | one video | luma matte video |

All three are small (7–10 nodes) and meant to be run as-is with one or two inputs changed. Do not add
them to the UI; open the JSON if you need to read it.

## Run it

```js
const run = await tools["comfy-<host>-<port>"].run_workflow({
  workflow_path: "<repo>/workflows/sam3/api/sam3-mask-video.api.json",
  wait: false
});
```

Then poll `/history/<prompt_id>` and collect the output. See
[`../workflow-development/SKILL.md`](../workflow-development/SKILL.md) for the full submit/poll/
collect loop.

Change the source and target in a **copy** under `work/scratch/`; never write back into `workflows/`.

| Address | Meaning | Public default |
| - | - | - |
| `10.video` (`sam3-mask-video`, `sam3-track-video`) | input video in the target's `input/` | `example.mp4` |
| `10.image` (`sam3-mask-image`) | input image in the target's `input/` | `example.png` |
| `12.text` | what to detect | `person` |

Stage assets in `work/uploads/<project>/` with the exact filename, then `upload_file` them to every
target that may run the job. `upload_file` preserves the filename. Check `VHS_LoadVideo`'s `video`
combo (or `/object_info/VHS_LoadVideo`) before assuming a target has the file.

## Choosing what SAM3 detects

`12.text` is a `CLIPTextEncode` feeding SAM3's text encoder. It is an open-vocabulary prompt with a
small grammar:

| Prompt | Result |
| - | - |
| `person` | the single most confident person |
| `man` / `woman` / `child` | narrows by apparent gender/age |
| `person:3` | up to 3 people, unioned into one matte |
| `dog, bicycle` | both categories, unioned into one matte |
| `red car` | attribute-steered; works when the attribute is visible |
| `woman in white sweater` | use when several similar subjects are present |

Rules from the tokenizer (`comfy/text_encoders/sam3_clip.py`):

- Commas split the prompt into **separate categories**. Each is detected independently, then unioned
  when `individual_masks=false`. Never put a comma inside one description.
- `:N` sets max detections for that category (`person:3`, `dog:2`). Default is **1** per category, so
  `person` returns only the top-scoring instance.
- The tokenizer caps at **32 tokens**. Keep prompts to a short noun phrase; long sentences are
  truncated and behave unpredictably.
- There is no text negative prompt. Use a more specific target, a higher `13.threshold`, or the
  tracker's `object_indices` to drop unwanted objects.

### Absent targets do not return empty

Measured on the same portrait, same graph, `refine_iterations=2`:

| Prompt | Coverage | What came back |
| - | - | - |
| `person` | 86.67% | the person — correct |
| `elephant` (absent) | 86.67% | still the person |
| `narrow prop` (absent) | 98.04% | the person plus a band of wall/hair |
| `man, narrow prop` | 98.04% | union poisoned by the absent category |

SAM3 is a *segmenter*: an unmatched prompt falls back to the salient foreground object or a broader
region rather than returning nothing. Two consequences:

1. **A nearly-full matte means the prompt is wrong**, not that the subject is large.
2. **Never stack a speculative category into the prompt** — one bad category floods the union. Test
   categories one at a time.

`refine_iterations` is not the cause: the absent prompt gave the same 98.04% at
`refine_iterations=0`.

## Knobs

| Address | Default | Effect |
| - | - | - |
| `13.threshold` | `0.5` | detection score gate. Raise to 0.6–0.7 to drop weak/background hits; lower to 0.3 if a real subject is missed |
| `13.refine_iterations` | `2` | SAM decoder passes on the detection crop; 0 is fastest and uses the raw detector mask |
| `13.individual_masks` | `false` | images only: `true` emits one mask per object (N PNGs). **Keep `false` for video** — on video it concatenates per-object masks into the frame batch, multiplying the frame count and breaking timing |
| `14.expand` | `2` | dilate the matte by N px; `0` for a hard matte |
| `14.blur_radius` | `4.0` | feather in px; `0` for a hard matte |
| `20.frame_rate` | `24.0` | **must match the source fps** or the matte drifts against the plate. The graph does not wire fps from the loader to the saver, so set it by hand |
| `13.detection_threshold` (track) | `0.5` | tracker re-detection gate |
| `13.max_objects` (track) | `4` | tracked object budget; initial masks count toward it |
| `13.detect_interval` (track) | `1` | run detection every N frames; higher is cheaper but drifts |
| `14.object_indices` (track) | `""` | `""` = all objects; `"0"`, `"0,2"` select tracked IDs |

## Outputs

- The matte is a **luma matte**: white subject on black, same size and frame count as the source.
- Video → `COMFY_WORKFLOWS/SAM3_MASK_*.mp4` (h264) or `SAM3_TRACK_MASK_*.mp4`; image → matte PNG plus
  a preview PNG where the subject stays normal and the background is inverted (a fast “did it grab
  the right thing” check).
- Retrieve with `fetch_outputs`, or the target's `/view` URL. See
  [`../workflow-development/SKILL.md`](../workflow-development/SKILL.md) for the direct URL pattern.

### Sanity-check coverage before using a matte

Mean luma of a 1×1 downscale equals the matte's white fraction:

```bash
ffmpeg -i SAM3_MASK_00001.mp4 -vf "format=gray,scale=1:1" -f rawvideo -pix_fmt gray - \
  | python -c "import sys;b=sys.stdin.buffer.read();print(f'{sum(b)/len(b)/255:.2%} over {len(b)} frames')"
```

Expect roughly the subject's screen area: ~16% for a full-height figure in 16:9, and anywhere from
~40% to ~87% for a tight portrait (the verified 768×1376 head-and-shoulders matte measured 86.67%).
Cross-check against the preview or a single extracted frame — the number alone cannot distinguish
“subject fills the frame” from “prompt grabbed everything”. Above ~95% on a normal shot, assume the
prompt is wrong.

## Alpha WebM (compositing contract)

The matte is not alpha video, but it converts cleanly:

```bash
ffmpeg -i PLATE.mp4 -i SAM3_MASK_00001.mp4 \
  -filter_complex "[1:v]format=gray[m];[0:v][m]alphamerge" \
  -c:v libvpx-vp9 -pix_fmt yuva420p -b:v 0 -crf 28 -row-mt 1 -an fg.webm
```

VP9 stores alpha in a side channel: `ffprobe` reports `pix_fmt=yuv420p` with `TAG:alpha_mode=1`, and
that tag — not the pix_fmt — is the proof alpha survived. Browsers decode it.

## Text behind subject

1. Run `sam3-mask-video.api.json` on the plate → matte.
2. Convert to alpha WebM with the command above.
3. In HTML, paint in this z-order: plate (`z-index: 0`, keeps audio), text (`z-index: 10`), alpha
   foreground (`z-index: 20`). Text is occluded by the subject with nothing baked into the plate.

## Verified runs

Public sanitization changed only the input placeholders, not the graph shape or the default `person`
target. Reference runs on a 24 GB RTX 4090, ComfyUI 0.43.0:

| Graph | Input | Prompt | Result | Coverage |
| - | - | - | - | - |
| `sam3-mask-video` | 1376×768, 48 fps, 383 f | `person` | `SAM3_MASK_00001.mp4`, ~7.98 s, ~150 s wall | 15.97% mean (10.2–24.3%) |
| `sam3-mask-image` | 768×1376 | `person` | `SAM3_MASK_IMG_00001_.png` + preview | 86.67% (subject fills frame) |
| `sam3-track-video` | 48-frame cap | `person` | `SAM3_TRACK_MASK_00001.mp4`, ~2.0 s | 8.96% mean |

The video matte was visually checked (clean silhouette) and round-tripped to a VP9 alpha WebM,
`alpha_mode=1`, against the source plate. The graph shape is unchanged in the public copy; the
placeholder inputs have not been rendered.

## Gotchas

- **`frame_rate` mismatch** is the most common silent failure: the matte plays at the wrong speed and
  desyncs from the plate once converted to alpha. Set `20.frame_rate` to the source fps.
- **Tracker vs per-frame**: the tracker is temporally steadier and cheaper on long clips, but it can
  latch onto a second bright object (two small false positives on a lit window in the verified run)
  and it holds RAM across frames. Use `object_indices` to drop them, or stay on `sam3-mask-video` for
  short clips.
- **Per-frame detect can flicker** on soft edges or motion blur. A light `14.blur_radius` hides it;
  heavier cases need the tracker or a post-pass.
- **Hair, smoke, thin props**: the matte is binary/feathered and stops at the silhouette. Thin smoke
  is not included, and hair edges need `ImageMatting` with a trimap for close-ups.
- **`individual_masks=true` on video** breaks timing.
- **Empty detection** returns an all-black matte, not an error (rare; unmatched prompts usually fall
  back to the salient object). The coverage check catches both failure directions.
- **`GrowMaskWithBlur` missing**: it is KJNodes. If a target lacks it, delete nodes `14`/`15` and wire
  `SAM3_Detect`/`SAM3_TrackToMask` straight to `MaskToImage`; the SAM3 chain is core-only.
- **Wrong source file**: `example.mp4` and `example.png` are placeholders. Upload a real asset under
  the exact filename before running.

## Requirements

- ComfyUI 0.43.0 or newer with core `comfy_extras.nodes_sam3` (`SAM3_Detect`, `SAM3_VideoTrack`,
  `SAM3_TrackToMask`). No custom SAM3 pack is needed.
- `models/checkpoints/sam3.1_multiplex_fp16.safetensors` from Comfy-Org `sam3.1`.
- `ComfyUI-VideoHelperSuite` for the video graphs; `ComfyUI-KJNodes` for `GrowMaskWithBlur`.
- A 24 GB-class GPU is ample; a 383-frame 1376×768 video matte took ~150 s on a 4090.
