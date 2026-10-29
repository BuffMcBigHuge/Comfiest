# Krea 2 prompt sources

## Primary (vendor)

- Official prompting doc: https://github.com/krea-ai/krea-2/blob/main/docs/prompting.md
  - Positions: natural language prompts, long detailed prompts yield best results, quotes around words to render, minimal prompt engineering still works.
  - Ships 18 sample prompts at 2K on Turbo; they are the best calibration for output length and register.
- Official expansion system prompt: https://github.com/krea-ai/krea-2/blob/main/docs/expansion.txt
  - Nine numbered rules: faithfulness first, practical T2I structure, style planning internal, quote requested text, avoid over-specification, one paragraph, respect existing detail, respect the human form, preserve user medium.
- ComfyUI workflow doc: https://docs.comfy.org/tutorials/image/krea/krea-2
  - RAW 52 steps vs Turbo 8 steps, 1K to 2K via megapixels, `prompt_enhance` toggle, style reference workflow with 1 to 2 images, style LoRA selector, Qwen3-VL 4B text encoder, `qwen_image_vae`.
- Technical report: https://www.krea.ai/blog/krea-2-technical-report

## Secondary (independent guides, use for craft not for facts)

- https://fal.ai/learn/tools/krea-2-prompting-guide : model split and example prompts.
- https://krea2.co/blog/krea-2-prompt-guide : prompt stack (subject, context, composition, light, style, crop), camera cheat sheet, lighting as the primary quality lever.
- https://www.avocadoai.co/blog/listicle/krea-v2-image-generation-guide-2026 : creativity setting, texture words over color words, keep negatives minimal, weak on in-image text. Treat the text claim as low confidence; Krea's own doc says quotes help.

## Community signal

- r/StableDiffusion "Krea 2 king of styles" https://www.reddit.com/r/StableDiffusion/comments/1xfeonr/ : style breadth is the model's reputation.
- r/StableDiffusion "I've trained 100+ Krea 2 character LoRAs" https://www.reddit.com/r/StableDiffusion/comments/1x0imbp/ : likeness depends on training data, not prompt wording.
- r/StableDiffusion Krea2 Turbo 2-step distill LoRA https://www.reddit.com/r/StableDiffusion/comments/1x2s9sd/ : 2-step inference exists, expect quality loss.
- X, @influencer_seo posts Krea 2 samples with full prompts; useful for length calibration.
