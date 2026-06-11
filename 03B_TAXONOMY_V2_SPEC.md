# 03B_TAXONOMY_V2_SPEC — WordNet-anchored predicate mapping

Replaces the v1 keyword mapping with a resource-grounded one. Two steps
with a ratification stop between them. NLTK WordNet (offline; record
version).

## 1. Anchor sets (CC verifies exact synset ids at implementation;
lemmas below name the intended senses)

- RESPOND: react, respond, reply, answer
- EVALUATE: criticize, mock, ridicule, disparage, satirize, praise
- DIRECT (candidate family, report-only until ratified): request,
  solicit, ask, urge, encourage, invite, demand
- EXPRESS: express, convey, signal, indicate
- LABEL: label, name, refer, describe, depict, represent, denote
- STRUCTURAL, CAPTION: unchanged complement/keyword rules (constructional,
  not verb-semantic) — state this in the report.

## 2. Mapping procedure

For each USAGE predicate lemma: all verb synsets -> hypernym closure ->
match against anchor closures. Record ALL families hit; primary by fixed
order [RESPOND, EVALUATE, DIRECT, EXPRESS, LABEL]. Light verbs {make, do,
get, take, have, go} bypass WordNet: complement-aware rules only
('make fun (of)' -> EVALUATE) else OTHER. No anchor hit -> OTHER.

## 3. Step one output (then STOP for ratification)

- Agreement table: v2 vs v1 on the ratified v1 lemmas (target: near-total;
  every disagreement listed verbatim).
- Full lemma-level diff CSV: lemma, n_clauses, v1 family, v2 families, one
  example clause.
- Per-family clause counts v1 vs v2, including DIRECT mass.
- Top 30 remaining OTHER lemmas with nearest-anchor suggestions.

## 4. Step two (after chat ratification)

Apply v2 to gloss_layer (function_labels_v2), regenerate
extraction_report and ALL audit files with v2 labels (same seeds, same
rows). Update the 04 Searle crosswalk: DIRECT -> directive. Append
CLAUDE.md design log. Commit, push, STOP.

Sequencing: humans do not start annotating until step two lands; the
audit validates v2. 04 implementation can proceed in parallel (it reads
labels from the CSV) but runs only on the v2 layer.
