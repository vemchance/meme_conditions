# 04_ANALYSIS_SPEC — form-function analysis

Implement as scripts/04_analysis.py (+ scripts/05_audit_stats.py, runnable
independently whenever the filled audit files land). Everything seeded.
Append to CLAUDE.md design log: taxonomy v1 ratified; watermark rule
ratified as below; LABEL audit top-up added.

## 0. Population

Formats with >= 1 usage-family clause AND >= 20 usable instances
(~1,607). Formats whose only clauses are UNMAPPED carry has_usage_gloss
but no family: exclude from pair classification, report the count.
Multi-label preserved throughout.

## 1. Instance-text preparation

- Watermark stripping (ratified): token-strip the 9 v1 site marks
  (watermark_candidates.csv) plus {youtooz, cravi, vinyls}; phrase-strip
  {"twitter for iphone","twitter for android","twitter web app",
  "know your meme","click to view"}; in texts containing youtooz/cravi,
  additionally strip {"get 10 % off","use code","click here",
  "meme vinyls"}. Case-insensitive after whitespace normalisation. Log
  tokens removed. Re-apply the >= MIN_TOKENS filter after stripping.
- Lowercase for all tagging and counting.
- Per-format instance cap: seeded sample of up to
  PER_FORMAT_INSTANCE_CAP = 100 usable instances per format, so large
  formats do not dominate profile estimates.

## 2. Format form profiles

Per format, over its (capped) instances:
- Function-word distribution: relative frequencies over the fixed spaCy
  stop list (record list version). Pair distance: Jensen-Shannon
  divergence.
- POS-trigram distribution (spaCy en_core_web_sm on lowercased text,
  padded sentence boundaries). Pair similarity: cosine.
- Shallow cues (per-instance rates averaged per format): first-person
  pronoun rate; second/third-person pronoun rate; INTJ rate;
  'when'-clause rate (token 'when' starting a clause or text);
  question-mark rate.

## 3. Headline test

Same-function pair := formats sharing >= 1 usage family; different :=
sharing none.
- Statistic: mean(within) - mean(between), per measure (FW-JSD sign
  flipped so positive = more similar; POS cosine as-is).
- Inference: permutation test, label sets shuffled over formats
  preserving multiplicities, N_PERMUTATIONS = 10,000; one-sided p.
- Per-family one-vs-rest contrasts: which functions bind form most
  tightly. Report effect sizes with permutation CIs.

## 4. Controls (the separability claim)

- Pair-level regression: similarity ~ same_function + tag_overlap
  (Jaccard over normalised Tags) + same_type (share >= 1 normalised
  Type) + log instance counts. Dyadic non-independence handled by
  MRQAP-style inference: re-estimate the same_function coefficient under
  the §3 label permutations.
- Transparent version: within-vs-between contrast restricted to pairs
  with ZERO shared tags.
- Type strata: repeat §3 within exploitable-only, image-macro-only,
  catchphrase-only subsets.

## 5. Calibration and flagged classes

- Copypasta positive control: within-format INSTANCE-level mean
  similarity per format; show copypasta at/near ceiling vs fill-types.
- Reaction-type formats: report §3 with and without them (co-text
  caveat).

## 6. Directional checks (prespecified, exploratory)

Bootstrap CIs (1,000 resamples over formats) on shallow-cue rates per
family. Directions fixed now: RESPOND higher 'when'-clause and
second-person; EXPRESS higher first-person and INTJ; EVALUATE higher
second/third-person. STRUCTURAL and CAPTION are contrast classes, no
direction.

## 7. Robustness

- Re-run §3 unstripped (watermark sensitivity).
- Searle crosswalk: EXPRESS+EVALUATE -> expressive; LABEL -> assertive;
  RESPOND -> responsive (ISO feedback dimension; outside Searle's five);
  STRUCTURAL, CAPTION -> affordance (non-illocutionary; documented
  non-coverage). Re-run §3 under the grouped labels.
- Remap sensitivity: EVALUATE merged into EXPRESS.

## 8. Audit statistics (scripts/05_audit_stats.py)

When filled files exist: precision = share is_genuine_gloss = Y (A1,
150; LABEL top-up reported separately); recall proxy = share
missed_gloss = Y among the 100; Cohen's kappa on the 50-row overlap.
Report-only; no hard gate, discussion happens in chat.

## 9. Outputs

outputs/analysis_report.md (all numbers and tables); outputs/figures/
(PDF+PNG: within-vs-between distributions; per-family forest plot;
copypasta ceiling); outputs/pair_stats_summary.csv (small). Commit, push,
STOP. Interpretation happens in chat; the paper drafting follows.

## Config additions

PER_FORMAT_INSTANCE_CAP = 100; N_PERMUTATIONS = 10000; BOOTSTRAP_N = 1000
