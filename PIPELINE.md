# PIPELINE — status map (update on every commit)

Paper: use-conditions of meme templates, SemDial 2026. Deadline 17 June.

| # | Stage | Status |
|---|-------|--------|
| 01 | Gate (viability checks) | DONE — commit (A 72.3%, B 4,029, C settled as register) |
| 02 | Type profile | DONE — no type gating; Type = stratum; copypasta = control |
| 03 | Gloss extraction + taxonomy v1 | DONE — 4,517 clauses; 39.9% intersection coverage |
| 03B | Taxonomy v2 (WordNet anchors, DIRECT candidate) | DONE — v2 ratified + applied (step 2); label_v2/function_labels_v2 live; EXPRESS 854 / STRUCTURAL 1537 / RESPOND 535 / EVALUATE 461 / CAPTION 453 / LABEL 309 / DIRECT 16 (descriptive) / OTHER 158 |
| — | Human audits (A1 250 rows + LABEL 25; A2 50 rows) | UNBLOCKED — audit files relabelled to v2, same rows; annotation can start |
| 04 | Analysis (form-function tests) | DONE — omnibus headline null (p~.97); per-family: LABEL + EVALUATE bind form (p<=.001), CAPTION anti-coherent; copypasta ceiling confirmed; RESPOND when-clause direction supported; watermark-insensitive. Interpretation in chat |
| 05 | Audit statistics (precision/recall/kappa) | When filled audit files land |
| 06 | Paper drafting (in chat, from analysis_report.md) | Days 5-6 |
| 07 | Submission: anonymised snapshot, no repo links | 17 June |

Standing rules: specs are ratified in chat before implementation; every
stage STOPs after committing outputs; humans never annotate against
labels that are about to change.
