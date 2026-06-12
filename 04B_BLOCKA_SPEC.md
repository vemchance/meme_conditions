# 04B_BLOCKA_SPEC — repairs and per-family controls

Implement as scripts/04b_block_a.py. Reuse the 04 machinery (profiles,
similarity matrices, permutation scheme) by import or minimal extraction
into shared functions — do not fork-and-diverge the pair logic. Everything
seeded (config.RANDOM_SEED). Same population, same v2 labels, same
N_PERMUTATIONS = 10,000. No new data preparation: this block consumes what
04 built.

Two choices ratified with this spec:
(a) numbering: this is 04B, with Blocks B and C to follow as 04C/04D;
    PIPELINE.md gains rows for the three blocks between 04 and the audit/
    drafting stages.
(b) per-family controls run for ALL families meeting the >= 100-clause rule
    (EXPRESS, STRUCTURAL, RESPOND, EVALUATE, CAPTION, LABEL), not only the
    two significant ones, to avoid post-hoc selection in what gets
    controlled. DIRECT stays descriptive-only per the standing rule.

## 1. Two-sided inference for the existing contrasts

For every permutation contrast reported in 04 (§3 headline, §3 per-family
one-vs-rest, §4 zerotag, §4 type strata, §7 unstripped, §7 Searle grouping,
§7 merge_eval), report alongside the existing one-sided p:

- p_upper (existing): share of permuted effects >= observed.
- p_lower: share of permuted effects <= observed.
- p_twosided: share of |permuted| >= |observed|.

Same label-shuffle scheme and seed as 04 so the null distributions are
reproducible. Output a single table (one row per contrast x measure)
superseding the inference columns of pair_stats_summary.csv; keep the 04
file untouched for provenance.

Purpose: the CAPTION anti-coherence and the Searle-grouping reversal are
currently claims read off null-band exceedance; they need proper p-values
before they are written into the paper.

## 2. Tag diagnostic (report-only; no decisions baked in)

Characterise what tag overlap is actually measuring, to explain the
negative tag_jaccard coefficient in the 04 regression before tags are used
or retired as a control.

- Distribution of pairwise tag Jaccard (deciles; share of pairs at exactly
  zero).
- Top 30 tags by format frequency, with counts.
- The 50 highest-Jaccard pairs: format titles, shared tags, Types of both
  formats, both formats' instance counts.
- For each Type, the mean tag Jaccard of within-Type pairs (tests whether
  high overlap concentrates in particular Types, e.g. character/slang).
- Spearman correlations at the pair level: tag_jaccard vs same_type,
  tag_jaccard vs min/max log instance count, tag_jaccard vs each
  similarity measure (the raw bivariate, for comparison against the
  regression coefficient).
- A seeded random sample of 25 mid-range pairs (Jaccard in [0.1, 0.3]) with
  titles and shared tags, for qualitative reading in chat.

No thresholds, no filtering decisions in this script; interpretation
happens in chat and feeds the Block B control design.

## 3. Per-family controls

For each family meeting FAMILY_CONTRAST_MIN_CLAUSES, the one-vs-rest
contrast (within := both formats carry the family) under the two control
designs from 04 §4, unchanged except for the family-specific pair
definition:

- Zerotag restriction: one-vs-rest effect computed only over pairs sharing
  zero normalised tags; inference by the §1 permutation scheme with the
  restriction re-applied inside each permutation.
- MRQAP-style regression: similarity ~ within_family + tag_jaccard +
  same_type + log instance counts (both formats); within_family
  coefficient re-estimated under the label permutations; report observed
  coefficient, permutation p (both tails and two-sided).

Report per family x measure: uncontrolled effect (from 04, for reference),
zerotag effect with p's, regression coefficient with p's, and the within-
pair count surviving the zerotag restriction (so thin cells are visible —
flag any family whose zerotag within-pair count falls below 100 pairs and
treat its zerotag result as descriptive).

Purpose: LABEL and EVALUATE are the paper's positive results and have not
faced the topic/type controls; the remaining families are run identically
so the controlled table is complete rather than selective.

## 4. Outputs

outputs/blocka_report.md (all tables, with the §2 diagnostic in full);
outputs/blocka_inference.csv (the §1 table plus §3 rows; small). Update
PIPELINE.md (insert Blocks A/B/C; renumber nothing else). Append to the
CLAUDE.md design log: Block plan adopted (A repairs/controls, B content
layer, C visual layer); choices (a) and (b) above. Commit, push, STOP.
Interpretation happens in chat.

## Config additions

None required. (TAG_DIAG_TOP_PAIRS = 50 and TAG_DIAG_MID_SAMPLE = 25 may be
added to config.py for visibility.)
