# GATE_SPEC — day-1 kill/commit checks

Purpose: decide whether the gloss angle is viable before further investment.
Three gates. Implement as scripts/01_gate.py (one script is fine), reading
paths and parameters from config.py, writing outputs/gate_report.md plus the
small sample files named below. Print actual schemas before using them.

## Gate A — About Text integrity and gloss-cue coverage

Input: entries CSV.

1. Report the actual column list and row count; reconcile against the
   reference figures in CLAUDE.md.
2. Identify the status and entry-type fields by inspection and report their
   value counts verbatim BEFORE filtering. Then filter to Confirmed
   meme-type entries.
3. About Text nulls: rate of null / empty / whitespace-only. Length
   distribution in characters and whitespace tokens (min, quartiles, max).
   Rate under 100 characters.
4. Weak truncation probe: rate of non-null About Texts that do not end in
   terminal punctuation (. ! ? closing quote or bracket).
5. Gloss-cue coverage: case-insensitive regex over About Text, reporting
   per-cue match counts and the union rate. Cues (recall-oriented probes for
   the gate only, not the extractor):
   - used to | used as | used when | used in
   - express(es|ing)?
   - refer(s|ring)? to
   - reaction( image| gif| video)? and bare "a reaction"
   - mock(s|ing|ery)?
   - parod(y|ies|ying)
   - depict(s|ing)?
   - describ(es|ing)?
   - typically
   - captioned
   - in which
   - represent(s|ing)?
6. Samples for human and chat review (seeded):
   - 30 cue-matched and 30 unmatched About Texts, first ~400 characters,
     with id and title -> outputs/samples/about_gate_sample.md
   - 500-row CSV (id, title, cues matched, full About Text)
     -> outputs/samples/about_sample_500.csv

## Gate B — join and intersection

Input: Confirmed OCR CSV plus entries.

1. Report actual columns; print 5 raw image-reference values verbatim.
2. Parse the parent id from the reference per the expected filename pattern;
   report the parse success rate and 5 verbatim failures if any exist.
3. Join parsed ids to entries. Identify the matching entry-side id column by
   inspection; if no direct id match works, attempt a URL-slug match and say
   so explicitly. Report the join rate.
4. OCR token counts (whitespace). usable := tokens >= MIN_TOKENS
   (config, default 3). Report the usable rate.
5. Per-format usable-instance counts; number of formats with >= 20 and
   >= 50.
6. THE NUMBER: count of formats with (>= 1 gloss cue in About Text) AND
   (>= MIN_INSTANCES usable instances). Report the >= 50 variant alongside.

## Gate C — OCR quality for the planned measures

Input: seeded random sample of SAMPLE_N (default 500) usable OCR texts.

1. Casing: rate of all-caps texts. Lowercase before tagging and say so in
   the report.
2. Function-word rate per text against a standard English function-word
   list (spaCy stop words are an acceptable stand-in; state what was used):
   distribution, plus the share of texts falling in a 30-70% band. Ordinary
   English prose sits around 40-60%; large deviation suggests OCR is
   dropping or mangling short words.
3. POS-taggability with spaCy en_core_web_sm (install if absent; if
   installation is impossible, say so and stop Gate C): tag distribution
   over the sample; flag if any single tag exceeds 50% or if
   DET+PRON+AUX+ADP jointly fall below 15%.
4. Junk rate: texts mostly non-alphabetic, single repeated tokens, or
   length <= 1 after cleaning.
5. 30-text eyeball sample, with raw vs lowercased vs tagged shown for 5 of
   them -> outputs/samples/ocr_gate_sample.md

## Report and decision table

outputs/gate_report.md ends with observed values against these priors:

| Gate | Measure                                              | Kill  | Marginal | Commit |
|------|------------------------------------------------------|-------|----------|--------|
| A    | cue-union rate among Confirmed memes with About Text | <15%  | 15-35%   | >35%   |
| B    | formats with cue AND >= 20 usable instances          | <200  | 200-500  | >500   |
| C    | share of texts in the 30-70% function-word band      | <50%  | 50-75%   | >75%   |

The thresholds are priors, not laws: report the numbers and let the humans
argue. If any sub-check could not run, the report states exactly why.

## After the gate

Commit and push the script, gate_report.md, and the samples. Then stop.
Extraction and analysis proceed only after sign-off in chat.
