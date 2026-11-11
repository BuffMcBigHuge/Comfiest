---
name: minimax-h3-image-prompt-writer
description: Use when writing MiniMax-H3-Image prompts for text-to-image or reference-image editing.
---

# MiniMax-H3-Image prompt writer

Guidance for writing **MiniMax-H3-Image** text-to-image and reference-edit prompts. The model reads a
prompt as a **specification of the finished picture**, not as a wish: everything you want to see must
be stated as something visible, and placed.

Adapted from MiniMax's official H3Image prompt-writing guide
(<https://github.com/MiniMax-AI/MiniMax-H3-Image>) plus local test results. The vendor guide is the
authority on prompt grammar; this file adds the operational facts for Comfiest's graphs.

## When to use

- Writing a prompt from a short idea or a detailed brief.
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

## Output contract

Return exactly one finalized prompt: **one cohesive English paragraph**, usually 120 to 300 words. No
bullets, no JSON, no headings, no alternatives, no meta-commentary about the model.

Visible lettering keeps whatever language it is written in; the narration around it stays English.

- **Text-to-image:** organise the description naturally.
- **Editing:** one paragraph in the order *source definitions → target overview and relationships →
  changed or new details*. Do not print those stage names as headings.

Deliver the prompt, not an image. If the caller needs generation settings, give the aspect ratio
separately.

## Text-to-image

### Hold the brief as constraints

Treat named entities, counts, formulas, data, style, medium, direction and spatial relationships as
constraints, not suggestions. Keep meaningful qualifiers and exclusions. Keep a named product or system
distinct from the generic category it belongs to — and remember a named entity does not need a visible
label. When revising an existing prompt, change only the requested scope.

Add detail for a reason: a readable interaction, convincing material, depth, light, or information
hierarchy. Keep the requested medium and restraint — abstract art need not become photorealistic, and a
minimal logo need not acquire scenery. Concrete visual choices beat generic quality claims, invented
backstory, and extra principal subjects.

### Set the composition

Honour explicit canvas dimensions, orientation, panel layout and reading order. Separate the whole
image from an object, a depicted screen, or a single panel. State grid rows and columns explicitly; the
cell count does not determine the canvas ratio. Carousel pages, cards and slides are separate canvases
unless a combined overview or continuous composition is requested.

When geometry is unspecified, choose framing from the deliverable and the main content: a compact
subject can stay compact, a comparison needs room side by side, stacked information needs vertical
room. A style word like "cinematic" does not fix the canvas. Fix the composition before adding scenery,
and do not add content to justify a shape you prefer. Recommend an aspect ratio from that composition.

### Make the scene physically readable

Describe the subject's visible state or action, the viewpoint, the setting and meaningful light. Use a
single frozen moment unless a sequence is requested; in a sequence, show each distinct event and the
specified outcome through visible evidence, not mood alone.

Keep the scene's topology consistent: screen-left and screen-right, foreground and background, gaze and
movement. Camera-relative body orientation, the visible body surfaces, hands, support points and contact
must agree. Frame the requested interaction clearly without mirroring a layout or moving its
destination to suit a pose. Preserve the structure of courts, game grids, paths, stairs and rooms
unless the request changes it, and keep required ground markings and labels visible.

### Complete designed artifacts

For posters, cards, boards, packaging, UI, charts, dashboards, infographics, technical diagrams and
multi-panel composites, build a **finished information architecture** rather than a scene containing the
requested objects.

Plan the canvas in reading order as slots — header, subtitle, hero visual, left panel, right sidebar,
card row, diagram body, chart area, specification block, footer — and give each slot actual content:
a title, diagram, controls, labels, or copy. "Some icons" or "a paragraph of copy" does not complete a
design. When asked to author copy, write the real wording in the requested language, otherwise the
user's language; ordinary creative decisions do not need approval.

Include functional detail where it explains the artifact: UI controls and selected states; chart axes,
units, scales and legends; scientific labels, variable definitions and attached arrows; product
materials, construction and joints. Respect a minimal design rather than filling a checklist.

### Literal text

Put the exact wording in single or double quotation marks and say where it sits and how it is set:

> across the top of the frame the word "KYOTO" in deep indigo condensed serif, and directly beneath it
> a smaller line reads "AUTUMN 1936"

- Put lettering on its intended surface and preserve its language, capitalisation, punctuation,
  numbers, spelling and line order unless a transformation is requested.
- Supply complete new or transformed wording. Do not add text when text is prohibited.
- Say the language when it is not English.
- For Chinese text, use full-width spaces (U+3000) immediately before or after the Chinese run.
- If label colours are unspecified, ask for **one** neutral uniform style. Left open, the model assigns
  a different colour per label.
- State the order when order matters: `left to right`, `top to bottom`.
- Multi-line layouts come back **exact** — this model does not need short strings.

### Data and charts

Match data marks to the supplied values and scale. Retain the requested chart type and measurement
method. **Compute any derivable result yourself** — totals, differences, percentages — rather than
delegating arithmetic to the image model. Do not replace a requested data display with decorative
imagery.

Invent content freely for a fictional design, but never present invented real statistics, prices,
certifications or specifications as verified fact. Known ranges and trends are fine without fabricating
individual measurements or significance results.

For paired views such as plan/render or front/back, use one shared inventory and coordinate frame:
the same objects, counts and relationships in both. In a grid, specify cell contents in reading order
without forcing a rectangular layout onto a deliberately irregular arrangement.

### Resolve dependencies and finish

Resolve a generic template from the specific brief and its explicit constraints. If equally specific
requirements conflict, keep the compatible content and ask only when the conflict prevents a useful
prompt; do not silently repair factual data. A missing field should not discard the rest of a usable
design.

A named asset can stay a named reference without inventing its appearance or claiming it was inspected.
For an unseen source, describe only the stated transformation. Mention a necessary asset or data
dependency naturally inside the prompt; ask for it only when its unknown contents block the prompt.

Check the finished prompt against the brief: exact copy and qualifiers, required content and counts,
spatial bindings, values and data marks, labels and arrow endpoints, body and contact consistency, and
correspondence across views. Every requested region should contain inspectable content. Keep intentional
negative space and remove repetition.

## Editing

Write one continuous paragraph. Narration describes the **final state** — "the former location is
filled by continuous tabletop" — rather than issuing an editing command. Required literal wording may
itself contain imperatives.

### Inspect the sources

Separate what you observe in the references from the target you are describing; there is no observed
target. Ground identities, counts, colours, wording, data and spatial relationships in the supplied
images. Do not guess hidden parts, unreadable text, exact colour values or unfamiliar object
identities — use visible cues to locate uncertain objects. Read dense text at a readable scale and
recheck critical names, acronyms, values and dates without normalising unfamiliar spellings.

Keep uncertainty local: complete the supported content, preserve unreadable regions, and do not claim
their transcription or translation is complete. Ask only when the unknown information prevents a useful
interpretation of the main task.

### 1. Define the referenced content

Open with short, source-grounded definitions:

> The red cup at the left of `<Picture 1>` is `<Subject 1>`.

Keep `<Picture N>` in supplied image order and `<Subject N>` stable throughout. `@Picture 1` and `@图1`
both mean `<Picture 1>`. When one identity is supported by several images, cite each explicitly rather
than a range or "all references".

Choose a Subject for each scope that needs an independent relationship: an object, person, text block,
background, pose, composition, or transferable property. Do not force one Subject per image, and do not
number every incidental part. Unmentioned content stays stable; explicitly track a salient non-target
element when the change might affect or confuse it.

Define a property-only donor as a property, not as an object. New target-only content, and content
removed or replaced with no other use, get no Subject number — locate removals in the target overview.
A traceable text edit keeps its source Subject. If no source content remains, omit the definitions and
start with the target overview.

For each text or data scope, transcribe every clearly readable line, label, value and field exactly
once, including wording that will change. Preserve language, punctuation, capitalisation, grouping and
reading order. A coherent block or series can be one Subject. Do not guess obscured content, silently
correct source data, or treat unreadability as permission to delete it.

### 2. Describe the target and each relationship

Start the overview with "The target image" and state the principal result — a local edit or a new
reference-guided composition. Resolve the layout before judging preservation.

**Canvas.** Honour exact target geometry or crop; an explicit canvas selection overrides conflicting
generic orientation wording. Otherwise keep the edited base's canvas when its composition is retained.
Take framing from the base or the designated composition reference, never from a colour or identity
donor. Compute from original display dimensions, not resized or padded previews: widening to 150% with
unchanged height multiplies the aspect ratio by 1.5. Changing an object's size does not change the
canvas. Describe reframing and newly exposed regions when they matter. Panel counts and embedded
screens are not whole-canvas dimensions.

Give every defined Subject its own relationship, judged over the scope actually defined:

| Relationship | How to write it |
| - | - |
| Fully preserved | The standalone sentence `Exactly <Subject N> is fully preserved.` |
| Partially preserved | State that it is partially preserved, which categories remain, and which change |
| Attribute transfer | Name the property and the carrier: `<Subject 2> supplies the exact body colour transferred to <Subject 1>.` |
| Weak reference | Name the borrowed quality and what may vary: `<Subject 2> serves as a weak style reference for the new background, with freely adapted forms.` |

Full preservation covers the whole defined scope, including count, position, state, appearance and
role. Moving, rotating, duplicating, relighting or occluding an element is a change. A fully preserved
parent cannot contain an edited child — narrow the definition or mark it partially preserved. Judge all
target uses of a Subject together, including extra instances. New shadows and reflections count as
changes to the scopes they affect.

A donor property does not become partially preserved just because it is used elsewhere. Exact transfer
must match that property; a weak reference permits only the stated adaptation. For exact colours, reuse
the source property rather than guessing a hex value or substituting an approximate name, and honour
explicit user-provided values.

### 3. Complete the changed and new content

Develop the requested result into concrete visual detail: shape, materials, contact, depth, perspective,
light and layout as needed. A new environment or global style can need substantial description; a local
recolour should stay local. Preserve explicitly requested modes of depiction. Necessary integration with
neighbouring content must agree with that content's preservation relationship.

- Describe a removal through the resulting surface or empty space. Moving relocates an object; copying
  adds an instance. Keep those outcomes distinct.
- After full preservation, use only the bare Subject token as an anchor — do not re-caption its
  appearance or parts. For partial preservation, elaborate the changes without repeating retained
  appearance. For a transfer or weak reference, describe the quality on its target carrier without
  importing incidental donor properties.
- Simplifying surrounding copy does not authorise redesigning retained diagrams: keep their internal
  structure, labels and data unless targeted. Resizing or repositioning need not change their contents.
- Stop once the result is specified. If the overview and relationships already cover it, add no filler.

### Finish the actual wording

Give the complete resulting line or field for each text edit, not just the replacement word; omit
separate unchanged lines. For a translation, write the actual translation here and keep the original in
its definition. Preserve factual qualifiers, deadlines, quantities and scope when condensing.

Quote literal wording and preserve its own apostrophes; describe multi-line text inline in reading
order with its intended line placement. Only text meant for the image becomes visible lettering.
Complete separately requested prose too, with its outside-image destination explicit — do not turn it
into a sign, and do not ask the user to write copy they asked you to author.

### Check the edit

Verify source bindings and independent relationships, preservation of salient non-target elements,
transfer boundaries, complete target wording, counts, geometry and the requested depiction mode. The
final details should cover changes and additions without re-describing retained appearance.

## Aspect ratio and canvas

If you set the canvas yourself, state the size in the prompt only when it changes the composition
(panorama, poster, phone story). Sizes must be multiples of 32.

In Comfiest's graphs the canvas comes from the conditioning node's `width`/`height`
(`4.width` / `4.height`), not from the prompt: the reference is reframed into that aspect. Set those
two fields to change the canvas, and do not expect prompt wording to override them.

| Ratio | 16 MP size |
| - | - |
| 1:1 | 4096 × 4096 |
| 4:3 / 3:4 | 4736 × 3552 / 3552 × 4736 |
| 3:2 / 2:3 | 5024 × 3360 / 3360 × 5024 |
| 16:9 / 9:16 | 5472 × 3072 / 3072 × 5472 |
| 21:9 | 6272 × 2688 |

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
| Generic, empty image | short prompt, no placement | write the full caption, place every element |
| Sparse poster or card | scene description instead of an artifact | build slots, give each one content |
| Text wrong or missing | unquoted, unplaced | quote exactly, say where it sits |
| Wrong canvas | ratio left to the model | set width/height explicitly |
| Edit ignored | instruction phrasing, or too large a change | narrate the final state, define Subjects, shrink the change |
| Noisy edit | whole-scene re-imagining | keep the reference's scene, change one attribute |
| Rainbow labels | label colours unspecified | ask for one uniform marking style |
| Retained detail drifts | re-captioned a fully preserved Subject | use the bare token, describe only the change |

## Operator parameters

| Route | Size | Steps | Note |
| - | - | - | - |
| Draft | 2048² (4 MP) | 6 | 14–18 s, good for iteration |
| Production | 4096² (16 MP) | 6 | 25–31 s, the model's design point |
| Wide | 5472×3072 | 6 | 28 s |
| With expander | any | 6 | adds one 9B text pass |

`cfg` stays 1 and there is no negative prompt — put everything you want to avoid into the positive
description as a visible property.

Reference cost is real: each extra reference adds ~11 s and re-composes the image (1↔4 is 20.19 dB,
1↔8 is 9.87 dB at 256 px). Keep 1–2 references for identity plus a prop, 4 for a full composition, and
judge identity on the faces rather than pixel similarity.

## Examples

### Text-to-image

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

### Edit

References: `<Picture 1>` is a woman in a denim jacket on a wet city street at dusk. Query: `make the
jacket forest green, keep everything else the same`.

> The woman wearing the denim jacket in `<Picture 1>` is `<Subject 1>`. The wet street, parked cars and
> dusk skyline behind her in `<Picture 1>` are `<Subject 2>`. The target image is a local colour change
> on `<Subject 1>`. `<Subject 1>` is partially preserved; her pose, hair, face, hands, the jacket's cut,
> stitching, seams and folds, and her position and scale in frame all remain, while the denim's colour
> changes to a deep forest green. `<Subject 2>` is fully preserved. The new colour follows the jacket's
> existing shading, abrasion at the cuffs and highlights along the shoulders, so the denim still reads
> as worn indigo twill rather than painted fabric, and the reflections on the wet asphalt are unchanged.

## Sources

- MiniMax official H3Image prompt-writing guide (text-to-image and reference-edit), paraphrased above:
  <https://github.com/MiniMax-AI/MiniMax-H3-Image/tree/main/skills/h3-image-prompt-writing>
- ComfyUI H3-Image templates and local test results behind the timings, sizes and reference-cost
  figures.
