# MOSS-Image prompt sources

## Primary (vendor)

- Repo: https://github.com/OpenMOSS/MOSS-Image
  - README layout section is the authority for the model-facing format: `summary` plus flat `items`, `bbox_format: "yxyx"` meaning `[y_min, x_min, y_max, x_max]`, `bbox_coord_space: "abs_centralized"` meaning pixels relative to canvas centre with -512 to +512 per axis on 1024x1024, and the rule `x' = x - W/2`, `y' = y - H/2` from ordinary top-left coordinates.
  - Also states: 4K token prompts, 5B backbone, strong text rendering, layout control, Base vs SFT difference, native ComfyUI support, day-0 SGLang and vLLM-Omni support.
  - `USERGUIDE.md` covers sampling settings, prompt examples, and LoRA guidance.
- Official prompt-enhancer skill: `skills/moss-image-prompt-enhancer/SKILL.md` in the same repo. Key rules taken from it:
  - draft Layout in `bbox_coord_space="abs"` and `bbox_format="xyxy"` with concrete `width`/`height`, then compile.
  - compiled output is one physical line, integer `abs_centralized` / `yxyx`, no canvas metadata.
  - dimensions must be positive multiples of 16; do not silently change explicit dimensions.
  - captions are cohesive prose with visible words quoted exactly, and must not carry coordinates.
  - tool instructions (JSON, bbox conversion) must not leak into image-description fields.
- Models: https://huggingface.co/OpenMOSS-Team/MOSS-Image-Base and https://huggingface.co/OpenMOSS-Team/MOSS-Image-SFT, plus ComfyUI weights at https://huggingface.co/Comfy-Org/MOSS-Image
- Technical report: https://arxiv.org/abs/2610.23374

## Operational

- ComfyUI workflow notes (layout prompt node, text encoder `qwen3.5_9b`, int8_convrot weights): https://comfyui-wiki.com/en/news/2026-10-16-moss-image
- Release discussion: https://www.reddit.com/r/LocalLLaMA/comments/1x7ey7i/openmoss_releases_mossimage/
- Prompt-thread color (community, low confidence): r/StableDiffusion "Moss prompting tips" https://www.reddit.com/r/StableDiffusion/comments/1x8e3dd/moss_prompting_tips/ and "Moss is the best base model we've gotten yet" https://www.reddit.com/r/StableDiffusion/comments/1x8ixsy/

## Corrections applied to the first draft of this guide

- Layout must be drafted in top-left pixel coordinates and converted, not hand-centred. The README shows only the compiled form, which is easy to imitate incorrectly.
- The compiled prompt carries no `width`/`height`; dimensions are passed to the image workflow separately, and the two must match.
- Caption and Layout are different artifacts. Adding bbox fields to a caption to make it look structured is wrong.
