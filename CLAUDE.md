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
- Instances: source_data/OCR_text/confirmed_memes_full.csv. Expected
  columns: an image reference ('Image Ref' or 'file') plus OCR 'Text'.
  Downloaded image filenames follow {meme_id}_main.*, {meme_id}_template.*,
  {meme_id}_gallery_NNN.* inside per-meme folders, so the parent id should
  be recoverable from the reference string; verify and report the parse
  rate rather than trusting this.

## Reference figures for sanity checks

Reconcile observed counts against these and note discrepancies; do not
force agreement: 16,707 KYM entries total; 507,127 instances; 419,482
instances with OCR text overall (Confirmed and Submission combined);
roughly 4,500 Confirmed formats with instances; 8,597 Confirmed meme
classes used in retrieval.

## Current stage

Stage 0: the gate (GATE_SPEC.md). Everything else is blocked on its result
and the human's sign-off in chat.
