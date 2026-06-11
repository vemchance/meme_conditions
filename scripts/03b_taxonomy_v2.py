"""03b_taxonomy_v2.py - taxonomy v2 per 03B_TAXONOMY_V2_SPEC.md, STEP TWO,
with the chat ratifications of 2026-06-11:

- denote -> LABEL accepted (v2 over v1);
- primary order reordered to [RESPOND, EVALUATE, DIRECT, LABEL, EXPRESS]
  (specific before general; anything depictive trivially "expresses");
- published supplement list layered on the anchors where WordNet's
  hypernym paths fail: insult, shame, celebrate, commemorate, mimic,
  joke -> EVALUATE; complain, demonstrate, display -> EXPRESS;
  characterize, call, claim -> LABEL;
- DIRECT pruned: hold, censor -> OTHER (claim moved to LABEL above);
- DIRECT ratified as a family; per-family statistical contrasts only at
  >= 100 clauses (encoded in 04), descriptive reporting below that.

The pre-ratification step-one diff (outputs/taxonomy_v2_step1.md) is left
untouched as the ratification record; this script applies v2 to the layer
and relabels ALL audit files in place, preserving rows byte-for-byte
except the draft_label column. No reparse: everything derives from
outputs/gloss_clauses.csv.

Run: python scripts/03b_taxonomy_v2.py
"""
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

import nltk
from nltk.corpus import wordnet as wn

REPORT_LINES = []


def emit(line=""):
    print(line)
    REPORT_LINES.append(line)


FAMILY_ORDER = ["RESPOND", "EVALUATE", "DIRECT", "LABEL", "EXPRESS"]
ANCHORS = {
    "RESPOND": ["react.v.01", "answer.v.01"],
    "EVALUATE": ["knock.v.06", "mock.v.01", "mock.v.02", "ridicule.v.01",
                 "disparage.v.01", "satirize.v.01", "praise.v.01"],
    "DIRECT": ["request.v.01", "request.v.02", "solicit.v.01", "ask.v.02",
               "urge.v.01", "recommend.v.01", "encourage.v.03",
               "invite.v.04", "demand.v.01"],
    "EXPRESS": ["express.v.01", "express.v.02", "carry.v.04", "convey.v.01",
                "sign.v.05", "bespeak.v.01", "indicate.v.03"],
    "LABEL": ["label.v.01", "name.v.01", "name.v.02", "mention.v.01",
              "describe.v.01", "picture.v.02", "portray.v.02",
              "typify.v.02", "denote.v.01", "denote.v.02"],
}

# Ratified supplement: published list layered on the anchors where
# WordNet's paths fail (or mislead, as for call/claim). Forces the primary;
# WordNet hits are retained in the all-hits record. express/show added by
# ratification 2026-06-11 after stray sense collisions surfaced (express.v.04
# 'indicate through a symbol' reaches denote.v.02; 'show' is a lemma of the
# LABEL anchor picture.v.02), which the reorder would otherwise flip to LABEL.
SUPPLEMENT = {
    "insult": "EVALUATE", "shame": "EVALUATE", "celebrate": "EVALUATE",
    "commemorate": "EVALUATE", "mimic": "EVALUATE", "joke": "EVALUATE",
    "complain": "EXPRESS", "demonstrate": "EXPRESS", "display": "EXPRESS",
    "express": "EXPRESS", "show": "EXPRESS",
    "characterize": "LABEL", "call": "LABEL", "claim": "LABEL",
}
FORCED_OTHER = {"hold", "censor"}

CONSTRUCTIONAL = {
    "use_as": "STRUCTURAL", "use_for": "STRUCTURAL", "use_in": "STRUCTURAL",
    "create": "STRUCTURAL",
    "caption": "CAPTION", "pair": "CAPTION",
    "use_when": "RESPOND", "response": "RESPOND", "reaction": "RESPOND",
    "post": "RESPOND",
}
LIGHT_VERBS = {"make", "do", "get", "take", "have", "go"}
MULTIWORD_RULES = {"make_fun_of": "EVALUATE", "poke_fun_at": "EVALUATE"}

ANCHOR_SYNSETS = {}


def build_anchors():
    for fam, ids in ANCHORS.items():
        ANCHOR_SYNSETS[fam] = {wn.synset(i) for i in ids}


def wordnet_hits(lemma):
    closures = set()
    for s in wn.synsets(lemma, pos="v"):
        closures.add(s)
        closures.update(s.closure(lambda x: x.hypernyms()))
    return [fam for fam in FAMILY_ORDER if closures & ANCHOR_SYNSETS[fam]]


def map_lemma_v2(pred):
    """Returns (primary, all_hits, rule). primary is a family name or
    'OTHER'."""
    if pred in MULTIWORD_RULES:
        f = MULTIWORD_RULES[pred]
        return f, [f], "multiword"
    if pred in CONSTRUCTIONAL:
        f = CONSTRUCTIONAL[pred]
        return f, [f], "constructional"
    if pred in FORCED_OTHER:
        return "OTHER", [], "pruned_to_other"
    hits = [] if pred in LIGHT_VERBS or "_" in pred else wordnet_hits(pred)
    if pred in SUPPLEMENT:
        f = SUPPLEMENT[pred]
        all_hits = [f] + [h for h in hits if h != f]
        return f, all_hits, "supplement"
    if pred in LIGHT_VERBS:
        return "OTHER", [], "light_verb"
    if "_" in pred:
        return "OTHER", [], "unparsed"
    if hits:
        return hits[0], hits, "wordnet"
    return "OTHER", [], "no_anchor_hit"


def clause_label_v2(predicate, comp_head, lemma_primary):
    if comp_head == "reaction":
        return "RESPOND"
    return lemma_primary


def relabel_audit(path, label_of):
    """Replace draft_label in an audit CSV with v2 labels; rows untouched."""
    a = pd.read_csv(path, dtype=str, keep_default_na=False)
    before = len(a)
    a["draft_label"] = [
        label_of.get((e, c, f, p), "OTHER")
        for e, c, f, p in zip(a["entry_id"], a["clause_text"],
                              a["family"], a["predicate"])]
    assert len(a) == before
    a.to_csv(path, index=False, encoding="utf-8")
    return a


def main():
    build_anchors()
    emit("# Taxonomy v2, step two: ratified mapping applied "
         "(03B_TAXONOMY_V2_SPEC.md)")
    emit()
    emit("Generated by scripts/03b_taxonomy_v2.py on {}. NLTK {}, WordNet {}.".format(
        datetime.now().strftime("%Y-%m-%d %H:%M"), nltk.__version__,
        wn.get_version()))
    emit()
    emit("Ratifications applied: primary order {}; supplement {}; pruned to "
         "OTHER: {}; denote stays LABEL per anchors; DIRECT ratified "
         "(statistical contrasts only at >= {} clauses, encoded in 04; "
         "Searle crosswalk DIRECT -> directive).".format(
             FAMILY_ORDER, SUPPLEMENT, sorted(FORCED_OTHER),
             config.FAMILY_CONTRAST_MIN_CLAUSES))
    emit()

    clauses = pd.read_csv(config.OUTPUTS_DIR / "gloss_clauses.csv", dtype=str,
                          keep_default_na=False)
    lemma_map = {}
    for pred in clauses["predicate"].unique():
        lemma_map[pred] = map_lemma_v2(pred)

    clauses["label_v2"] = [
        clause_label_v2(p, h, lemma_map[p][0])
        for p, h in zip(clauses["predicate"], clauses["comp_head"])]
    clauses["v2_all_hits"] = [";".join(lemma_map[p][1])
                              for p in clauses["predicate"]]
    clauses.to_csv(config.OUTPUTS_DIR / "gloss_clauses.csv", index=False,
                   encoding="utf-8")
    emit("- gloss_clauses.csv: label_v2 and v2_all_hits columns written "
         "({} clauses).".format(len(clauses)))

    # entry-level layer
    layer_p = config.OUTPUTS_DIR / "gloss_layer_draft.csv"
    layer = pd.read_csv(layer_p, dtype=str, keep_default_na=False)
    per_entry = clauses.groupby("entry_id")["label_v2"].agg(
        lambda s: ";".join(sorted(set(s))))
    layer["function_labels_v2"] = layer["entry_id"].map(per_entry).fillna("")
    layer.to_csv(layer_p, index=False, encoding="utf-8")
    emit("- gloss_layer_draft.csv: function_labels_v2 column written "
         "({} rows; v1 column retained for provenance).".format(len(layer)))

    # audit files: same rows, v2 labels
    key_label = {}
    for e, c, f, p, l in zip(clauses["entry_id"], clauses["clause"],
                             clauses["family"], clauses["predicate"],
                             clauses["label_v2"]):
        key_label[(e, c, f, p)] = l
    a150 = relabel_audit(config.SAMPLES_DIR / "audit_clauses_150.csv", key_label)
    a150.head(50).to_csv(config.SAMPLES_DIR / "audit_clauses_50_A2.csv",
                         index=False, encoding="utf-8")
    l25 = relabel_audit(config.SAMPLES_DIR / "audit_label_25.csv", key_label)
    still_label = (l25["draft_label"] == "LABEL").sum()
    emit("- audit_clauses_150.csv, audit_clauses_50_A2.csv, "
         "audit_label_25.csv relabelled in place (same rows).")
    emit("- LABEL top-up under v2: {} of {} rows still LABEL "
         "(the rest moved family; flag in chat if a fresh LABEL top-up "
         "is wanted).".format(still_label, len(l25)))
    emit("- audit_nogloss_100.csv has no label column; untouched.")
    emit()

    # accounting
    emit("## Per-family clause counts (v2 final, primary labels)")
    emit()
    counts = Counter(clauses["label_v2"])
    emit("| Family | Clauses | Contrast-eligible (>= {}) |".format(
        config.FAMILY_CONTRAST_MIN_CLAUSES))
    emit("|--------|---------|---------------------------|")
    for fam in ["RESPOND", "EVALUATE", "DIRECT", "LABEL", "EXPRESS",
                "STRUCTURAL", "CAPTION", "OTHER"]:
        k = counts.get(fam, 0)
        emit("| {} | {} | {} |".format(
            fam, k, "yes" if k >= config.FAMILY_CONTRAST_MIN_CLAUSES and
            fam != "OTHER" else ("-" if fam == "OTHER" else "no, descriptive only")))
    emit()
    direct_lemmas = sorted(set(
        p for p in clauses.loc[clauses["label_v2"] == "DIRECT", "predicate"]))
    emit("- DIRECT lemmas after pruning: {}".format(", ".join(direct_lemmas)))
    sup_applied = Counter(p for p in clauses["predicate"] if p in SUPPLEMENT)
    emit("- Supplement applications: {}".format(dict(sup_applied)))
    emit()
    emit("## Entry-level coverage (v2)")
    emit()
    ent = Counter()
    for labs in per_entry:
        for f in set(labs.split(";")):
            ent[f] += 1
    emit("| Family | Entries with >= 1 clause |")
    emit("|--------|--------------------------|")
    for fam in ["RESPOND", "EVALUATE", "DIRECT", "LABEL", "EXPRESS",
                "STRUCTURAL", "CAPTION", "OTHER"]:
        emit("| {} | {} |".format(fam, ent.get(fam, 0)))
    emit()
    emit("04 runs only on this v2 layer (label_v2 / function_labels_v2).")

    (config.OUTPUTS_DIR / "taxonomy_v2_step2.md").write_text(
        "\n".join(REPORT_LINES), encoding="utf-8")
    print("Report written to outputs/taxonomy_v2_step2.md")

    # supersession note at the top of the v1-era extraction report
    er = config.OUTPUTS_DIR / "extraction_report.md"
    txt = er.read_text(encoding="utf-8")
    note = ("> SUPERSEDED LABELS: taxonomy v2 was ratified and applied on "
            "2026-06-11; labels in this report are v1. The live labels are "
            "label_v2 / function_labels_v2 (see outputs/taxonomy_v2_step2.md "
            "and outputs/taxonomy_v2_step1.md).\n\n")
    if not txt.startswith("> SUPERSEDED"):
        er.write_text(note + txt, encoding="utf-8")
        print("Supersession note prepended to extraction_report.md")


if __name__ == "__main__":
    main()
