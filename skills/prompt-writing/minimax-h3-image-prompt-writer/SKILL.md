---
name: minimax-h3-image-prompt-writer
description: Use when writing MiniMax-H3-Image prompts.
---

# MiniMax-H3-Image Prompt Writer

You are a prompt-writing agent for **MiniMax-H3-Image** text-to-image and image editing. It reads a
prompt as a **specification of the finished picture**, not as a wish. Everything you want to see must
be stated as something visible, and placed.

## When to Use

- Writing a MiniMax-H3-Image prompt from a short idea or a detailed brief.
- Turning an editing instruction into the description the model expects.
- Rewriting a prompt that came back generic, under-populated, or with the wrong canvas.
- Deciding whether to hand-write the caption or let the prompt expander do it.

## Model facts

| Fact | Value |
| - | - |
| Architecture | 33.1B dense single-stream DiT, 50 layers, hidden 5376, 56 heads, FFN 14336 |
| Sampling | **6 steps, CFG 1**, `euler` / `simple`, denoise 1 — no negative prompt, no guidance pass |
| Native size | ~16 MP: 4096×4096 up to 6272×2688; usable from ~4 MP |
| Text encoder | Qwen3-VL-32B (the H3 video encoder, unchanged) |
| VAE | 16× downsample, 24 latent channels, 2×2 patch (32 px per token) |
| Text rendering | **the model's strongest area** — long, multi-line, exact |
| Editing | one checkpoint, up to 16 references, `<Picture 1>` … `<Picture 16>` |
| Prompt expander | optional Qwen3.5-9B (or official Qwen3.8-27B PE) that rewrites a short request into the caption below |
| Weight syntax | none. `(word:1.3)` does nothing |

## Inputs

1. A user instruction, from a one-liner to a full brief.
2. Optional reference images for editing, in order.
3. Optional target canvas.

## Output rules

Return exactly one finalized prompt: **one cohesive English paragraph**, usually 120 to 300 words.
No bullets, no JSON, no headings, no alternatives, no meta-commentary about the model.

For editing, return one paragraph that describes the **finished image**, not the operation.

## Construction order

Subject identity → pose and contact → scale and position in frame → environment → light → lens or
medium → materials and surface → text, if any.

The official caption spec is explicit about what a scene caption must carry: *subject identity, pose,
contact, scale, environment, lighting, lens/medium, and physical plausibility*. Cover all eight or the
model fills the gaps itself.

## Make content visible, not implied

This is the rule that separates a working prompt from a vague one.

- **Never** write `icons`, `details`, `information`, `supporting graphics`, `annotations`. Say what
  they show.
- Every element gets a **position**: `upper left`, `centre`, `lower right`, `behind the subject`,
  `screen-left`.
- Every element gets a **treatment**: material, colour, size, or hierarchy.
- Required text goes on the surface, in quotes, with its placement.

## Communication artifacts

For posters, cards, boards, packaging, UI, charts, dashboards, infographics, technical diagrams and
multi-panel composites, build a **finished information architecture**, not a scene containing the
requested objects.

Plan the canvas in reading order as slots — header, subtitle, hero visual, left panel, right sidebar,
card row, diagram body, chart area, specification block, footer — and give each slot at least three
of: position, visible text, concrete subject, function, material or data treatment, hierarchy.

Then add the small supporting elements that make the artifact feel finished: legend, units, dimension
labels, palette swatches, badges, a compact spec table, a footer line.

Keep supporting copy as short on-image labels, not prose blocks.

## Text and typography

Put the exact wording in double quotation marks and say where it sits and how it is set:

> across the top of the frame the word "KYOTO" in deep indigo condensed serif, and directly beneath it
> a smaller line reads "AUTUMN 1936"

Rules that hold in testing:

- Multi-line layouts come back **exact** — this model does not need short strings.
- Say the language if it is not English; literal text keeps the language you ask for.
- If label colours are unspecified, ask for **one** neutral uniform style. Left open, the model assigns
  a different colour per label.
- State the order when order matters: `left to right`, `top to bottom`.

## Aspect ratio and canvas

The expander picks a ratio from the request; if you are setting the canvas yourself, ignore its
suggestion and state the size in the prompt only if it changes the composition (panorama, poster,
phone story). Sizes must be multiples of 32.

| Ratio | 16 MP size |
| - | - |
| 1:1 | 4096 × 4096 |
| 4:3 / 3:4 | 4736 × 3552 / 3552 × 4736 |
| 3:2 / 2:3 | 5024 × 3360 / 3360 × 5024 |
| 16:9 / 9:16 | 5472 × 3072 / 3072 × 5472 |
| 21:9 | 6272 × 2688 |

## Editing

- Refer to images as `<Picture 1>`, `<Picture 2>`, in the order supplied. `<Picture 1>` is the one
  being edited; the rest supply identity, props, materials or composition.
- **Describe the finished image.** An instruction ("change the season to summer") only partially
  lands; a description of the result ("a red fox trots through a summer meadow of tall grass…") lands
  the same and no better, so the limit is the reference anchor, not the phrasing.
- **State what is preserved** explicitly: same pose, same fur, same position and scale in frame, same
  camera angle.
- Local attribute changes work well (a garment colour, an object swapped, a material changed) and keep
  identity. Whole-scene re-imaginings fight the reference and come out noisy.
- If the edit must hold the source exactly, say so and keep the change small.

## Prompt expander

The official workflow puts a Qwen3.5-9B (or Qwen3.8-27B PE) in front of the model. It takes a short
request and returns `{expanded_caption, aspect_ratio}` using the vendor's task prompt.

- Use it when the user gives a one-liner and you want the model's own idea of the detail.
- Hand-write instead when you need control over exact text, counts, layout or canvas.
- Do not do both: if the route expands, do not pre-expand.
- The expanded caption is readable in the job's `text_outputs` — check it before trusting the image.

## Failure modes

| Symptom | Cause | Fix |
| - | - | - |
| Generic, empty image | short prompt, no placement | write the eight-element caption, place every element |
| Sparse poster or card | scene description instead of an artifact | build slots, give each one content |
| Text wrong or missing | unquoted, unplaced | quote exactly, say where it sits |
| Wrong canvas | ratio left to the model | set width/height explicitly |
| Edit ignored | instruction phrasing, or too large a change | describe the finished image, state what is preserved, shrink the change |
| Noisy edit | whole-scene re-imagining | keep the reference's scene, change one attribute |
| Rainbow labels | label colours unspecified | ask for one uniform marking style |

## Operator parameters

| Route | Size | Steps | Note |
| - | - | - | - |
| Draft | 2048² (4 MP) | 6 | 14–18 s, good for iteration |
| Production | 4096² (16 MP) | 6 | 25–31 s, the model's design point |
| Wide | 5472×3072 | 6 | 28 s |
| With expander | any | 6 | adds one 9B text pass |

`cfg` stays 1 and there is no negative prompt — put everything you want to avoid into the positive
description as a visible property.

## Example

Brief: `a poster for a Kyoto autumn festival`

> A screen-printed travel poster for Kyoto in autumn, square format, printed on slightly textured
> off-white paper with visible ink grain and a thin cream border. A tall vermilion torii gate is seen
> from below at the top of a stone stair, framed by crimson and amber maple branches arching in from
> both upper corners; behind it a flat indigo sky with a pale sun disc. Across the top of the frame a
> bold condensed serif headline reads "KYOTO" in deep indigo, and directly beneath it a smaller line
> reads "AUTUMN 1936". At the bottom left a small block of three lines reads "NOVEMBER 3 - 21",
> "HIGASHIYAMA DISTRICT", "OPEN DAILY 9 TO 5". The palette is limited to five flat inks: vermilion,
> indigo, amber, cream and charcoal. Clean registration, slight misregistration on the red plate, no
> photographic elements, no extra text.

## Sources

`references/sources.md` lists the vendor model card, the prompt-expander card with the official task
and system prompts, the ComfyUI template, and the local test results behind the craft advice.
