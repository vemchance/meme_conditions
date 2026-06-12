# 04D_BLOCKC_SPEC — the visual layer and the gallery-noise check

Implement as scripts/04d_block_c.py, importing the shared 04 functions.
Same population (canonical 1,622), v2 labels, permutation scheme,
N_PERMUTATIONS = 10,000, seeded, both tails + two-sided p throughout.
Scope is deliberately narrow per decision point B: the visual one-vs-rest,
the coherence-restriction robustness rerun, and one completing
regression. Nothing else.

Choices ratified with this spec:
(a) Visual embeddings are the BASE (non-fine-tuned) SigLIP vectors from
    the SemioMeme release. The fine-tuned model was trained to maximise
    same-format similarity and would contaminate both the between-format
    layer and the coherence measure. VERIFY before use that the local
    embedding chunks are the base vectors, not fine-tuned ones (check
    provenance metadata / regenerate from the base model for a 100-
    instance sample and compare if provenance is unclear); record the
    verification in the report. If the chunks turn out to be fine-tuned,
    STOP and raise in chat before computing anything.
(b) The visual layer uses exactly the 04 instance sample (the stripped,
    filtered, capped seeded set), so all three layers describe the same
    instances. Vision-only instances are excluded by construction;
    record this as a stated limitation, not a silent one.
(c) Per-format visual coherence = mean cosine of the format's instance
    embeddings to its own visual centroid. The robustness split is at
    the population median of coherence ("high-coherence" = above
    median).
(d) The coherence-restriction rerun covers ALL significant grid cells —
    both form measures AND content — not form only. Protecting only half
    the grid would be selective.

## 0. Registered predictions (fixed before running)

Confirmatory (one-sided):
- EXPRESS binds visually: one-vs-rest visual effect > 0 (emotion-face
  imagery recurs across expressive formats).
- RESPOND binds visually: one-vs-rest visual effect > 0 (reaction-image
  iconography).

Exploratory (two-sided, no registered direction): omnibus visual;
EVALUATE, LABEL, STRUCTURAL, CAPTION visual effects. The robustness
rerun (§2) is a check, not a hypothesis: no registered direction.

## 1. Visual layer

- Per format: visual centroid of its 04-sample instance embeddings under
  (a)/(b); L2-normalise instance vectors before averaging. Report
  per-format counts (must match the 04 capped counts).
- Pair visual similarity: centroid cosine over the same pair population.
- Tests: omnibus within-vs-between and per-family one-vs-rest on visual
  similarity, identical machinery. DIRECT descriptive.
- Output the completed family x layer grid: FW, POS, content, visual —
  effects and inference side by side (blockc_grid.csv supersedes
  blockb_grid.csv as the paper's central table; leave the B file
  untouched for provenance).
- Context statistics: Spearman of visual similarity with content
  similarity and with each form measure over all pairs (how coupled the
  third layer is at baseline).

## 2. Gallery-noise robustness (the owed check)

- Report the distribution of per-format coherence under (c): histogram,
  quartiles, coherence by family (descriptive) and by Type
  (descriptive; reaction and character types are the expected extremes).
- Restriction rerun: recompute every significant grid cell (EVALUATE
  form x2, LABEL form x2, LABEL content, EXPRESS content, CAPTION's
  negative cells) on the high-coherence half of formats only. Same
  permutation inference within the restricted population. Flag any cell
  whose within-pair count falls below 100; report effects side by side
  with the full-population values.
- Reading rule, recorded in advance: effects that hold or strengthen
  under restriction were diluted by gallery noise (full-population
  results conservative); effects that vanish are flagged as possible
  artefacts of mixed galleries and discussed in chat before drafting.

## 3. Completing regression (one model per protected cell)

MRQAP as in 04C §2, adding the visual term:
- form similarity ~ within_family + content_sim + visual_sim + same_type
  + log instance counts, for EVALUATE and LABEL (both form measures).
- content similarity ~ within_family + visual_sim + same_type + log
  instance counts, for EXPRESS and LABEL.
The within_family coefficient under label permutations is the statistic;
this is the strongest separability statement available (form binding net
of content AND visual similarity), and the symmetric protection for the
content cells.

## 4. Outputs

outputs/blockc_report.md; outputs/blockc_grid.csv; figures: completed
grid heatmap (four layers), coherence distribution, restricted-vs-full
effect comparison. PIPELINE row; design-log entry: choices (a)-(d) and
the §0 registrations. Commit, push, STOP. Decision point C — final
scope call and exhibits planning — happens in chat.

## Config additions

VISION_EMBEDDINGS_PATH (point at the base SigLIP chunks);
COHERENCE_SPLIT = "median"; MIN_PAIRS_FLAG = 100 (existing).
