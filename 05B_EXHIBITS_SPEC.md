# 05B_EXHIBITS_SPEC — qualitative material for the paper

Implement as scripts/05b_exhibits.py. Read-only over existing data and
04-prepared texts; no statistics, no new claims. Seeded throughout.

## 1. Per-family format tables

For each of the seven families (DIRECT included), a CSV of all
population carriers: format title, KYM entry id, Type, instance count
(prepared sample), all v2 clauses for the family (clause text, predicate,
comp_head), NSFW badge flag, and the format's similarity to the family
centroid on each layer (FW, POS, content, visual).

## 2. Shortlists with sample texts

Per family, eight formats: the four closest to the family centroid on
the layer where the family binds (EVALUATE/LABEL: POS; EXPRESS/RESPOND:
content; CAPTION/STRUCTURAL/DIRECT: content, as a neutral default), plus
four seeded-random carriers. For each shortlisted format: ten
seeded-random fill texts from the prepared sample (the post-stripping
text actually analysed), each marked SAFE / OFFENSIVE / UNCLEAR by a
simple flag pass (slur list + NSFW badge inheritance) so paper-safe
examples can be chosen in chat without re-reading raw data.

## 3. Cell illustrations

- EVALUATE: for the shortlist, question-mark-bearing fill texts (up to 5
  per format where present).
- RESPOND: when-clause fill texts (up to 5 per format where present).
- LABEL: fill texts illustrating the labelling construction.
- EXPRESS: the discrete-head groups (frustration, confusion,
  disappointment, ...): for each head with >= 5 formats, the format
  titles and three fill texts per format — content binding with form
  variety is the point these need to show.
- CAPTION: two high-heterogeneity carriers (lowest within-format form
  self-similarity among carriers) with ten texts each, illustrating
  anti-coherence.
- Copypasta ceiling: one copypasta format, ten texts, showing
  near-verbatim repetition.

## 4. Outputs

outputs/exhibits/: family_<NAME>.csv (§1), shortlists.md (§2 and §3,
human-readable, grouped by family, safety flags inline), exhibits_index.md
(one-page list of what's where). PIPELINE row; design-log entry. Commit,
push, STOP.

## Config additions

EXHIBIT_SHORTLIST_N = 8; EXHIBIT_TEXTS_PER_FORMAT = 10;
EXHIBIT_SLUR_LIST: use an established public list (e.g. the one already
in the repo's dependencies if present; otherwise record which list was
used). The flag pass is coarse by design — final selection happens in
chat.
