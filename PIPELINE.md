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
| 04B | Block A: repairs + per-family controls | Two-sided p's for all 04 contrasts; tag diagnostic; zerotag + MRQAP controls for all 6 contrast families. Outputs: blocka_report.md, blocka_inference.csv |
| 04C | Block B: content layer | DONE — double dissociation: EVALUATE binds form not content; EXPRESS binds content not form; LABEL binds both; CAPTION anti-coherent on all three layers. LABEL+EVALUATE form effects survive content controls (p=.0001). EXPRESS complement prediction: continuous n.s. (p=.097), discrete companion p=.042. Decision point B in chat |
| 04D | Block C: visual layer | DONE — base SigLIP verified; both visual predictions supported (RESPOND p=.006, EXPRESS p=.0002); completed grid: EVALUATE form-only, EXPRESS semantic-only, LABEL all four layers, CAPTION negativity text-only. FLAG per reading rule: EVALUATE form effects attenuate to n.s. under high-coherence restriction (completing regression still p=.0001) — chat discussion before drafting. Decision point C in chat |
| 04E | Flag resolution: selection vs noise | DONE — coherence/modality confound confirmed (high-coherence split keeps 39% of EVALUATE, 26% of LABEL carriers; slang 56->4); low-coherence half shows effects affirmatively (LABEL p=.0001 x2, EVALUATE p=.012/.024); within-Type deciding cells all descriptive (<100 pairs) so the rule does not fire — selection reading supported, wording in chat |
| 04F | Instance-level denoising (primary noise answer) | DONE — fine-tuned-SigLIP typicality, 10% global cut (no Type >25%, flag not triggered); ALL ten significant cells hold under denoising (worst p2=.016), sensitivity 20% same signs, base-space variant agrees (no verdict flips, Jaccard .34). Gallery noise discharged; full-data claims stand with denoised robustness paragraph |
| 05B | Exhibits (qualitative material) | DONE — 7 family carrier CSVs, shortlists.md (56 shortlisted formats, 10 flagged texts each), cell illustrations (EVALUATE ?, RESPOND when, LABEL cues, EXPRESS head groups, CAPTION anti-coherence, copypasta ceiling). Flags: better_profanity + Sensitive badge; selection in chat |
| 05 | Audit statistics (precision/recall/kappa) | When filled audit files land |
| 06 | Paper drafting (in chat, from analysis_report.md) | Days 5-6 |
| 07 | Submission: anonymised snapshot, no repo links | 17 June |

Standing rules: specs are ratified in chat before implementation; every
stage STOPs after committing outputs; humans never annotate against
labels that are about to change.
