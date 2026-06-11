# 03_EXTRACTION_SPEC — usage-gloss extraction and function taxonomy

Purpose: build the gloss layer — the paper's scheme and released resource.
Implement as scripts/03_extract_glosses.py. Runs over ALL Confirmed memes
with non-empty About Text (n = 11,489), not just the intersection: the
gloss layer is a resource over the whole meta layer; the intersection
matters only for the instance-side analysis later.

Principle carried over: clause-level extraction, not entry-level flags.
The gate showed 'refers to' entries routinely carry a genuine usage clause
later in the same text; the unit of extraction is the clause.

Also in this commit, append a design log to CLAUDE.md: (1) no type-based
discard — primary analysis runs on the full intersection; 'Type:' is a
stratification/control variable only, and multi-typed formats belong to
every stratum they carry; (2) copypasta = reproductive positive control;
reaction = co-text-flagged class, reported separately from fill-types;
(3) watermark stoplist v1 = the 9 approved candidates from 02; stripping
is deferred to 04 and applies only to a human-approved list.

## 1. Candidate clause extraction

Sentence-split About Text (spaCy en_core_web_sm). Over sentences, match
these families (case-insensitive; lemma-aware where cheap). For every
match, capture: entry id, sentence index, family, the matched predicate
verb, and the complement span (from the predicate to the sentence end or
the next finite clause boundary).

- USED-TO: optional adverb/auxiliary ('is|are|was|were|has been|often|
  typically|most often|commonly|usually') + 'used (to|as|for|in|when)' +
  continuation.
- RESPONSE: '(in|as a) (response|reaction|reply) to', 'react(ing|s)? to',
  'used when', 'posted (in response|when|after)'.
- EXPRESS: 'to (express|convey|indicate|signal|denote|show|communicate)'.
- ACTION: 'to (mock|criticize|criticise|ridicule|deride|troll|parody|
  satirize|satirise|make fun of|poke fun at|celebrate|praise)'.
- CAPTION: 'captioned (with|to|as)', 'paired with', 'with captions'.
- COPULA (for gloss typing only, not function): first-sentence 'X is
  a/an <NP>' and 'X refers to <NP>'.

Families may overlap on the same clause; record all.

## 2. Gloss typing

Classify each entry's extracted material:
- USAGE: any clause from USED-TO / RESPONSE / EXPRESS / ACTION / CAPTION.
- DEFINITIONAL-ONLY: COPULA material with no USAGE clause anywhere.
- Exclude narrative sentences (origin/spread verbs: 'began', 'originated',
  'gained', 'went viral', 'was uploaded') from USAGE capture even when a
  family pattern fires inside them; record exclusions counted by rule.
- Exclude 'used to' matches whose governed verb lemma is 'be' or 'have'
  (past-habitual reading: 'used to be popular'); count by rule.

Entry-level summary fields: has_usage_gloss, n_usage_clauses, families
present, predicate lemmas present.

## 3. Predicate inventory and proposed taxonomy

- Frequency table of USAGE predicate lemmas with their most common
  complement heads (e.g. express -> frustration, excitement, agreement).
- Propose a mapping from predicate lemmas to a SMALL set of function
  labels, induced from the data. Working hypothesis to test against the
  table, not to force: RESPOND (trigger-conditional), EXPRESS
  (stance/affect), EVALUATE (mock/criticise/parody-of-target), DESCRIBE
  (label situations/people), STRUCTURAL (used as an exploitable/template/
  snowclone — affordance rather than function).
- Multi-label per entry is allowed and expected.
- Output the proposed mapping as a markdown table in the report. THE
  MAPPING IS NOT FINAL until the humans amend and ratify it in chat; the
  draft labels in the output CSV are marked draft.

## 4. Validation audits (prepared for the human, ~1-2 hours total)

- Precision audit: seeded random sample of 150 extracted USAGE clauses
  -> outputs/samples/audit_clauses_150.csv with columns (entry id, title,
  clause text, family, predicate, draft label, BLANK: is_genuine_gloss,
  BLANK: label_correct, BLANK: notes).
- Recall audit: seeded random sample of 100 entries with NO extracted
  USAGE clause -> outputs/samples/audit_nogloss_100.csv with (entry id,
  title, full About Text, BLANK: missed_gloss, BLANK: missed_text).
- These two filled files become the paper's reliability numbers
  (single expert annotator, stated honestly). OPTIONAL if time allows
  later: a second annotation pass by an LLM with agreement statistics —
  precedent exists in the thesis (LLM vs human annotators, Chapter 5) —
  but do not implement this now.

## 5. Outputs

- outputs/gloss_layer_draft.csv: entry id, title, normalised type(s),
  status, usage clauses (joined), families, predicates, draft function
  label(s), has_usage_gloss, definitional_only.
- outputs/extraction_report.md: counts per family and predicate; coverage
  overall AND within the 4,029 intersection; 20 worked examples spanning
  families; the proposed taxonomy mapping table; known failure modes
  observed.
- The two audit CSVs above.
- Commit and push. Then STOP: taxonomy ratification and audit results
  happen in chat before any instance-side analysis (spec 04).

## 6. Broadened watermark scan (instance-side housekeeping)

Rides along in the same run and commit; the STOP above applies after this
section's outputs are written. Re-run the 02 scan WITHOUT the TLD/seed
restriction: alphabetic tokens of length >= 4 appearing in >= 300 distinct
formats (add WATERMARK_V2_MIN_FORMATS to config), excluding the 200 most
frequent ordinary English words; report the top 50 by format spread with 3
example contexts each -> outputs/samples/watermark_candidates_v2.csv.
This catches bare-name marks ('imgflip' without the TLD, unknown sites)
that the seeded scan structurally misses. No stripping applied; the
human-approved combined list is applied in 04.

## Config additions

EXTRACT_AUDIT_CLAUSES_N = 150
EXTRACT_AUDIT_NOGLOSS_N = 100
