"""01_gate.py - day-1 kill/commit checks per GATE_SPEC.md.

Run from the repo root or anywhere: python scripts/01_gate.py
Reads paths and parameters from config.py. Writes outputs/gate_report.md,
outputs/samples/about_gate_sample.md, outputs/samples/about_sample_500.csv,
outputs/samples/ocr_gate_sample.md.

Every section prints the actual schema it finds before using it. On a
mismatch with the expectations in CLAUDE.md, the discrepancy is recorded in
the report and the affected sub-check stops rather than improvising.
"""
import os

# Must be set before spaCy is imported: thinc imports the user-site
# tensorflow, which crashes on a protobuf C-extension version mismatch
# unless protobuf falls back to its pure-Python implementation.
os.environ.setdefault("PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION", "python")

import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

REPORT_LINES = []


def emit(line=""):
    print(line)
    REPORT_LINES.append(line)


def pct(x):
    return "{:.1f}%".format(100.0 * x)


def dist_line(series):
    q = series.quantile([0.0, 0.25, 0.5, 0.75, 1.0])
    return "min {:.0f} / q25 {:.0f} / median {:.0f} / q75 {:.0f} / max {:.0f} (mean {:.1f})".format(
        q[0.0], q[0.25], q[0.5], q[0.75], q[1.0], series.mean()
    )


def snippet(text, n=400):
    return " ".join(str(text).split())[:n]


# Gloss-cue probes from GATE_SPEC.md (recall-oriented, gate only).
# Note: the spec writes "describ(es|ing)?" but bare "describ" is not a word,
# so the optional group is made mandatory; recorded here, not silently.
CUES = [
    ("used to/as/when/in", r"\bused (?:to|as|when|in)\b"),
    ("express(es|ing)?", r"\bexpress(?:es|ing)?\b"),
    ("refer(s|ring)? to", r"\brefer(?:s|ring)? to\b"),
    ("reaction (image/gif/video) or 'a reaction'", r"\breaction(?:\s+(?:image|gif|video))?\b"),
    ("mock(s|ing|ery)?", r"\bmock(?:s|ing|ery)?\b"),
    ("parod(y|ies|ying)", r"\bparod(?:y|ies|ying)\b"),
    ("depict(s|ing)?", r"\bdepict(?:s|ing)?\b"),
    ("describ(es|ing)", r"\bdescrib(?:es|ing)\b"),
    ("typically", r"\btypically\b"),
    ("captioned", r"\bcaptioned\b"),
    ("in which", r"\bin which\b"),
    ("represent(s|ing)?", r"\brepresent(?:s|ing)?\b"),
]
CUES_COMPILED = [(name, re.compile(rx, re.IGNORECASE)) for name, rx in CUES]

TERMINAL_CHARS = set('.!?"\')]}’”»…')

EXPECTED_FILE_PATTERN = re.compile(r"^(.+?)_(?:main|template|gallery_\d+)\.[A-Za-z0-9]+$")
OBSERVED_FILE_PATTERN = re.compile(r"^([0-9a-f]{8})-\d+\.[A-Za-z0-9]+$")


def gate_a():
    emit("## Gate A - About Text integrity and gloss-cue coverage")
    emit()

    entries = pd.read_csv(config.ENTRIES_CSV, dtype=str, low_memory=False)
    emit("### A1. Schema and row count")
    emit()
    emit("Columns ({}): {}".format(len(entries.columns), list(entries.columns)))
    emit()
    emit("- Row count: {} (reference figure: 16,707; difference: {:+d})".format(
        len(entries), len(entries) - 16707))
    emit()

    emit("### A2. Status and entry-type fields (value counts before filtering)")
    emit()
    for col in ("Status", "Entry Type", "Type:"):
        if col not in entries.columns:
            emit("- DISCREPANCY: expected column '{}' is absent. Stopping Gate A.".format(col))
            return None
        vc = entries[col].value_counts(dropna=False)
        emit("'{}' value counts:".format(col))
        for val, n in vc.head(20).items():
            emit("- {!r}: {}".format(val, n))
        if len(vc) > 20:
            emit("- ... ({} further distinct values)".format(len(vc) - 20))
        emit()
    emit("Fields used: 'Status' (Confirmed/Unconfirmed) and 'Entry Type' "
         "(meme/event/person/...). 'Type:' is the KYM sidebar subtype "
         "(Image Macro, Reaction, ...), shown for inspection only, not used "
         "for filtering.")
    emit()

    cm = entries[(entries["Status"] == "Confirmed") & (entries["Entry Type"] == "meme")].copy()
    emit("- Confirmed meme-type entries: {} of {}".format(len(cm), len(entries)))
    emit()

    if "About Text" not in cm.columns:
        emit("- DISCREPANCY: expected column 'About Text' is absent. Stopping Gate A.")
        return None

    emit("### A3. About Text nulls and length")
    emit()
    about = cm["About Text"]
    n = len(cm)
    is_null = about.isna()
    is_empty = about.fillna("").eq("")
    is_ws = about.fillna("").str.strip().eq("") & ~is_empty & ~is_null
    nonempty_mask = ~about.fillna("").str.strip().eq("")
    cm["about_nonempty"] = nonempty_mask
    ne = cm[nonempty_mask]
    emit("- Null (NaN): {} ({})".format(is_null.sum(), pct(is_null.sum() / n)))
    emit("- Empty string: {} ({})".format((is_empty & ~is_null).sum(), pct((is_empty & ~is_null).sum() / n)))
    emit("- Whitespace-only: {} ({})".format(is_ws.sum(), pct(is_ws.sum() / n)))
    emit("- Non-empty About Text: {} ({})".format(len(ne), pct(len(ne) / n)))
    char_len = ne["About Text"].str.len()
    tok_len = ne["About Text"].str.split().str.len()
    emit("- Length, characters: " + dist_line(char_len))
    emit("- Length, whitespace tokens: " + dist_line(tok_len))
    emit("- Under 100 characters (of non-empty): {} ({})".format(
        (char_len < 100).sum(), pct((char_len < 100).sum() / len(ne))))
    emit()

    emit("### A4. Weak truncation probe")
    emit()
    last_char = ne["About Text"].str.rstrip().str[-1]
    not_terminal = ~last_char.isin(TERMINAL_CHARS)
    emit("- Non-empty About Texts not ending in terminal punctuation "
         "(. ! ? closing quote/bracket): {} ({})".format(
             not_terminal.sum(), pct(not_terminal.sum() / len(ne))))
    emit()

    emit("### A5. Gloss-cue coverage (Confirmed memes with non-empty About Text, n={})".format(len(ne)))
    emit()

    def match_cues(text):
        return [name for name, rx in CUES_COMPILED if rx.search(text)]

    cue_lists = ne["About Text"].map(match_cues)
    cm["cues_matched"] = ""
    cm.loc[ne.index, "cues_matched"] = cue_lists.map("; ".join)
    cm["cue_any"] = False
    cm.loc[ne.index, "cue_any"] = cue_lists.map(bool)

    emit("| Cue | Matches | Rate |")
    emit("|-----|---------|------|")
    for name, rx in CUES_COMPILED:
        k = cue_lists.map(lambda cs, name=name: name in cs).sum()
        emit("| {} | {} | {} |".format(name, k, pct(k / len(ne))))
    union = cm.loc[ne.index, "cue_any"].sum()
    union_rate = union / len(ne)
    emit("| **union (any cue)** | **{}** | **{}** |".format(union, pct(union_rate)))
    emit()

    emit("### A6. Samples")
    emit()
    samples_dir = config.SAMPLES_DIR
    samples_dir.mkdir(parents=True, exist_ok=True)

    matched_pool = cm[cm["cue_any"]]
    unmatched_pool = cm[cm["about_nonempty"] & ~cm["cue_any"]]
    m30 = matched_pool.sample(n=min(30, len(matched_pool)), random_state=config.RANDOM_SEED)
    u30 = unmatched_pool.sample(n=min(30, len(unmatched_pool)), random_state=config.RANDOM_SEED)

    md = ["# Gate A sample: About Texts (seed {})".format(config.RANDOM_SEED), ""]
    md += ["## Cue-matched ({})".format(len(m30)), ""]
    for _, row in m30.iterrows():
        md.append("### {} - {}".format(row["ID"], row["Title"]))
        md.append("Cues: {}".format(row["cues_matched"]))
        md.append("")
        md.append("> " + snippet(row["About Text"]))
        md.append("")
    md += ["## Unmatched ({})".format(len(u30)), ""]
    for _, row in u30.iterrows():
        md.append("### {} - {}".format(row["ID"], row["Title"]))
        md.append("")
        md.append("> " + snippet(row["About Text"]))
        md.append("")
    p = samples_dir / "about_gate_sample.md"
    p.write_text("\n".join(md), encoding="utf-8")
    emit("- Wrote {} ({} matched + {} unmatched)".format(p.relative_to(config.REPO_ROOT), len(m30), len(u30)))

    ne_all = cm[cm["about_nonempty"]]
    s500 = ne_all.sample(n=min(config.SAMPLE_N, len(ne_all)), random_state=config.RANDOM_SEED)
    csv_out = s500[["ID", "Title", "cues_matched", "About Text"]].rename(
        columns={"ID": "id", "Title": "title", "About Text": "about_text"})
    p = samples_dir / "about_sample_500.csv"
    csv_out.to_csv(p, index=False, encoding="utf-8")
    emit("- Wrote {} ({} rows)".format(p.relative_to(config.REPO_ROOT), len(csv_out)))
    emit()

    return cm, union_rate


def gate_b(cm):
    emit("## Gate B - join and intersection")
    emit()

    ocr = pd.read_csv(config.OCR_CONFIRMED_CSV, dtype=str)
    emit("### B1. Schema")
    emit()
    emit("Columns ({}): {}".format(len(ocr.columns), list(ocr.columns)))
    emit()
    emit("- Row count: {} (reference figures: 507,127 instances total; "
         "419,482 with OCR text incl. Submissions - this file is Confirmed only)".format(len(ocr)))
    emit()
    ref_col = None
    for cand in config.EXPECTED_OCR_REF_COLS:
        if cand in ocr.columns:
            ref_col = cand
            break
    if ref_col is None:
        emit("- DISCREPANCY: no expected image-reference column {} found. Stopping Gate B.".format(
            config.EXPECTED_OCR_REF_COLS))
        return None
    emit("- Image-reference column used: '{}'. 5 raw values verbatim:".format(ref_col))
    for v in ocr[ref_col].head(5):
        emit("  - {!r}".format(v))
    emit()

    emit("### B2. Parent-id parse from the reference")
    emit()
    refs = ocr[ref_col].fillna("")
    exp_match = refs.str.match(EXPECTED_FILE_PATTERN)
    emit("- Expected pattern `{{meme_id}}_(main|template|gallery_NNN).ext`: "
         "{} of {} parse ({})".format(exp_match.sum(), len(ocr), pct(exp_match.sum() / len(ocr))))
    if exp_match.sum() < len(ocr):
        emit("- 5 verbatim non-matches:")
        for v in refs[~exp_match].head(5):
            emit("  - {!r}".format(v))
    emit()
    obs_extract = refs.str.extract(OBSERVED_FILE_PATTERN, expand=False)
    obs_ok = obs_extract.notna()
    emit("- DISCREPANCY with CLAUDE.md expectation: filenames instead follow "
         "`{{8-hex id}}-NNNNN.ext`. Observed pattern parses {} of {} ({}).".format(
             obs_ok.sum(), len(ocr), pct(obs_ok.sum() / len(ocr))))
    if (~obs_ok).any():
        emit("- 5 verbatim failures of the observed pattern:")
        for v in refs[~obs_ok].head(5):
            emit("  - {!r}".format(v))
    if "label" in ocr.columns:
        agree = (obs_extract[obs_ok] == ocr.loc[obs_ok, "label"]).mean() if obs_ok.any() else float("nan")
        emit("- Cross-check: the 'label' column equals the filename-parsed id in "
             "{} of parsed rows. 'label' is used as the format id below.".format(pct(agree)))
        ocr["format_id"] = ocr["label"]
    else:
        emit("- No 'label' column; using filename-parsed id as the format id.")
        ocr["format_id"] = obs_extract
    emit()

    emit("### B3. Join to entries")
    emit()
    emit("- Entry-side id column by inspection: 'ID' (8-hex, same format as "
         "OCR 'label', e.g. {!r}); direct id match attempted, no URL-slug "
         "fallback needed.".format(cm["ID"].iloc[0]))
    all_ids = set(cm["ID"].dropna())
    joined = ocr["format_id"].isin(all_ids)
    emit("- OCR rows joining to a Confirmed meme entry: {} of {} ({})".format(
        joined.sum(), len(ocr), pct(joined.sum() / len(ocr))))
    emit("- Distinct format ids in OCR file: {}; of these join: {} "
         "(reference figure: roughly 4,500 Confirmed formats with instances)".format(
             ocr["format_id"].nunique(), ocr.loc[joined, "format_id"].nunique()))
    emit()

    emit("### B4. Usable OCR text")
    emit()
    ocr["n_tokens"] = ocr["Text"].fillna("").str.split().str.len()
    ocr["usable"] = ocr["n_tokens"] >= config.MIN_TOKENS
    emit("- usable := whitespace tokens >= MIN_TOKENS ({})".format(config.MIN_TOKENS))
    emit("- Usable rate, all rows: {} of {} ({})".format(
        ocr["usable"].sum(), len(ocr), pct(ocr["usable"].mean())))
    emit("- Usable rate, rows joined to Confirmed memes: {}".format(
        pct(ocr.loc[joined, "usable"].mean())))
    emit()

    emit("### B5. Per-format usable-instance counts (formats joined to Confirmed memes)")
    emit()
    usable_joined = ocr[joined & ocr["usable"]]
    per_format = usable_joined.groupby("format_id").size()
    emit("- Formats with >= 1 usable instance: {}".format(len(per_format)))
    emit("- Formats with >= 20 usable instances: {}".format((per_format >= 20).sum()))
    emit("- Formats with >= 50 usable instances: {}".format((per_format >= 50).sum()))
    emit()

    emit("### B6. THE NUMBER")
    emit()
    cue_ids = set(cm.loc[cm["cue_any"], "ID"])
    n20 = sum(1 for fid, k in per_format.items() if k >= config.MIN_INSTANCES and fid in cue_ids)
    n50 = sum(1 for fid, k in per_format.items() if k >= 50 and fid in cue_ids)
    emit("- Formats with >= 1 gloss cue in About Text AND >= {} usable instances: **{}**".format(
        config.MIN_INSTANCES, n20))
    emit("- Variant with >= 50 usable instances: {}".format(n50))
    emit()

    return usable_joined, n20


def gate_c(usable_joined):
    emit("## Gate C - OCR quality for the planned measures")
    emit()
    emit("Sample: seeded random sample of {} usable OCR texts from instances "
         "joined to Confirmed memes (seed {}).".format(config.SAMPLE_N, config.RANDOM_SEED))
    emit()

    sample = usable_joined.sample(
        n=min(config.SAMPLE_N, len(usable_joined)), random_state=config.RANDOM_SEED)
    texts = sample["Text"].fillna("").tolist()

    emit("### C1. Casing")
    emit()
    has_letters = [t for t in texts if any(c.isalpha() for c in t)]
    all_caps = sum(1 for t in has_letters if t == t.upper())
    emit("- All-caps texts (among {} with letters): {} ({})".format(
        len(has_letters), all_caps, pct(all_caps / len(has_letters))))
    emit("- Texts are lowercased before tagging (and for C2/C3 below).")
    emit()

    try:
        import spacy
        nlp = spacy.load("en_core_web_sm", disable=["parser", "ner", "lemmatizer"])
    except Exception as exc:
        emit("### C2-C5 NOT RUN")
        emit()
        emit("spaCy en_core_web_sm could not be loaded: {!r}. Per the spec, "
             "Gate C stops here.".format(exc))
        emit()
        return None

    lowered = [t.lower() for t in texts]
    docs = list(nlp.pipe(lowered, batch_size=64))

    emit("### C2. Function-word rate")
    emit()
    emit("- Function-word list: spaCy en stop words (len {}), via token.is_stop "
         "on lowercased text; rate computed over alphabetic tokens.".format(
             len(nlp.Defaults.stop_words)))
    fw_rates = []
    no_alpha = 0
    in_band_flags = []
    for doc in docs:
        alpha = [t for t in doc if t.is_alpha]
        if not alpha:
            no_alpha += 1
            in_band_flags.append(False)
            continue
        rate = sum(1 for t in alpha if t.is_stop) / len(alpha)
        fw_rates.append(rate)
        in_band_flags.append(0.30 <= rate <= 0.70)
    fw = pd.Series(fw_rates)
    emit("- Texts with no alphabetic tokens (excluded from distribution, "
         "counted out-of-band): {}".format(no_alpha))
    emit("- Distribution: min {} / q25 {} / median {} / q75 {} / max {} (mean {})".format(
        pct(fw.min()), pct(fw.quantile(0.25)), pct(fw.median()),
        pct(fw.quantile(0.75)), pct(fw.max()), pct(fw.mean())))
    band_all = sum(in_band_flags) / len(in_band_flags)
    band_alpha = sum(1 for r in fw_rates if 0.30 <= r <= 0.70) / len(fw_rates)
    emit("- Share in 30-70% band, all {} sampled texts: {}".format(len(texts), pct(band_all)))
    emit("- Share in 30-70% band, texts with alphabetic tokens only: {}".format(pct(band_alpha)))
    emit()

    emit("### C3. POS-taggability (spaCy en_core_web_sm, lowercased input)")
    emit()
    tag_counts = Counter(t.pos_ for doc in docs for t in doc)
    total = sum(tag_counts.values())
    emit("| POS | Count | Share |")
    emit("|-----|-------|-------|")
    for tag, k in tag_counts.most_common():
        emit("| {} | {} | {} |".format(tag, k, pct(k / total)))
    top_tag, top_k = tag_counts.most_common(1)[0]
    closed = sum(tag_counts[t] for t in ("DET", "PRON", "AUX", "ADP"))
    emit()
    emit("- Max single tag: {} at {} {}".format(
        top_tag, pct(top_k / total), "- FLAG (> 50%)" if top_k / total > 0.5 else "(no flag)"))
    emit("- DET+PRON+AUX+ADP jointly: {} {}".format(
        pct(closed / total), "- FLAG (< 15%)" if closed / total < 0.15 else "(no flag)"))
    emit()

    emit("### C4. Junk rate")
    emit()
    n_mostly_nonalpha = n_single_repeat = n_short = 0
    junk_flags = []
    for t in texts:
        nonspace = [c for c in t if not c.isspace()]
        alpha_ratio = (sum(1 for c in nonspace if c.isalpha()) / len(nonspace)) if nonspace else 0.0
        cleaned = [re.sub(r"[^a-z0-9]", "", w) for w in t.lower().split()]
        cleaned = [w for w in cleaned if w]
        mostly_nonalpha = alpha_ratio < 0.5
        single_repeat = len(cleaned) > 1 and len(set(cleaned)) == 1
        short = len(cleaned) <= 1
        n_mostly_nonalpha += mostly_nonalpha
        n_single_repeat += single_repeat
        n_short += short
        junk_flags.append(mostly_nonalpha or single_repeat or short)
    emit("- Mostly non-alphabetic (alpha chars < 50% of non-space chars): {} ({})".format(
        n_mostly_nonalpha, pct(n_mostly_nonalpha / len(texts))))
    emit("- Single repeated token: {} ({})".format(n_single_repeat, pct(n_single_repeat / len(texts))))
    emit("- <= 1 token after cleaning: {} ({})".format(n_short, pct(n_short / len(texts))))
    emit("- Junk (union): {} ({})".format(sum(junk_flags), pct(sum(junk_flags) / len(texts))))
    emit()

    emit("### C5. Eyeball sample")
    emit()
    md = ["# Gate C sample: usable OCR texts (seed {})".format(config.RANDOM_SEED), ""]
    rows = sample.head(30).reset_index(drop=True)
    for i, row in rows.iterrows():
        raw = str(row["Text"])
        md.append("## {}. format {} - file {}".format(i + 1, row["format_id"], row["file"]))
        md.append("")
        md.append("Raw: " + snippet(raw, 300))
        if i < 5:
            doc = nlp(raw.lower())
            md.append("")
            md.append("Lowercased: " + snippet(raw.lower(), 300))
            md.append("")
            md.append("Tagged: " + " ".join("{}/{}".format(t.text, t.pos_) for t in doc[:50]))
        md.append("")
    p = config.SAMPLES_DIR / "ocr_gate_sample.md"
    p.write_text("\n".join(md), encoding="utf-8")
    emit("- Wrote {} (30 texts; raw vs lowercased vs tagged for the first 5)".format(
        p.relative_to(config.REPO_ROOT)))
    emit()

    return band_all


def main():
    config.OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    config.SAMPLES_DIR.mkdir(parents=True, exist_ok=True)

    emit("# Gate report (GATE_SPEC.md)")
    emit()
    emit("Generated by scripts/01_gate.py on {} with seed {}.".format(
        datetime.now().strftime("%Y-%m-%d %H:%M"), config.RANDOM_SEED))
    emit()
    emit("- Entries: {}".format(config.ENTRIES_CSV))
    emit("- OCR (Confirmed): {}".format(config.OCR_CONFIRMED_CSV))
    emit()

    a = gate_a()
    if a is None:
        union_rate = None
        the_number = None
        band = None
    else:
        cm, union_rate = a
        b = gate_b(cm)
        if b is None:
            the_number = None
            band = None
        else:
            usable_joined, the_number = b
            band = gate_c(usable_joined)

    emit("## Decision table")
    emit()
    emit("| Gate | Measure | Observed | Kill | Marginal | Commit | Reading |")
    emit("|------|---------|----------|------|----------|--------|---------|")

    def verdict(value, kill, commit, fmt):
        if value is None:
            return "NOT RUN", "-"
        label = "Kill" if value < kill else ("Commit" if value > commit else "Marginal")
        return fmt(value), label

    v, lab = verdict(union_rate, 0.15, 0.35, pct)
    emit("| A | cue-union rate among Confirmed memes with About Text | {} | <15% | 15-35% | >35% | {} |".format(v, lab))
    v, lab = verdict(the_number, 200, 500, str)
    emit("| B | formats with cue AND >= 20 usable instances | {} | <200 | 200-500 | >500 | {} |".format(v, lab))
    v, lab = verdict(band, 0.50, 0.75, pct)
    emit("| C | share of texts in the 30-70% function-word band | {} | <50% | 50-75% | >75% | {} |".format(v, lab))
    emit()
    emit("The thresholds are priors, not laws: the numbers above are reported "
         "for the humans to argue over. Extraction and analysis do not proceed "
         "without sign-off in chat.")
    emit()

    report = config.OUTPUTS_DIR / "gate_report.md"
    report.write_text("\n".join(REPORT_LINES), encoding="utf-8")
    print("Report written to {}".format(report))


if __name__ == "__main__":
    main()
