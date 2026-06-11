# PIPELINE — status map (update on every commit)

Paper: use-conditions of meme templates, SemDial 2026. Deadline 17 June.

| # | Stage | Status |
|---|-------|--------|
| 01 | Gate (viability checks) | DONE — commit (A 72.3%, B 4,029, C settled as register) |
| 02 | Type profile | DONE — no type gating; Type = stratum; copypasta = control |
| 03 | Gloss extraction + taxonomy v1 | DONE — 4,517 clauses; 39.9% intersection coverage |
| 03B | Taxonomy v2 (WordNet anchors, DIRECT candidate) | Step 1 COMMITTED — diff in outputs/taxonomy_v2_step1.md (73% lemma agreement, 10 disagreements listed, DIRECT = 30 clauses); awaiting ratification in chat before step 2 |
| — | Human audits (A1 250 rows + LABEL 25; A2 50 rows) | BLOCKED on 03B step 2. Protocol: AUDIT_PROTOCOL.md |
| 04 | Analysis (form-function tests) | Code in progress; RUNS ONLY on v2 layer |
| 05 | Audit statistics (precision/recall/kappa) | When filled audit files land |
| 06 | Paper drafting (in chat, from analysis_report.md) | Days 5-6 |
| 07 | Submission: anonymised snapshot, no repo links | 17 June |

Standing rules: specs are ratified in chat before implementation; every
stage STOPs after committing outputs; humans never annotate against
labels that are about to change.
