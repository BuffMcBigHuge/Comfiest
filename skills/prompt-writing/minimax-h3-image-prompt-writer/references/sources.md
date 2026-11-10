# MiniMax-H3-Image prompt sources

## Primary (vendor)

- Model card: https://huggingface.co/MiniMaxAI/MiniMax-H3-Image
  - 33.1B DiT, H3 architecture without the audio branch; 50 layers, hidden 5376, 56 heads, FFN 14336.
  - 6 NFEs, no CFG; ~16 MP native from 4096×4096 to 6272×2688 with no upscaler.
  - "expects a detailed English description of the whole image"; the hosted API runs H3-Image-Context-IR
    first to turn a short prompt into that description.
  - Editing: up to 16 references, `<Picture 1>` upwards, order defines the labels.
- Prompt expander card: https://huggingface.co/MiniMaxAI/MiniMax-H3-Image-PE
  - Ships `prompt/t2i/task_prompt.txt` and `system_prompt.txt` — the caption spec this skill encodes:
    subject identity, pose, contact, scale, environment, lighting, lens/medium, physical plausibility;
    content-map slots for communication artifacts; "required content must be visible, not implied";
    preserve exact text, counts and order; style comes after content.
  - Aspect-ratio policy: allowed set 1:1, 5:4, 4:3, 3:2, 16:9, 21:9, 4:5, 3:4, 2:3, 9:16, chosen from
    explicit canvas → requested deliverable → primary composition → minimal completion.
  - Request params: temperature 1.0, top_p 0.95, top_k 20, min_p 0, presence 0, repetition 1.0,
    max_tokens 4096, reasoning_effort xhigh, thinking true.
  - Output schema: `{expanded_caption, aspect_ratio}` for T2I; `{expanded_caption, target_aspect_ratio}`
    for editing.
- ComfyUI tutorial: https://docs.comfy.org/tutorials/image/minimax/minimax-h3-image
  - Two templates (T2I, edit), both need ComfyUI 0.45.0+ and template pack 0.11.104+.
  - T2I template ships at 4 MP "so low-VRAM machines do not run out of memory"; the expander is off by
    default there and on in the edit template.
  - Reference images need no preparation: the template rounds to 32 px; the node scales the vision copy
    to a 1024 px short edge and the VAE copy to a short edge clamped 1024–2048 px.
- Comfy-Org mirror: https://huggingface.co/Comfy-Org/MiniMax-H3-Image
  - int8_convrot 21 GB, w4a8 12.5 GB, bf16 40 GB; image VAE fp16 1.17 GB.

## Local test results (2026-11-10, RTX 4090 24 GB, ComfyUI 0.45.0)

- 4 MP 2048²: 13.8 s int8 / 17.9 s w4a8. 16 MP 4096²: 24.6 / 26.4 s. Wide 5472×3072: 27.7 s.
- Text: a five-line poster layout (`KYOTO` / `AUTUMN 1936` / `NOVEMBER 3 - 21` / `HIGASHIYAMA DISTRICT`
  / `OPEN DAILY 9 TO 5`) reproduced **exactly** at 4096². Strongest text result of any model tested in
  this bundle.
- int8 vs w4a8 at the same seed: 18.4 dB PSNR at 256 px — the composition itself diverges, so a fixed
  seed is not a controlled A/B across builds.
- Edit, local attribute change (charcoal → burgundy turtleneck): works, identity preserved, Laplacian
  364 vs 452 for T2I.
- Edit, whole-scene change (winter → summer): partial. Green 0.2 % → 10.0 %, warm 10.6 % → 22.1 %, but
  28 % still read as snow-white and Laplacian ~1192 (noisy). Rewriting the instruction as a description
  of the finished image changed nothing (green 9.0 % vs 10.0 %) — the reference anchor is the limit,
  not the phrasing.
- Edit, object replacement (`<Picture 1>` station, `<Picture 2>` red bicycle): works structurally.
  2752×1536, 27.7 s, Laplacian 2238; the object lands in the right place, with edit-path grit.
- Multi-reference identity, 1 / 4 / 8 refs: 20.4 / 47.1 / 102.3 s (about +11 s per reference). 1↔4 is
  20.19 dB and 1↔8 is 9.87 dB at 256 px — adding references re-composes, so judge identity on faces,
  not pixel similarity. Keep 1–2 refs for identity and a prop; 4 for a full composition.
- Expander on "a red fox in snow" produced: *"A solitary red fox stands upright in a field of fresh,
  undisturbed snow, its vibrant russet coat contrasting sharply with the surrounding white landscape…
  It occupies the lower half of the frame, while the background fades into a flat, wintry horizon under
  a soft, diffused sky."* The render followed it: brighter, more sky, subject lower in frame
  (Laplacian 1096 vs 718 for the raw short prompt).
- Full report: internal test notes, not shipped.

## Secondary

- No independent prompting guides found at the time of writing; the model is new. Treat community
  advice as unverified until it reproduces against the local stack.
