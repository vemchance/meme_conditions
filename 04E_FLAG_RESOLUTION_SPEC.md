# 04E_FLAG_RESOLUTION_SPEC — selection vs noise

Implement as scripts/04e_flag_resolution.py, importing the shared
machinery. Same population, labels, permutation scheme, seeds, both
tails + two-sided p. This block exists solely to discharge the §2 flag
from Block C under the pre-recorded reading rule; it adds no new claims.

Context recorded with this spec: choice (c) of 04D (visual coherence as
the gallery-noise proxy) is confounded with format modality —
text-anchored Types (catchphrase, copypasta, snowclone, slang) are
visually diverse by construction, so the population-median split removes
them rather than removing noise. The tests below separate the selection
story from the noise story.

Hypotheses fixed in advance:
- Selection (expected): EVALUATE/LABEL form effects concentrate in
  text-anchored / low-coherence formats; within image-anchored Type at
  fixed composition, coherence restriction does not eliminate them.
- Noise (flagged risk): effects attenuate under coherence restriction
  even within Type.

## 1. Composition on the record

- The coherence-by-Type table from Block C, read into this report, plus:
  share of each Type falling in the high-coherence half, and the Type
  distribution of EVALUATE-carrying and LABEL-carrying formats in the
  full vs high-coherence populations.

## 2. Within-Type coherence split (the deciding test)

- Population: image-macro-Type formats only (report n; if any other
  image-anchored Type exceeds 150 formats, run it as a companion,
  recorded as such).
- Median coherence split WITHIN this population; rerun EVALUATE and
  LABEL one-vs-rest form cells (FW, POS) on the high-coherence half and,
  for symmetry, the low-coherence half. Same label-permutation
  inference; flag cells under 100 within-pairs.
- Decision rule, fixed now: effects holding in the within-Type
  high-coherence half discharge the flag (attenuation = compositional);
  effects attenuating within Type as well are reported as a genuine
  robustness limitation in the paper, verbatim.

## 3. Low-coherence half (the positive selection check)

- EVALUATE and LABEL one-vs-rest form cells on the below-median
  coherence half of the full population (the complement of Block C §2).
  Strong effects here confirm the selection story affirmatively and
  license the interpretive sentence that register conventions
  concentrate in text-anchored formats.

## 4. Outputs

outputs/blocke_report.md (small); one figure: EVALUATE/LABEL form
effects across full / high-coherence / low-coherence / within-Type-high
/ within-Type-low, side by side. PIPELINE row; design-log entry
recording the (c) confound and the §2 decision rule. Commit, push,
STOP. Exhibits spec and drafting handoff follow in chat.

## Config additions

None. (Image-macro Type string as already normalised in 02; companion
Type threshold 150.)
