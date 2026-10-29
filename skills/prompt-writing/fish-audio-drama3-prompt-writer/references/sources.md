# Fish Audio Drama 3 prompt sources

## Primary (vendor)

- Docs page: https://docs.fish.audio/features/text-to-speech/drama-3
  - Complete scoped tag list, verified: `<whisper>`, `<emphasis>`, `<soft>`, `<fast>`, `<slow>`, `<stress>`, `<forceful>`.
  - Square-bracket directions in any language, placed before the words they govern.
  - Language tag pairs for mid-line switching, marked experimental.
  - Phoneme tags `<|phoneme_start|>...<|phoneme_end|>` with CMU Arpabet for English (digit = stress level), pinyin for Chinese, romaji for Japanese.
  - Multi-speaker: `<|speaker:N|>` at the start of each turn, with one voice per speaker in a `reference_id` array. Character names in the readable script are not sent; the request carries speaker tokens.
  - Model header `model: drama-3`; a missing or misspelled header silently falls back to `s2.1-pro`.
- Launch post with worked tag examples: https://fish.audio/blog/fish-audio-drama-3/
- Product page (direction, sounds, pauses, scoped tags, multi-speaker): https://fish.audio/drama-3/

## Operational

- vLLM recipe: https://recipes.vllm.ai/fishaudio/drama-3 (tags are ordinary text, no special tokens; documented wordings work best; speaker tags supported).
- Model family repo: https://github.com/fishaudio/fish-speech
- Local ComfyUI execution (variants, speaker slot mapping, frame budget, VRAM): Hermes skill `fish-audio-drama3`.

## Notes and corrections

- The first draft of the Drama 3 guide listed five scoped tags. The docs list seven: `<soft>` and `<fast>` were missing.
- Phoneme tags and the experimental language tags were absent from that draft and are documented features.
- A readable script with character names is a working draft, not the request payload. Convert names to `<|speaker:N|>` before delivery unless the application assigns speakers itself.
