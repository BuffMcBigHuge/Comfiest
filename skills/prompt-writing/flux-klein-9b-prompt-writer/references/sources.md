# FLUX.2 [klein] 9B prompt sources

## Primary (vendor)

- klein quick-start and prompting tips: https://help.bfl.ai/articles/7592221790-how-do-i-generate-quickly-with-flux-2-klein
  - 4B vs 9B table, VRAM, licences, multi-reference up to 4, hex codes, resolution range, and the three headline tips: narrative prompting, be specific about lighting/composition/style, include context.
  - Also states plainly what klein does NOT support: prompt upsampling, grounding search, more than 4 references.
- FLUX.2 text-to-image docs: https://docs.bfl.ai/flux_2/flux2_text_to_image
  - Subject plus action plus style plus context ordering, prompt length bands (10 to 30 words quick concept, 30 to 80 ideal, 80+ complex), hex handling, quoted text rendering, JSON structured prompting, preview vs pinned endpoints and KV caching.
- Family README: https://github.com/black-forest-labs/flux2/blob/main/README.md (variant matrix and licences).

## Secondary

- https://fuser.studio/articles/flux-2-prompt-guide : wording order, hex tied to one object, no negative prompt, multi-reference role statement, text rendering recipe, variant selection.
- https://github.com/nodetool-ai/nodetool/blob/main/packages/system-skills/flux-2-klein-prompting/SKILL.md : distilled vs base routes, guidance and step guidance, the five common mistakes, the one-variable iteration loop.
- https://www.earngenix.com/workflows/flux2-klein-image-comfyui : Qwen text encoder means natural language, 4B distilled wants exactly 4 steps, 9B base 20 to 30 steps.

## Notes

- FLUX.3 Image Klein exists as of Oct 2026 and has its own prompt upsampler. Do not mix its rules (bounding-box layout tables) into a FLUX.2 klein prompt.
- The `-preview` endpoints are the ones BFL recommends for best quality; the pinned ones exist for reproducibility.
