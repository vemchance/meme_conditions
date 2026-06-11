# 02_TYPE_PROFILE_SPEC — meme-type profiles and subset grounding

Purpose: ground the type-subsetting decision in measurement before any
analysis design is fixed. Implement as scripts/02_type_profile.py, writing
outputs/type_profile.md plus the small CSVs named below. Reuse the gate's
join logic: OCR parent id = 'label' column (canonical; validated 100%
against filename parse in the gate).

Also in this commit: correct two items in CLAUDE.md so future sessions are
not misled — (1) schema note: OCR instance file columns are
['Text','label','file']; 'label' is the KYM id and the canonical join key;
filenames follow '{8-hex id}-NNNNN.ext' with variants, not the download
script's '{id}_gallery_NNN' pattern; (2) reference figure: 8,597 Confirmed
classes is the right comparator for formats-with-instances (the ~4,500
figure was the thresholded retrieval-evaluation class count, 4,478).

## 1. Normalise 'Type:' (Confirmed memes only)

Split on ';', strip whitespace, unify case. Report:
- top 30 normalised types with entry counts (multi-typed entries count once
  per type) and the multi-type rate;
- NaN/none rate among (a) all Confirmed memes, (b) the gate's intersection
  set (>= 1 cue AND >= 20 usable instances).

## 2. Per-type profiles (intersection set)

For each of the top 15 normalised types by number of intersection formats:
- formats; total usable instances; median usable instances per format;
- on a seeded sample of up to 300 usable texts per type: median tokens,
  function-word rate distribution (report the share in the 30-70% band),
  all-caps rate, junk rate (gate C definitions).

Output the table in the report and as outputs/samples/type_profile.csv.

## 3. Watermark scan

Across usable OCR texts joined to Confirmed memes, find candidate
watermark tokens/bigrams: items appearing in >= 200 distinct formats that
contain '.com'/'.net' or match a seed list (quickmeme, memegenerator,
imgflip, ragebuilder, 9gag, ifunny, kapwing, makeameme). Report the top 40
with format-spread counts. Write a draft stoplist to
outputs/samples/watermark_candidates.csv for human review. Do NOT apply
any stripping yet.

## 4. Report

End the report with the per-type table sorted by intersection formats.
No recommendation logic in code: the humans choose the subset. Commit and
push the script, report, and CSVs. Then stop.
