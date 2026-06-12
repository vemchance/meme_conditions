# 04F_DENOISE_SPEC — instance-level gallery denoising

Implement as scripts/04f_denoise.py, importing shared machinery. Same
population, labels, permutation scheme, seeds, both tails + two-sided p.
Purpose: replace the format-level coherence approach (04D §2 / 04E) with
direct removal of off-template instances, then retest the significant
grid cells. 04E's composition findings stand as supporting evidence;
this is the primary noise answer.

Choices ratified with this spec:
(a) Embedding space for typicality: fine-tuned SigLIP, obtained by
    applying vision_model.pth (projection head) to the stored base
    chunks. VERIFY first that the head's expected input matches the
    stored vectors (dimension, normalisation, any preprocessing in the
    Chapter-3 inference path); if it does not apply cleanly to stored
    features, STOP and raise in chat. Base embeddings run as the
    robustness variant regardless.
(b) Typicality: per instance, mean cosine to its k = 5 nearest
    neighbours within its own format's prepared-sample gallery
    (instances in formats with <= 6 sampled instances are exempt from
    removal — too few neighbours to judge).
(c) Removal threshold: global, at the 10th percentile of the
    all-instance typicality distribution (primary); 20th percentile as
    sensitivity. Per-format removal is whatever falls below the global
    cut — noisy galleries lose more, clean galleries little.
(d) Text-anchored formats are not exempted or special-cased: the
    criterion is gallery-internal, so a visually diverse catchphrase
    gallery with mutually distant instances will see removals near the
    global rate. Report removal rate by Type so this is visible; if
    text-anchored Types show extreme removal (> 25% at the primary
    threshold), flag in the report for chat before interpretation.

## 1. Denoising pass

- Compute typicality under (a)/(b) for all 78,014 sample instances.
- Report: typicality distribution; removal counts at both thresholds,
  overall, by Type, and by family-carrier status.
- Removed-instance sample for human reading: 40 seeded-random removed
  instances (format title, OCR text, typicality score) and 40 retained,
  in the report. This is the check on what the filter actually catches.

## 2. Retest

- Rebuild format profiles (FW, POS, content) from retained instances
  only; recompute the significant grid cells (EVALUATE form x2, LABEL
  form x2, LABEL content, EXPRESS content, CAPTION negative cells,
  RESPOND when-clause) at the primary threshold, with full permutation
  inference; sensitivity threshold reported as effects-only.
- Side-by-side table: full-data vs denoised effects and p's.
- Reading rule, fixed now: cells holding under denoising are reported
  with the denoised analysis as a robustness paragraph; any cell losing
  significance at the primary threshold is flagged and the full-data
  claim is qualified in the paper accordingly. No within-format
  coherence argument is made from this block in either direction.

## 3. Robustness variant

- Repeat §1-§2 at the primary threshold with BASE embeddings for
  typicality; report the overlap of removed sets (Jaccard) and the
  retest table. Divergence between spaces goes in the report, not the
  paper, unless a cell's verdict flips between spaces — that goes to
  chat.

## 4. Outputs

outputs/blockf_report.md; outputs/blockf_retest.csv; figure: full vs
denoised effects per cell. PIPELINE row; design-log entry: choices
(a)-(d), thresholds, the reading rule, and the recorded caveats
(SigLIP text-in-image sensitivity; sibling-template bleed). Commit,
push, STOP.

## Config additions

DENOISE_K = 5; DENOISE_PCTL_PRIMARY = 10; DENOISE_PCTL_SENS = 20;
DENOISE_MIN_GALLERY = 7.
