# MiniMax Music 3 prompt sources

## Primary (vendor)

- Model card: https://huggingface.co/MiniMaxAI/MiniMax-Music3
  - Two-input control, Structured Caption with the three sections, 5-minute songs, 5,000-token prompt limit, 9,000 acoustic frame limit, section tag list, the note that tag text on the same line is dropped.
- Repo: https://github.com/MiniMax-AI/MiniMax-Music3
  - `skills/music-caption-rewriter/SKILL.md` is the official rewrite contract: Music Brief, precedence order, timeline planning, exact output headings, 250 to 450 word default, validation checklist.
  - `references/genre-router.md` plus 1,000-plus templates under `templates/` and per-family indexes. Use the router before templates; do not scan the whole library.
  - `skills/README.md` explains the progressive-disclosure structure.
- Launch writeup: https://www.minimax.io/blog/minimax-music-3-0-next-generation-open-weights-production-ready-versatile-music-model (structured captions, global plus local LLM split, prompt enhancement system).
- Diffusers pipeline: https://huggingface.co/docs/diffusers/api/pipelines/minimax_music3 (44.1 kHz native vocoder output, tag-per-line rule, guidance 1.7, 25 frames per second of audio).
- ComfyUI tutorial: https://docs.comfy.org/tutorials/audio/minimax/minimax-music-3 (three-section prompting tip, section tags, `max_duration`, `tiled_decode`).
- Demo gallery with 26 worked captions across 11 genres: https://minimax-ai.github.io/music3-demo/

## Secondary

- https://fal.ai/models/minimax/music-3/llms.txt : API fields, `duration` default 60 with a 300 s cap, guidance and step defaults.
- https://github.com/UgurInanc12/minimax-music3-prompt-writing/blob/main/references/prompting-guide-full.md : community restatement of the caption rules, pre-flight checklist, conflict-priority order.

## Community

- X, @niklaslenz_ai ran a full rap music video on Music 3: 60 s of beat and vocals in 45 s, best of 3 takes. Useful for expectation setting, not for prompt wording.
- No substantive prompt-technique thread on r/comfyui or r/AI_Music as of Oct 2026. Reddit discussion is tooling, not prompting.
