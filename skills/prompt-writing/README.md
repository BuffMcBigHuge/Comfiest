# Prompt-writing skills

Use these before filling a workflow's prompt, caption, lyrics, or script field. They are written for
the model families in this repository and return a production-ready prompt rather than a keyword list.

| Family | Skill | Workflows |
| - | - | - |
| Krea 2 | [`krea2-prompt-writer`](krea2-prompt-writer/SKILL.md) | `text2image-krea.json`, `image2image-krea-edit.json` |
| Flux.2 Klein 9B | [`flux-klein-9b-prompt-writer`](flux-klein-9b-prompt-writer/SKILL.md) | `text2image-fluxklein.json`, `image2image-fluxklein.json` |
| MOSS-Image | [`moss-image-prompt-writer`](moss-image-prompt-writer/SKILL.md) | `text2image-moss.json` |
| YuE2 3B | [`yue2-prompt-writer`](yue2-prompt-writer/SKILL.md) | `text2music-yue2.json` |
| MiniMax Music 3 | [`minimax-music3-prompt-writer`](minimax-music3-prompt-writer/SKILL.md) | `text2music-minimaxmusic3.json` |
| Fish Audio Drama 3 | [`fish-audio-drama3-prompt-writer`](fish-audio-drama3-prompt-writer/SKILL.md) | `workflows/fishdrama3/*.json` |

## How to use them

1. Read the family's prompt-writing skill.
2. Write or expand the prompt in the skill's output format.
3. Put the result into the workflow's prompt/caption/lyrics field.
4. Keep the workflow's other settings unchanged; the prompt writer does not choose sampler or model
   settings.

These skills are guidance only. The workflow JSON remains the authority on model, steps, and save
prefix. For a new graph, follow [`../workflow-development/SKILL.md`](../workflow-development/SKILL.md).
