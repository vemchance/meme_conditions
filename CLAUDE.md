# CLAUDE.md — meme_conditions (SemDial 2026)

## What this project is

A 5-6 page long paper for SemDial 2026. Long-paper deadline 17 June 2026;
poster fallback 17 July 2026.

Core idea: KnowYourMeme (KYM) editorial About sections contain
community-authored usage glosses for meme templates ("a reaction image used
to express disappointment", "used to mock X"). We extract these glosses,
derive a small bottom-up function taxonomy from the gloss predicates, and
test whether the documented function predicts measurable regularities in the
linguistic form of the text people actually write into those templates
(function-word distributions, POS structure), with topic controlled via
tags. Contribution shape: scheme + finding + released resource (a
template-to-function gloss layer over the SemioMeme dataset).

The theoretical framing (use-conditional semantics vs speech-act/force) is
deliberately undecided until we see the distribution of gloss predicates.
Do not bake either framing into code, variable names, or outputs.

## Division of labour

- The human and Claude in the claude.ai project hold strategy, specs,
  interpretation, and the paper prose. That Claude instance pulls this repo
  from GitHub to read outputs; it cannot see this machine.
- Claude Code (you) executes locally against the full SemioMeme data, which
  lives on this machine, via the paths in config.py.
- This repo is the bridge. Commit code and SMALL outputs (reports, samples).
  Never commit the source CSVs or any file over ~5 MB.

## Ground rules

1. Read GATE_SPEC.md before writing any gate code. Do not proceed beyond the
   gate (no gloss extractor, no analysis) without explicit instruction from
   the human.
2. Do not assume anything about the data. The schema notes below come from
   reading the scraper and builder source code, not from the files
   themselves. Every script prints the actual schema it finds; on mismatch,
   record the discrepancy in the report and stop that sub-check rather than
   silently improvising a mapping.
3. House style: numbered scripts (scripts/01_*.py, 02_*.py, ...), plain
   Python, each runnable end to end. No notebooks. No emojis in code or
   output. pandas + stdlib preferred; add spaCy only where the spec asks.
   Do not over-engineer: no classes where functions do, no premature
   abstraction.
4. Seeded randomness everywhere (config.RANDOM_SEED).
5. Outputs go to outputs/ as markdown and small CSVs. Commit and push them
   when a stage completes, so the chat instance can pull and read.
6. Do not link this repo in any submitted paper. An anonymised snapshot will
   be made at submission time.

## Decided constraints

- Confirmed entries only.
- About Text is the gloss source. Origin/Spread text are reserves; do not
  use them without instruction.
- Instance text = OCR text of Confirmed memes.

## Schema expectations (verify at runtime, never assume)

From recon of github.com/vemchance/kym_scraper and
github.com/vemchance/semiomeme:

- Entries: source_data/KYM_metadata/cleaned_source_data.csv. Expected
  columns include Title-Case renames: 'About Text', 'Origin Text',
  'Spread Text', 'Full Text', 'Meta Description', plus title, status,
  entry type/category, tags, views, date fields, and a KYM id and/or URL.
  About Text was scraped as all <p> blocks under <h2 id="about"> until the
  next h2; entries lacking that header have a null About Text. Expect a
  non-trivial null rate and measure it.
- Instances: source_data/OCR_text/confirmed_memes_full.csv. Actual columns
  (verified in the gate): ['Text', 'label', 'file']. 'label' is the KYM id
  and the canonical join key to the entries 'ID' column (validated 100%
  against the filename parse in the gate). Filenames follow
  '{8-hex id}-NNNNN.ext' with variants (e.g. '{id}-(2)-NNNNN.ext'), not the
  download script's '{id}_gallery_NNN' pattern.

## Reference figures for sanity checks

Reconcile observed counts against these and note discrepancies; do not
force agreement: 16,707 KYM entries total; 507,127 instances; 419,482
instances with OCR text overall (Confirmed and Submission combined);
8,597 Confirmed classes is the comparator for formats-with-instances
(the gate observed 8,131 distinct joining format ids; the previously
cited ~4,500 was the thresholded retrieval-evaluation class count,
4,478).

## Design log

- 2026-06-11 (with 03): No type-based discard — the primary analysis runs
  on the full intersection; 'Type:' is a stratification/control variable
  only, and multi-typed formats belong to every stratum they carry.
- 2026-06-11 (with 03): copypasta = reproductive positive control;
  reaction = co-text-flagged class, reported separately from fill-types.
- 2026-06-11 (with 03): watermark stoplist v1 = the 9 approved candidates
  from 02 (outputs/samples/watermark_candidates.csv). Stripping is deferred
  to 04 and applies only to a human-approved list.
- 2026-06-11 (with 04): taxonomy v1 ratified in chat (reaction-heads ->
  RESPOND; LABEL replaces DESCRIBE and absorbs refer/represent/describe;
  signify/highlight -> EXPRESS; create -> STRUCTURAL). For analysis, CAPTION
  is reported as its own contrast class, split from STRUCTURAL (per the 04
  spec and the AUDIT_PROTOCOL family table); the reaction-head override
  keeps precedence.
- 2026-06-11 (with 04): watermark rule ratified: token-strip the 9 v1 site
  marks + {youtooz, cravi, vinyls}; phrase-strip the five screenshot-chrome
  phrases; conditionally strip the ad-banner fragments in youtooz/cravi
  texts. Case-insensitive after whitespace normalisation; re-apply
  MIN_TOKENS after stripping.
- 2026-06-11 (with 04): LABEL audit top-up added (audit_label_25.csv, A1
  only, seeded, excludes clauses already in the 150-row audit).
- 2026-06-11 (03B step 2): taxonomy v2 ratified and applied. WordNet-anchored
  mapping (NLTK/WordNet 3.0; anchor synsets in scripts/03b_taxonomy_v2.py);
  primary order [RESPOND, EVALUATE, DIRECT, LABEL, EXPRESS]; published
  14-lemma supplement where WordNet paths fail or mislead (incl. express and
  show, added after sense-collision review: express.v.04/picture.v.02);
  hold, censor pruned to OTHER. DIRECT ratified as a family; per-family
  statistical contrasts only at >= 100 clauses
  (config.FAMILY_CONTRAST_MIN_CLAUSES), below that descriptive only; Searle
  crosswalk DIRECT -> directive. Live labels: label_v2 (clause level) and
  function_labels_v2 (entry level); v1 columns retained for provenance.
  04 runs only on the v2 layer.
- 2026-06-12 (04B): Block plan adopted - A repairs/controls (04B), B content
  layer (04C), C visual layer (04D). Choices ratified with the 04B spec:
  (a) numbering 04B/04C/04D, PIPELINE rows inserted between 04 and the
  audit/drafting stages; (b) per-family controls run for ALL families
  meeting the >= 100-clause rule, not only the significant ones, to avoid
  post-hoc selection; DIRECT stays descriptive-only. 04_analysis.py was
  restructured into shared functions (prepare/pair_context/make_all_stats/
  unstripped_sims) by pure code motion so blocks import rather than fork;
  04's committed outputs remain those of the pre-refactor run.

## Current stage

Stage 0: the gate (GATE_SPEC.md). Everything else is blocked on its result
and the human's sign-off in chat.
