# 04G_EXPANSION_SPEC — full-scale rerun and pre-drafting checks

Implement as scripts/04g_expansion.py, importing shared machinery. Same
population definition (1,622 formats), v2 labels, permutation scheme,
seeds, both tails + two-sided p. Two purposes: (1) remove the
100-instance cap and rerun the grid at full scale; (2) close four cheap
holes identified in the handoff before drafting.

Choices ratified with this spec:
(a) Uncapped = every instance of a population format that passes the
    existing preparation filters (OCR text present, length floor,
    watermark stripping), denoised by the 04F primary filter (k-NN
    typicality, fine-tuned space, global 10th percentile) applied to
    the FULL galleries. New BGE embeddings computed for added
    instances; visual centroids from stored chunks.
(b) Decision rule, fixed now: if every grid cell agrees with the capped
    analysis in sign and significance category, the paper reports the
    capped analysis as prespecified primary and the uncapped as the
    scale/robustness analysis; any flip goes to chat before drafting.
(c) "Pure-carrier" in §3 means: carries the target family and no other
    FUNCTION family (EXPRESS, EVALUATE, RESPOND, LABEL, DIRECT);
    affordance co-carriage (STRUCTURAL, CAPTION) is permitted, since
    affordance documentation describes mechanics, not competing
    function. Report carrier counts under both this and the strict
    (no co-carriage at all) definition; run contrasts only where the
    permissive definition leaves >= 30 carriers.

## 1. Uncapped grid

- Rebuild prepared sets with no cap; report the new funnel (instances
  per format distribution: min/median/max; total instance count before
  and after denoising).
- Recompute all format profiles (FW, POS, content centroid, visual
  centroid) from the denoised uncapped sets.
- Rerun: the full four-layer grid (omnibus + all families, all four
  measures), the completing regressions (04D §3), and the RESPOND
  when-clause contrast. Side-by-side table: capped vs uncapped effect
  and p for every cell.

## 2. Size-precision diagnostic

The reason the cap existed; quantify it rather than assume it away:
- Per-format split-half profile stability (FW and POS): correlation of
  profiles built from random halves of the format's instances, vs
  instance count. Shows how precision scales with size.
- Pair-level: mean similarity as a function of min(pair instance
  counts), bins of equal pair count, all three text measures. Shows
  whether big-big pairs are inflated.
- Report whether the log-size regression terms absorb the gradient
  (compare family coefficients with and without size terms, uncapped).

## 3. Pre-drafting checks (handoff §8 items 3, 4, 5)

- Co-carriage: the 7x7 format-level co-carriage matrix (counts and
  Jaccard). Pure-carrier one-vs-rest contrasts under (c) for EXPRESS,
  EVALUATE, LABEL on their binding layers, with permutation inference;
  side-by-side with the standard contrasts.
- When-clause Type control: format-level regression when_clause_rate ~
  RESPOND_carrier + Type dummies + log instance count; RESPOND
  coefficient under label permutations.
- Content-space anisotropy: mean-centre the centroid space (subtract
  the global mean centroid, re-normalise) and recompute the content
  one-vs-rest effects for EXPRESS, LABEL, RESPOND, CAPTION.
  Additionally, an instance-level content variant for EXPRESS and
  LABEL: mean cross-format instance-pair cosine on a seeded subsample
  (cap 50 instances per format for the subsample; this is a measure
  check, not the primary analysis). Report agreement with the centroid
  versions.

## 4. Outputs

outputs/blockg_report.md; outputs/blockg_grid.csv (capped vs uncapped,
every cell); outputs/blockg_checks.csv (§2-§3). Figure: capped-vs-
uncapped effect scatter. PIPELINE row; design-log entry: choices
(a)-(c) and the (b) decision rule. Commit, push, STOP. This is the
final analysis block before drafting unless a flip or a §3 surprise
sends something back to chat.

## Config additions

UNCAPPED = True path variants; PURE_CARRIER_MIN = 30;
INSTANCE_CONTENT_SUBSAMPLE = 50.
