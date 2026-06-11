"""03b_taxonomy_v2.py - step ONE of 03B_TAXONOMY_V2_SPEC.md: WordNet-anchored
predicate mapping, diffed against taxonomy v1. STOPS after writing the diff;
step two (layer regeneration) runs only after ratification in chat.

Run: python scripts/03b_taxonomy_v2.py
Reads outputs/gloss_clauses.csv. Writes outputs/taxonomy_v2_step1.md and
outputs/samples/taxonomy_v2_diff.csv. No layer or audit files are touched.
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


# Anchor synsets (exact ids verified at implementation; definitions are
# printed below so the intended senses are auditable). Family order is the
# primary-tiebreak order from the spec.
FAMILY_ORDER = ["RESPOND", "EVALUATE", "DIRECT", "EXPRESS", "LABEL"]
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

# Constructional/keyword rules carried over unchanged (not verb-semantic):
CONSTRUCTIONAL = {
    "use_as": "STRUCTURAL", "use_for": "STRUCTURAL", "use_in": "STRUCTURAL",
    "create": "STRUCTURAL",
    "caption": "CAPTION", "pair": "CAPTION",
    "use_when": "RESPOND", "response": "RESPOND", "reaction": "RESPOND",
    "post": "RESPOND",
}
LIGHT_VERBS = {"make", "do", "get", "take", "have", "go"}
MULTIWORD_RULES = {"make_fun_of": "EVALUATE", "poke_fun_at": "EVALUATE"}

# v1 mapping for the diff (taxonomy v1 as ratified 2026-06-11, with the
# CAPTION split used by 04; constructional entries included).
V1_MAP = {}
for fam, preds in {
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
    "STRUCTURAL": ["use_as", "use_for", "use_in", "create"],
    "CAPTION": ["caption", "pair"],
}.items():
    for p in preds:
        V1_MAP[p] = fam

ANCHOR_SYNSETS = {}
ANCHOR_ALL = []


def build_anchors():
    for fam, ids in ANCHORS.items():
        ss = [wn.synset(i) for i in ids]
        ANCHOR_SYNSETS[fam] = set(ss)
        for s in ss:
            ANCHOR_ALL.append((fam, s))


def hypernym_closure(synset):
    out = {synset}
    out.update(synset.closure(lambda s: s.hypernyms()))
    return out


def v2_families(lemma):
    """All anchor families hit by any verb synset of the lemma via its
    hypernym closure; [] if none. Light verbs and multiword predicates are
    handled by the caller."""
    hits = []
    syns = wn.synsets(lemma, pos="v")
    closures = set()
    for s in syns:
        closures.update(hypernym_closure(s))
    for fam in FAMILY_ORDER:
        if closures & ANCHOR_SYNSETS[fam]:
            hits.append(fam)
    return hits


def map_lemma(pred):
    """Returns (v2 families list, rule). Constructional and light-verb
    rules first; WordNet for ordinary lemmas; OTHER if nothing hits."""
    if pred in MULTIWORD_RULES:
        return [MULTIWORD_RULES[pred]], "multiword"
    if pred in CONSTRUCTIONAL:
        return [CONSTRUCTIONAL[pred]], "constructional"
    if pred in LIGHT_VERBS:
        return [], "light_verb"
    if "_" in pred:
        return [], "unparsed"
    fams = v2_families(pred)
    return fams, ("wordnet" if fams else "no_anchor_hit")


def nearest_anchor(lemma):
    best = (None, None, 0.0)
    for s in wn.synsets(lemma, pos="v"):
        for fam, a in ANCHOR_ALL:
            sim = s.path_similarity(a)
            if sim is not None and sim > best[2]:
                best = (fam, a.name(), sim)
    return best


def main():
    build_anchors()
    emit("# Taxonomy v2, step one: WordNet-anchored mapping vs v1 "
         "(03B_TAXONOMY_V2_SPEC.md)")
    emit()
    emit("Generated by scripts/03b_taxonomy_v2.py on {}. NLTK {}, WordNet {}. "
         "STOP: ratification in chat before step two; no layer or audit "
         "files were modified.".format(
             datetime.now().strftime("%Y-%m-%d %H:%M"),
             nltk.__version__, wn.get_version()))
    emit()

    emit("## Anchor synsets (exact senses)")
    emit()
    for fam in FAMILY_ORDER:
        emit("- **{}**:".format(fam))
        for i in ANCHORS[fam]:
            emit("  - `{}` - {}".format(i, wn.synset(i).definition()))
    emit()
    emit("STRUCTURAL and CAPTION keep the v1 complement/keyword rules "
         "(constructional, not verb-semantic): {}. Light verbs {} bypass "
         "WordNet (complement-aware rules only: {}); otherwise OTHER. "
         "Primary family by fixed order {}.".format(
             {k: v for k, v in CONSTRUCTIONAL.items()},
             sorted(LIGHT_VERBS), MULTIWORD_RULES, FAMILY_ORDER))
    emit()

    clauses = pd.read_csv(config.OUTPUTS_DIR / "gloss_clauses.csv", dtype=str)
    pred_counts = clauses["predicate"].value_counts()
    example = clauses.groupby("predicate")["clause"].first()

    results = {}
    for pred in pred_counts.index:
        fams, rule = map_lemma(pred)
        results[pred] = (fams, rule)

    # ------------------------------------------------------------------
    emit("## Agreement with v1 on the ratified v1 lemmas")
    emit()
    verb_lemmas = [p for p in V1_MAP
                   if p not in CONSTRUCTIONAL and p not in MULTIWORD_RULES]
    agree = disagree = 0
    rows = []
    for p in sorted(verb_lemmas):
        fams, rule = (results[p] if p in results else (map_lemma(p)[0], "unobserved"))
        primary = fams[0] if fams else "OTHER"
        v1 = V1_MAP[p]
        ok = primary == v1
        in_hits = v1 in fams
        agree += ok
        disagree += (not ok)
        if not ok:
            rows.append((p, v1, primary, fams, rule,
                         int(pred_counts.get(p, 0))))
    emit("- Verb-semantic v1 lemmas checked: {}; primary agreement: {} "
         "({:.1f}%).".format(len(verb_lemmas), agree,
                             100.0 * agree / len(verb_lemmas)))
    if rows:
        emit()
        emit("Every disagreement, verbatim:")
        emit()
        emit("| Lemma | v1 | v2 primary | v2 all hits | Rule | Clauses |")
        emit("|-------|----|------------|-------------|------|---------|")
        for p, v1, primary, fams, rule, k in rows:
            emit("| {} | {} | {} | {} | {} | {} |".format(
                p, v1, primary, ", ".join(fams) or "-", rule, k))
    emit()

    # ------------------------------------------------------------------
    # full lemma-level diff CSV
    diff_rows = []
    for pred, k in pred_counts.items():
        fams, rule = results[pred]
        primary = fams[0] if fams else (
            CONSTRUCTIONAL.get(pred) or MULTIWORD_RULES.get(pred) or "OTHER")
        if rule in ("constructional", "multiword"):
            primary = fams[0]
        diff_rows.append({
            "lemma": pred,
            "n_clauses": int(k),
            "v1_family": V1_MAP.get(pred, "UNMAPPED"),
            "v2_primary": primary,
            "v2_all_hits": ";".join(fams),
            "rule": rule,
            "example_clause": " ".join(str(example[pred]).split())[:200],
        })
    diff = pd.DataFrame(diff_rows)
    p_csv = config.SAMPLES_DIR / "taxonomy_v2_diff.csv"
    diff.to_csv(p_csv, index=False, encoding="utf-8")
    emit("Full lemma-level diff: {} ({} lemmas).".format(
        p_csv.relative_to(config.REPO_ROOT), len(diff)))
    emit()

    # ------------------------------------------------------------------
    emit("## Per-family clause counts, v1 vs v2 (primary; reaction-head "
         "override applied in both)")
    emit()
    v2_primary_map = dict(zip(diff["lemma"], diff["v2_primary"]))
    v1_counts = Counter()
    v2_counts = Counter()
    for _, r in clauses.iterrows():
        if r["comp_head"] == "reaction":
            v1_counts["RESPOND"] += 1
            v2_counts["RESPOND"] += 1
            continue
        v1_lab = V1_MAP.get(r["predicate"], "UNMAPPED")
        v1_counts["OTHER/UNMAPPED" if v1_lab == "UNMAPPED" else v1_lab] += 1
        v2_lab = v2_primary_map[r["predicate"]]
        v2_counts["OTHER/UNMAPPED" if v2_lab == "OTHER" else v2_lab] += 1
    emit("| Family | v1 clauses | v2 clauses |")
    emit("|--------|------------|------------|")
    for fam in ["RESPOND", "EVALUATE", "DIRECT", "EXPRESS", "LABEL",
                "STRUCTURAL", "CAPTION", "OTHER/UNMAPPED"]:
        emit("| {} | {} | {} |".format(fam, v1_counts.get(fam, 0),
                                       v2_counts.get(fam, 0)))
    emit()
    emit("DIRECT mass: {} clauses across {} lemmas ({}).".format(
        v2_counts.get("DIRECT", 0),
        sum(1 for _, r in diff.iterrows() if r["v2_primary"] == "DIRECT"),
        ", ".join(sorted(r["lemma"] for _, r in diff.iterrows()
                         if r["v2_primary"] == "DIRECT")) or "none"))
    emit()

    # ------------------------------------------------------------------
    emit("## Top 30 remaining OTHER lemmas with nearest-anchor suggestions")
    emit()
    other = diff[diff["v2_primary"] == "OTHER"].sort_values(
        "n_clauses", ascending=False).head(30)
    emit("| Lemma | Clauses | Nearest anchor | Path sim | Suggested family |")
    emit("|-------|---------|----------------|----------|------------------|")
    for _, r in other.iterrows():
        fam, anc, sim = nearest_anchor(r["lemma"])
        emit("| {} | {} | {} | {} | {} |".format(
            r["lemma"], r["n_clauses"], anc or "-",
            "{:.3f}".format(sim) if anc else "-", fam or "-"))
    emit()
    emit("STOP. Ratification of v2 (including the DIRECT candidate and every "
         "disagreement above) happens in chat before step two regenerates "
         "the layer and audit files.")

    (config.OUTPUTS_DIR / "taxonomy_v2_step1.md").write_text(
        "\n".join(REPORT_LINES), encoding="utf-8")
    print("Report written to outputs/taxonomy_v2_step1.md")


if __name__ == "__main__":
    main()
