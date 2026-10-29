# YuE2 prompt sources

## Primary (vendor / official)

- Repo: https://github.com/multimodal-art-projection/YuE
  - `skills/yue2-music/SKILL.md` is an official agent skill for YuE2: workflow table, conditioning modes, cover workflow, editing invariants, delivery rules.
  - `skills/yue2-music/references/generation-and-covers.md` has the field list, mode table, and the explicit statement that there is no `reference_audio`, `phonemes`, `bpm`, or `negative_prompt` field.
  - `skills/yue2-music/assets/prompt.json` is the reference request: style line, tagged lyrics, `cot`, `seed`.
  - `skills/yue2-music/references/abc-editing.md` for score-level edits.
- ComfyUI tutorial: https://docs.comfy.org/tutorials/audio/yue2/yue2
  - Style field guidance (genre, vocals, language, tempo, instruments), section tag list, planning mode choice.
- Paper: https://arxiv.org/html/2609.33757v1 (ABC as the symbolic layer; headers carry tempo, meter, key).
- Civitai orchestration schema: https://developer.civitai.com/orchestration/reference/operations/InvokeYuE2StepTemplate (`maxDuration` default 120, max 360; `mode` enum; `steps` default 32).

## Secondary

- https://ordalin.com/guides/yue2-prompting-guide : style template, the "style tokens compete with song length" observation, section tag list, and the warning that generation can stop earlier than `maxDuration`.

## Community

- r/StableDiffusion "A Meta-Prompt for YuE2" https://www.reddit.com/r/StableDiffusion/comments/1wwjm6g/ : question-driven prompt builder, style line order, "always give a concrete BPM", no stage directions in lyrics, syllable splitting done in the ABC rather than the lyrics.
- r/StableDiffusion "YuE2 Cover is so much fun" https://www.reddit.com/r/StableDiffusion/comments/1ww3n18/ and "ACE-Step 1.0 + YuE2 = Win" https://www.reddit.com/r/StableDiffusion/comments/1wxog4s/ : cover workflow in practice.
- X, @s21walker reports YuE2 SongBench 6.96 across 17 settings. Vendor-adjacent, treat as directional.
