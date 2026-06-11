# AUDIT_PROTOCOL — gloss extraction validation

Fixed before annotation begins. Commit this file before either annotator
opens the CSVs.

## Roles

- A1 (author): all 150 rows of audit_clauses_150.csv and all 100 rows of
  audit_nogloss_100.csv. ~60-90 minutes.
- A2 (second annotator): rows 1-50 of audit_clauses_150.csv only, in a
  separate copy (audit_clauses_50_A2.csv). ~25-30 minutes.
- Work independently. Do not discuss items until both files are committed.
  Agreement (Cohen's kappa) is computed on the 50-row overlap in spec 04.

## Definitions

- USAGE GLOSS: a statement of the conditions or purpose of USE of the
  meme by participants - when it is posted (trigger), what it signals
  (stance/affect), what act it performs (mock, praise), what it labels,
  or how it is captioned/deployed.
- NOT a usage gloss: purely definitional content (what the meme is or
  depicts), historical narrative (origin, spread, virality), or a
  statement about some other entity than this entry's meme.

## audit_clauses_150.csv - judge the clause AS EXTRACTED

Read only the clause text (plus its entry title). Do not rescue meaning
from the wider About Text.

- is_genuine_gloss (Y/N): does the clause state a condition or purpose of
  use, per the definition above? If torn, answer N (conservative).
- label_correct (Y/N): is the draft family right for this clause, given
  the family table below? If N, write the correct family in notes.
  Leave blank when is_genuine_gloss = N.
- notes: free text, optional.

Family table: RESPOND (posted in reaction/response to a trigger);
EXPRESS (signals affect/stance: frustration, agreement, excitement);
EVALUATE (mocks, criticises, parodies, praises a target);
LABEL (used to refer to / describe / represent something);
STRUCTURAL (used as an exploitable/template/snowclone - affordance);
CAPTION (captioning/pairing practice).

## audit_nogloss_100.csv - judge the whole About Text

- missed_gloss (Y/N): does the About Text contain a usage statement the
  pipeline failed to extract?
- missed_text: if Y, paste the exact span. Otherwise leave blank.

## Reporting

The filled files are committed as-is and become the paper's validation
numbers: precision from A1's is_genuine_gloss, recall estimate from
missed_gloss, kappa from the 50-row overlap. No post-hoc edits to
judgements; corrections to the PIPELINE motivated by the audit are made
openly and re-audited on a fresh seeded sample if substantial.
