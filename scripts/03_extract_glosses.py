"""03_extract_glosses.py - usage-gloss extraction and function taxonomy per
03_EXTRACTION_SPEC.md.

Run: python scripts/03_extract_glosses.py
Population: ALL Confirmed memes with non-empty About Text (the gloss layer
is a resource over the whole meta layer). Unit of extraction: the clause.

Writes outputs/gloss_layer_draft.csv, outputs/extraction_report.md,
outputs/samples/audit_clauses_150.csv, outputs/samples/audit_nogloss_100.csv,
outputs/samples/watermark_candidates_v2.csv.
"""
import os

# Must be set before spaCy is imported: thinc imports the user-site
# tensorflow, which crashes on a protobuf C-extension version mismatch
# unless protobuf falls back to its pure-Python implementation.
os.environ.setdefault("PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION", "python")

import re
import sys
from collections import Counter, defaultdict
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


# ----------------------------------------------------------------------
# Pattern families (case-insensitive). Complement span runs from the match
# to the sentence end or a cheap finite-clause boundary (see CLAUSE_BOUNDARY).
USED_TO_RX = re.compile(
    r"\b(?:(?:is|are|was|were|has been|often|typically|most often|commonly|usually)\s+)*"
    r"used\s+(to|as|for|in|when)\b", re.IGNORECASE)

RESPONSE_RXS = [
    (re.compile(r"\b(?:in|as a)\s+(response|reaction|reply)\s+to\b", re.IGNORECASE), None),
    (re.compile(r"\b(react)(?:ing|s)?\s+to\b", re.IGNORECASE), "react"),
    (re.compile(r"\bused\s+(when)\b", re.IGNORECASE), "use_when"),
    (re.compile(r"\b(posted)\s+(?:in response|when|after)\b", re.IGNORECASE), "post"),
]
EXPRESS_RX = re.compile(
    r"\bto\s+(express|convey|indicate|signal|denote|show|communicate)\b", re.IGNORECASE)
ACTION_RX = re.compile(
    r"\bto\s+(mock|criticize|criticise|ridicule|deride|troll|parody|satirize|satirise|"
    r"make fun of|poke fun at|celebrate|praise)\b", re.IGNORECASE)
CAPTION_RXS = [
    (re.compile(r"\b(captioned)\s+(?:with|to|as)\b", re.IGNORECASE), "caption"),
    (re.compile(r"\b(paired)\s+with\b", re.IGNORECASE), "pair"),
    (re.compile(r"\bwith\s+(captions)\b", re.IGNORECASE), "caption"),
]
COPULA_RXS = [
    (re.compile(r"\b(?:is|are)\s+an?\s+", re.IGNORECASE), "is_a"),
    (re.compile(r"\b(refer)s?\s+to\b", re.IGNORECASE), "refer"),
]

NARRATIVE_RX = re.compile(
    r"\b(?:began|originated|gained|went viral|was uploaded)\b", re.IGNORECASE)

CLAUSE_BOUNDARY = re.compile(r";|:\s|, (?:which|who|where|while|although|though|but)\b")

USAGE_FAMILIES = ("USED-TO", "RESPONSE", "EXPRESS", "ACTION", "CAPTION")

NORMALISE_PRED = {"criticise": "criticize", "satirise": "satirize",
                  "make fun of": "make_fun_of", "poke fun at": "poke_fun_at"}

# Taxonomy v1, ratified in chat 2026-06-11. Changes from the draft:
# reaction-head complements -> RESPOND (override below); DESCRIBE replaced
# by LABEL, which absorbs refer/represent/describe; signify/highlight ->
# EXPRESS; create -> STRUCTURAL. Remaining unknown predicates stay UNMAPPED.
RATIFIED_MAP = {
    "RESPOND": ["respond", "react", "reply", "response", "reaction", "post",
                "use_when", "answer"],
    "EXPRESS": ["express", "convey", "indicate", "signal", "denote", "show",
                "communicate", "demonstrate", "display", "signify",
                "highlight"],
    "EVALUATE": ["mock", "criticize", "ridicule", "deride", "troll", "parody",
                 "satirize", "make_fun_of", "poke_fun_at", "celebrate",
                 "praise", "insult", "shame", "lampoon"],
    "LABEL": ["describe", "label", "characterize", "depict", "portray",
              "illustrate", "identify", "call", "refer", "represent"],
    "STRUCTURAL": ["use_as", "use_for", "use_in", "caption", "pair",
                   "exploit", "template", "remix", "create"],
}
PRED_TO_LABEL = {p: lab for lab, preds in RATIFIED_MAP.items() for p in preds}


def assign_label(predicate, comp_head):
    """Ratified rule: any usage clause whose complement head is 'reaction'
    is RESPOND ('used as a reaction to ...'), regardless of predicate."""
    if comp_head == "reaction":
        return "RESPOND"
    return PRED_TO_LABEL.get(predicate, "UNMAPPED")

# Top-200 ordinary English words (Brown/GTWC-style list, embedded so the
# run is dependency-free and deterministic), for the v2 watermark scan.
COMMON_200 = set("""
the of and to in a is that for it as was with be by on not he i this are or
his from at which but have an had they you were their one all we can her has
there been if more when will would who so no she other its may these what
them than some him time into only could new then do any my now such like our
over man me even most made after also did many before must through years
where much your way well down should because each just those people mr how
too little state good very make world still own see men work long get here
between both life being under never day same another know while last might
us great old year off come since against go came right used take three
states himself few house use during without again place american around
however home small found mrs thought went say part once general high upon
school every don does got united left number course war until always away
something fact though water less public put thing almost hand enough far
took head yet government system better set told nothing night end why called
didn eyes find going look asked later knew point next city business case
group give days four
""".split())

STRIP_CHARS = "\"'.,;:!?()[]{}<>|*~`^"


def complement_span(sent_text, start, end):
    m = CLAUSE_BOUNDARY.search(sent_text, end)
    return sent_text[start:m.start() if m else len(sent_text)].strip()


def token_at_char(sent, abs_char):
    for tok in sent:
        if tok.idx <= abs_char < tok.idx + len(tok.text):
            return tok
    return None


def extract_used_to(sent, sent_text, records, entry_id, si, narrative):
    for m in USED_TO_RX.finditer(sent_text):
        prep = m.group(1).lower()
        clause = complement_span(sent_text, m.start(), m.end())
        exclusion = "narrative" if narrative else None
        if prep == "to":
            used_off = m.start() + m.group(0).lower().rfind("used")
            used_tok = token_at_char(sent, sent.start_char + used_off)
            governed = None
            if used_tok is not None:
                j = used_tok.i + 1
                doc = used_tok.doc
                # skip 'to' and any interleaved adverbs: 'used to sarcastically mock'
                while j < len(doc) and (doc[j].lower_ == "to" or doc[j].pos_ in ("ADV", "PART")):
                    j += 1
                if j < len(doc) and doc[j].is_alpha:
                    governed = doc[j]
            if governed is not None:
                lemma = governed.lemma_.lower()
                if lemma in ("be", "have") and exclusion is None:
                    exclusion = "used_to_be_have"
                if lemma == "make" and "fun of" in clause.lower():
                    pred = "make_fun_of"
                elif lemma == "poke" and "fun at" in clause.lower():
                    pred = "poke_fun_at"
                else:
                    pred = NORMALISE_PRED.get(lemma, lemma)
            else:
                pred = "use_to"
        else:
            pred = "use_" + prep
        records.append(dict(id=entry_id, sent_idx=si, family="USED-TO",
                            predicate=pred, clause=clause, exclusion=exclusion))


def extract_simple(sent_text, records, entry_id, si, narrative, family, rxs):
    for rx, fixed_pred in rxs:
        for m in rx.finditer(sent_text):
            pred = fixed_pred or m.group(1).lower()
            pred = NORMALISE_PRED.get(pred, pred)
            records.append(dict(
                id=entry_id, sent_idx=si, family=family, predicate=pred,
                clause=complement_span(sent_text, m.start(), m.end()),
                exclusion="narrative" if narrative else None))


def complement_head(sent, clause_abs_start, pred_end_abs):
    """First NOUN/PROPN lemma after the predicate inside the clause span."""
    for tok in sent:
        if tok.idx >= pred_end_abs and tok.pos_ in ("NOUN", "PROPN"):
            return tok.lemma_.lower()
    return None


def main():
    config.OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    config.SAMPLES_DIR.mkdir(parents=True, exist_ok=True)

    emit("# Extraction report (03_EXTRACTION_SPEC.md)")
    emit()
    emit("Generated by scripts/03_extract_glosses.py on {} with seed {}.".format(
        datetime.now().strftime("%Y-%m-%d %H:%M"), config.RANDOM_SEED))
    emit()

    entries = pd.read_csv(config.ENTRIES_CSV, dtype=str, low_memory=False)
    emit("Entries columns ({}): {}".format(len(entries.columns), list(entries.columns)))
    for col in ("Status", "Entry Type", "Type:", "About Text", "ID", "Title"):
        if col not in entries.columns:
            emit("DISCREPANCY: expected entries column '{}' absent. Stopping.".format(col))
            return
    cm = entries[(entries["Status"] == "Confirmed") & (entries["Entry Type"] == "meme")].copy()
    cm["about"] = cm["About Text"].fillna("")
    pop = cm[cm["about"].str.strip() != ""].copy().reset_index(drop=True)
    emit("Population: {} Confirmed memes with non-empty About Text "
         "(spec expectation: 11,489).".format(len(pop)))
    emit()

    def norm_types(val):
        if pd.isna(val):
            return []
        return [t.strip().lower() for t in str(val).split(";") if t.strip()]

    pop["types"] = pop["Type:"].map(norm_types)

    try:
        import spacy
        nlp = spacy.load("en_core_web_sm", disable=["ner"])
    except Exception as exc:
        emit("spaCy en_core_web_sm could not be loaded: {!r}. Extraction "
             "cannot run; stopping.".format(exc))
        return

    # ------------------------------------------------------------------
    emit("## 1. Candidate clause extraction")
    emit()
    records = []
    docs = nlp.pipe(pop["about"].tolist(), batch_size=32)
    for (_, row), doc in zip(pop.iterrows(), docs):
        for si, sent in enumerate(doc.sents):
            sent_text = sent.text
            narrative = bool(NARRATIVE_RX.search(sent_text))
            extract_used_to(sent, sent_text, records, row["ID"], si, narrative)
            extract_simple(sent_text, records, row["ID"], si, narrative,
                           "RESPONSE", RESPONSE_RXS)
            extract_simple(sent_text, records, row["ID"], si, narrative,
                           "EXPRESS", [(EXPRESS_RX, None)])
            extract_simple(sent_text, records, row["ID"], si, narrative,
                           "ACTION", [(ACTION_RX, None)])
            extract_simple(sent_text, records, row["ID"], si, narrative,
                           "CAPTION", CAPTION_RXS)
            if si == 0:
                # COPULA: gloss typing only, never narrative-excluded
                for rx, pred in COPULA_RXS:
                    m = rx.search(sent_text)
                    if m:
                        records.append(dict(
                            id=row["ID"], sent_idx=0, family="COPULA",
                            predicate=pred,
                            clause=complement_span(sent_text, m.start(), m.end()),
                            exclusion=None))

    rec = pd.DataFrame(records)
    usage_all = rec[rec["family"].isin(USAGE_FAMILIES)]
    usage = usage_all[usage_all["exclusion"].isna()]
    emit("Candidate clauses: {} total ({} usage-family, {} COPULA).".format(
        len(rec), len(usage_all), (rec["family"] == "COPULA").sum()))
    emit()
    emit("| Family | Matches | Excluded: narrative | Excluded: used-to-be/have | Kept |")
    emit("|--------|---------|---------------------|---------------------------|------|")
    for fam in USAGE_FAMILIES:
        f = usage_all[usage_all["family"] == fam]
        n_narr = (f["exclusion"] == "narrative").sum()
        n_befix = (f["exclusion"] == "used_to_be_have").sum()
        emit("| {} | {} | {} | {} | {} |".format(
            fam, len(f), n_narr, n_befix, f["exclusion"].isna().sum()))
    emit("| COPULA (typing only) | {} | - | - | {} |".format(
        (rec["family"] == "COPULA").sum(), (rec["family"] == "COPULA").sum()))
    emit()

    # ------------------------------------------------------------------
    emit("## 2. Gloss typing")
    emit()
    usage_by_id = usage.groupby("id")
    has_usage = set(usage["id"])
    copula_ids = set(rec.loc[rec["family"] == "COPULA", "id"])
    pop["has_usage_gloss"] = pop["ID"].isin(has_usage)
    pop["definitional_only"] = pop["ID"].isin(copula_ids) & ~pop["has_usage_gloss"]
    n_u = pop["has_usage_gloss"].sum()
    n_d = pop["definitional_only"].sum()
    n_none = len(pop) - n_u - n_d
    emit("- USAGE (>= 1 kept usage clause): {} ({})".format(n_u, pct(n_u / len(pop))))
    emit("- DEFINITIONAL-ONLY (COPULA, no usage clause): {} ({})".format(n_d, pct(n_d / len(pop))))
    emit("- Neither: {} ({})".format(n_none, pct(n_none / len(pop))))
    emit()

    # Coverage within the gate intersection (cue AND >= MIN_INSTANCES usable).
    ocr = pd.read_csv(config.OCR_CONFIRMED_CSV, dtype=str)
    emit("OCR columns ({}): {} (join key: 'label', per gate validation).".format(
        len(ocr.columns), list(ocr.columns)))
    cm_ids = set(cm["ID"].dropna())
    ocr["format_id"] = ocr["label"]
    ocr["n_tokens"] = ocr["Text"].fillna("").str.split().str.len()
    usable = ocr[ocr["format_id"].isin(cm_ids) & (ocr["n_tokens"] >= config.MIN_TOKENS)].copy()
    per_format = usable.groupby("format_id").size()
    gate_cues = re.compile("|".join([
        r"\bused (?:to|as|when|in)\b", r"\bexpress(?:es|ing)?\b",
        r"\brefer(?:s|ring)? to\b", r"\breaction(?:\s+(?:image|gif|video))?\b",
        r"\bmock(?:s|ing|ery)?\b", r"\bparod(?:y|ies|ying)\b",
        r"\bdepict(?:s|ing)?\b", r"\bdescrib(?:es|ing)\b", r"\btypically\b",
        r"\bcaptioned\b", r"\bin which\b", r"\brepresent(?:s|ing)?\b",
    ]), re.IGNORECASE)
    cue_ids = set(cm.loc[cm["about"].str.contains(gate_cues), "ID"])
    intersection = {fid for fid, k in per_format.items()
                    if k >= config.MIN_INSTANCES and fid in cue_ids}
    inter_pop = pop[pop["ID"].isin(intersection)]
    emit()
    emit("- Coverage, all Confirmed memes with About Text: {} of {} ({})".format(
        n_u, len(pop), pct(n_u / len(pop))))
    emit("- Coverage within the gate intersection ({} formats, gate reported "
         "4,029): {} of {} ({})".format(
             len(intersection), inter_pop["has_usage_gloss"].sum(), len(inter_pop),
             pct(inter_pop["has_usage_gloss"].sum() / len(inter_pop))))
    emit()

    # ------------------------------------------------------------------
    emit("## 3. Predicate inventory and taxonomy (v1, ratified in chat 2026-06-11)")
    emit()
    pred_counts = usage["predicate"].value_counts()

    # complement heads: first NOUN/PROPN lemma in the clause after the
    # predicate, kept per record so the reaction-head override can apply
    usage = usage.copy()
    heads = []
    head_docs = nlp.pipe(usage["clause"].str.slice(0, 200).tolist(), batch_size=64,
                         disable=["parser"])
    for (_, r), cdoc in zip(usage.iterrows(), head_docs):
        pred_word = r["predicate"].split("_")[0]
        seen_pred = False
        head = None
        for tok in cdoc:
            if not seen_pred and tok.lemma_.lower().startswith(pred_word[:4]):
                seen_pred = True
                continue
            if seen_pred and tok.pos_ in ("NOUN", "PROPN"):
                head = tok.lemma_.lower()
                break
        heads.append(head)
    usage["comp_head"] = heads
    head_counter = defaultdict(Counter)
    for predicate, head in zip(usage["predicate"], usage["comp_head"]):
        if head:
            head_counter[predicate][head] += 1

    emit("Top 30 USAGE predicate lemmas with most common complement heads:")
    emit()
    emit("| Predicate | Clauses | Top complement heads | Label (v1) |")
    emit("|-----------|---------|----------------------|-------------|")
    for predicate, k in pred_counts.head(30).items():
        heads = ", ".join("{} ({})".format(h, c)
                          for h, c in head_counter[predicate].most_common(5))
        emit("| {} | {} | {} | {} |".format(
            predicate, k, heads or "-", PRED_TO_LABEL.get(predicate, "UNMAPPED")))
    emit()
    unmapped = pred_counts[~pred_counts.index.isin(PRED_TO_LABEL)]
    emit("- Predicate lemmas outside the v1 mapping: {} distinct, {} clauses; "
         "top 15: {}".format(
             len(unmapped), int(unmapped.sum()),
             ", ".join("{} ({})".format(p, k) for p, k in unmapped.head(15).items())))
    emit()
    emit("Mapping v1, ratified in chat 2026-06-11 (changes from draft: "
         "reaction-head complements -> RESPOND regardless of predicate; "
         "DESCRIBE replaced by LABEL, absorbing refer/represent/describe; "
         "signify/highlight -> EXPRESS; create -> STRUCTURAL):")
    emit()
    emit("| Function label | Predicate lemmas |")
    emit("|----------------|------------------|")
    for lab, preds in RATIFIED_MAP.items():
        observed = [p for p in preds if p in pred_counts.index]
        emit("| {} | {} |".format(lab, ", ".join(observed) if observed else "(none observed)"))
    emit()
    n_react_override = (usage["comp_head"] == "reaction").sum()
    emit("- Reaction-head override applied to {} clauses ('used as a "
         "reaction to ...' and kin -> RESPOND).".format(n_react_override))
    emit("- Multi-label per entry is allowed and expected. Remaining unknown "
         "predicates stay UNMAPPED for a future ratification round.")
    emit()

    usage["draft_label"] = [assign_label(p, h) for p, h in
                            zip(usage["predicate"], usage["comp_head"])]

    # ------------------------------------------------------------------
    # 4. Validation audits
    aud = usage.merge(pop[["ID", "Title"]], left_on="id", right_on="ID")
    a150 = aud.sample(n=min(config.EXTRACT_AUDIT_CLAUSES_N, len(aud)),
                      random_state=config.RANDOM_SEED)
    a150_out = pd.DataFrame({
        "entry_id": a150["id"], "title": a150["Title"],
        "clause_text": a150["clause"], "family": a150["family"],
        "predicate": a150["predicate"], "draft_label": a150["draft_label"],
        "is_genuine_gloss": "", "label_correct": "", "notes": ""})
    p = config.SAMPLES_DIR / "audit_clauses_150.csv"
    a150_out.to_csv(p, index=False, encoding="utf-8")

    nogloss = pop[~pop["has_usage_gloss"]]
    a100 = nogloss.sample(n=min(config.EXTRACT_AUDIT_NOGLOSS_N, len(nogloss)),
                          random_state=config.RANDOM_SEED)
    a100_out = pd.DataFrame({
        "entry_id": a100["ID"], "title": a100["Title"],
        "about_text": a100["about"], "missed_gloss": "", "missed_text": ""})
    p2 = config.SAMPLES_DIR / "audit_nogloss_100.csv"
    a100_out.to_csv(p2, index=False, encoding="utf-8")

    emit("## 4. Validation audits")
    emit()
    emit("- Precision audit: {} extracted USAGE clauses -> {}".format(
        len(a150_out), p.relative_to(config.REPO_ROOT)))
    emit("- Recall audit: {} entries with no extracted USAGE clause -> {}".format(
        len(a100_out), p2.relative_to(config.REPO_ROOT)))
    emit("- Blank columns are for the human annotator; the filled files become "
         "the paper's reliability numbers (single expert annotator).")
    emit()

    # ------------------------------------------------------------------
    # 5. Gloss layer draft CSV
    agg = usage.groupby("id").agg(
        usage_clauses=("clause", lambda s: " || ".join(s)),
        families=("family", lambda s: ";".join(sorted(set(s)))),
        predicates=("predicate", lambda s: ";".join(sorted(set(s)))),
        function_labels=("draft_label", lambda s: ";".join(sorted(set(s)))),
        n_usage_clauses=("clause", "size"))
    layer = pop[["ID", "Title", "types", "Status", "has_usage_gloss",
                 "definitional_only"]].merge(
        agg, left_on="ID", right_index=True, how="left")
    layer["types"] = layer["types"].map(";".join)
    layer = layer.rename(columns={"ID": "entry_id", "Title": "title",
                                  "Status": "status"})
    layer["n_usage_clauses"] = layer["n_usage_clauses"].fillna(0).astype(int)
    for c in ("usage_clauses", "families", "predicates", "function_labels"):
        layer[c] = layer[c].fillna("")
    p = config.OUTPUTS_DIR / "gloss_layer_draft.csv"
    layer.to_csv(p, index=False, encoding="utf-8")
    emit("## 5. Gloss layer (taxonomy v1)")
    emit()
    emit("Wrote {} ({} rows; function_labels carry taxonomy v1 as ratified "
         "in chat 2026-06-11).".format(p.relative_to(config.REPO_ROOT), len(layer)))
    emit()

    # Worked examples: 4 seeded per usage family
    emit("### Worked examples (4 per family, seeded)")
    emit()
    ex = aud.groupby("family", group_keys=False).apply(
        lambda g: g.sample(n=min(4, len(g)), random_state=config.RANDOM_SEED))
    for _, r in ex.iterrows():
        emit("- **{}** [{} / {} -> {}] {}: \"{}\"".format(
            r["family"], r["predicate"], r["id"], r["draft_label"],
            r["Title"], " ".join(str(r["clause"]).split())[:220]))
    emit()

    emit("### Known failure modes observed")
    emit()
    emit("- Complement spans are cut at a cheap textual boundary (';', ': ', "
         "', which/who/where/while/although/though/but'); coordinated "
         "complements ('used to mock X and to praise Y') survive intact but "
         "trailing matter can leak in.")
    emit("- The narrative exclusion is sentence-level: a genuine usage clause "
         "inside a sentence that also mentions origin ('originated as a "
         "reaction image used to...') is excluded with it; counted above.")
    emit("- 'used in' often introduces venue ('used in forums') rather than "
         "function; kept under STRUCTURAL in taxonomy v1.")
    emit("- COPULA 'is a/an' on the first sentence over-fires on plain "
         "definitions; it is used for gloss typing only, never as USAGE.")
    emit()

    # ------------------------------------------------------------------
    emit("## 6. Broadened watermark scan (v2)")
    emit()
    emit("Alphabetic tokens, length >= 4, lowercased, appearing in >= {} "
         "distinct formats, excluding an embedded top-200 ordinary-English "
         "word list (Brown/GTWC-style). No stripping applied.".format(
             config.WATERMARK_V2_MIN_FORMATS))
    emit()
    tok_formats = Counter()
    for fid, grp in usable.groupby("format_id")["Text"]:
        fmt_tokens = set()
        for text in grp.fillna(""):
            for w in text.lower().split():
                w = w.strip(STRIP_CHARS)
                if len(w) >= 4 and w.isalpha() and w not in COMMON_200:
                    fmt_tokens.add(w)
        tok_formats.update(fmt_tokens)

    cand = [(t, k) for t, k in tok_formats.items() if k >= config.WATERMARK_V2_MIN_FORMATS]
    cand.sort(key=lambda x: -x[1])
    top50 = cand[:50]
    contexts = defaultdict(list)
    top_set = {t for t, _ in top50}
    for text in usable["Text"].fillna(""):
        low = text.lower()
        for t in top_set:
            if len(contexts[t]) < 3 and t in low:
                i = low.find(t)
                contexts[t].append(" ".join(text[max(0, i - 40):i + len(t) + 40].split()))
        if all(len(contexts[t]) >= 3 for t in top_set):
            break

    emit("Tokens in >= {} formats: {}. Top 25 (full top 50 with contexts in "
         "the CSV):".format(config.WATERMARK_V2_MIN_FORMATS, len(cand)))
    emit()
    emit("| Token | Formats |")
    emit("|-------|---------|")
    for t, k in top50[:25]:
        emit("| `{}` | {} |".format(t, k))
    emit()
    v2 = pd.DataFrame([{
        "token": t, "n_formats": k,
        "context_1": contexts[t][0] if len(contexts[t]) > 0 else "",
        "context_2": contexts[t][1] if len(contexts[t]) > 1 else "",
        "context_3": contexts[t][2] if len(contexts[t]) > 2 else "",
    } for t, k in top50])
    p = config.SAMPLES_DIR / "watermark_candidates_v2.csv"
    v2.to_csv(p, index=False, encoding="utf-8")
    emit("Wrote {} ({} rows) for human review; the approved combined list is "
         "applied in 04.".format(p.relative_to(config.REPO_ROOT), len(v2)))
    emit()

    report = config.OUTPUTS_DIR / "extraction_report.md"
    report.write_text("\n".join(REPORT_LINES), encoding="utf-8")
    print("Report written to {}".format(report))


if __name__ == "__main__":
    main()
