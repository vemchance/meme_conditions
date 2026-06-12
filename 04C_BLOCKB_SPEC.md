# 04C_BLOCKB_SPEC — the content layer

Implement as scripts/04c_block_b.py, importing the shared 04 functions.
Same population, v2 labels, permutation scheme, N_PERMUTATIONS = 10,000,
seeded throughout. Report both tails and two-sided p for every contrast
from the start (04B style). Resolve and record in the report whether the
canonical population count is 1,622 or 1,623 and why the two reports
differ.

Four choices ratified with this spec:
(a) Content embeddings are computed FRESH with a plain pretrained
    sentence-transformer: BAAI/bge-large-en-v1.5, used in symmetric
    similarity mode (NO query instruction prefix — that is for asymmetric
    retrieval only), embeddings L2-normalised, applied to exactly the
    04-prepared instance texts (stripped, filtered, capped seeded
    sample). Encode on GPU, batched; record model name, revision, and
    library versions in the report. The
    SemioMeme fine-tuned retrieval embeddings are NOT used: they were
    trained to maximise same-format similarity, which would make any
    format-level content control circular.
(b) Format content profile = mean of its instance embeddings (centroid);
    pair content similarity = cosine between centroids.
(c) The transparent separability check is decile stratification on content
    similarity (replacing zerotag, which §2 of Block A showed removes only
    6% of pairs and measures category/platform, not topic).
(d) The complement test is confirmatory for EXPRESS only; EVALUATE
    complements are reported descriptively (the poke-fun construction
    corrupts its comp_head field).

## 0. Registered predictions (fixed before running)

Confirmatory (one-sided where stated):
- EXPRESS binds content: one-vs-rest content effect > 0.
- EVALUATE binds content: one-vs-rest content effect > 0.
- EXPRESS complement-content correlation > 0 (§3).

Exploratory (two-sided, no registered direction):
- Omnibus content effect; LABEL, RESPOND, STRUCTURAL, CAPTION content
  effects. (Note for the record: LABEL plausibly binds form without
  binding content — the labelling construction is fixed while the
  labelled subject varies. A form-without-content cell would be a
  finding, not a failure.)

## 1. Content layer

- Per instance: embedding of its prepared text under (a).
- Per format: centroid under (b). Report per-format instance counts
  feeding centroids (should equal the 04 capped counts exactly).
- Pair content similarity: centroid cosine, computed for the same pair
  population as 04.
- Tests: omnibus within-vs-between and per-family one-vs-rest on content
  similarity, identical permutation machinery to the form layer. DIRECT
  descriptive as standing.
- Output the family x layer grid: every family's effect and p on FW, POS,
  and content side by side. This grid is the paper's central table.

## 2. Separability, redesigned

Does the form binding survive holding content fixed?

- Regression (MRQAP inference as in 04B §3): form similarity ~
  within_family + content_similarity + same_type + log instance counts,
  per family, both form measures. The within_family coefficient under
  label permutations is the headline control statistic for LABEL,
  EVALUATE, and CAPTION (the three significant form results).
- Transparent version under (c): split pairs into deciles of content
  similarity; within each decile, the one-vs-rest form effect; report the
  per-decile effects and the pooled within-decile estimate (weighted by
  pair count), inference by the same label permutations with the decile
  structure recomputed per permutation. Flag any decile x family cell
  with fewer than 100 within-pairs.
- Report the raw form-content relationship for context: Spearman of
  content similarity with each form measure over all pairs.

## 3. Complement test (EXPRESS confirmatory)

Preparation:
- EXPRESS clauses from gloss_clauses.csv (label_v2), restricted to
  population formats. Lowercase and lemmatise comp_head.
- Light-head stoplist (ratified; record in config): feeling, feelings,
  sense, emotion, emotions, way, manner, variety, kind, type, sort, form,
  thing, something. Clauses with stoplisted or missing heads drop out of
  this test only. Report coverage: population formats carrying EXPRESS
  with >= 1 usable head.
- Per format: the set of its usable EXPRESS heads (multi-head allowed).
- Head embeddings: same model as (a), applied to the bare head token.

Tests, over EXPRESS-EXPRESS within-pairs:
- Continuous (confirmatory): pair complement similarity = max cosine
  between the two formats' head embeddings. Spearman of complement
  similarity with content similarity. Inference: permute head sets across
  EXPRESS formats (seeded, 10,000), one-sided per §0, two-sided also
  reported.
- Discrete (readable companion): for exact lemmatised heads carried by
  >= 5 population formats (expected: frustration, confusion, disgust,
  approval, disappointment, anger, surprise, excitement...), same-head vs
  different-head contrast on content similarity, same permutation scheme.
  Report the qualifying heads and their format counts.
- Secondary, exploratory: the same continuous test against the two form
  measures (no registered direction).

EVALUATE (descriptive only): top lemmatised heads with counts; note the
poke-fun extraction issue in the report; the continuous correlation
reported without confirmatory status.

## 4. Outputs

outputs/blockb_report.md; outputs/blockb_grid.csv (family x layer effects
and inference; small); outputs/figures/ additions: the family x layer
grid heatmap, per-decile form-effect plot for LABEL and EVALUATE, the
EXPRESS complement scatter (complement similarity vs content similarity).
Update PIPELINE.md (04C row); append the design log: choices (a)-(d),
registered predictions as in §0, light-head stoplist. Commit, push, STOP.
Decision point B — the framing decision — happens in chat on these
results.

## Config additions

CONTENT_MODEL = "BAAI/bge-large-en-v1.5"; COMPLEMENT_HEAD_STOPLIST as in
§3; COMPLEMENT_MIN_FORMATS_PER_HEAD = 5; CONTENT_DECILES = 10.
