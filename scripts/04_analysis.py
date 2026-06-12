"""04_analysis.py - form-function analysis per 04_ANALYSIS_SPEC.md.

Run: python scripts/04_analysis.py
Inputs: outputs/gloss_clauses.csv (label_v2, from 03B step two), the entries
and OCR CSVs. Writes outputs/analysis_report.md,
outputs/pair_stats_summary.csv, outputs/figures/*.{pdf,png}.

Runs ONLY on the taxonomy v2 layer (label_v2). Seven families incl. the
ratified DIRECT; per-family statistical contrasts only for families with
>= config.FAMILY_CONTRAST_MIN_CLAUSES clauses (ratified rule) - families
under the bar are reported descriptively. Searle crosswalk includes
DIRECT -> directive.

Structured as shared functions (prepare / pair_context / make_all_stats /
unstripped_sims) so 04B+ blocks reuse the same population, profiles and
permutation machinery by import instead of forking (04B_BLOCKA_SPEC.md).
The refactor is pure code motion from the version that produced the
committed 04 outputs; all numerics are unchanged.
"""
import os

os.environ.setdefault("PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION", "python")

import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

REPORT_LINES = []
SUMMARY_ROWS = []


def emit(line=""):
    print(line)
    REPORT_LINES.append(line)


def pct(x):
    return "{:.1f}%".format(100.0 * x)


FAMILIES = ["RESPOND", "EXPRESS", "EVALUATE", "LABEL", "STRUCTURAL",
            "CAPTION", "DIRECT"]

PHRASE_STRIPS = ["twitter for iphone", "twitter for android", "twitter web app",
                 "know your meme", "click to view"]
CONDITIONAL_STRIPS = ["get 10 % off", "use code", "click here", "meme vinyls"]
EXTRA_TOKEN_STRIPS = {"youtooz", "cravi", "vinyls"}
STRIP_CHARS = "\"'.,;:!?()[]{}<>|*~`^"

FIRST_PERSON = {"i", "me", "my", "mine", "myself", "we", "us", "our", "ours",
                "ourselves"}
SECOND_THIRD = {"you", "your", "yours", "yourself", "yourselves",
                "he", "him", "his", "she", "her", "hers", "it", "its",
                "they", "them", "their", "theirs", "himself", "herself",
                "itself", "themselves"}

SEARLE_GROUPS = {"RESPOND": "responsive", "EXPRESS": "expressive",
                 "EVALUATE": "expressive", "LABEL": "assertive",
                 "STRUCTURAL": "affordance", "CAPTION": "affordance",
                 "DIRECT": "directive"}
MERGE_EVAL = {"RESPOND": "RESPOND", "EXPRESS": "EXPRESS",
              "EVALUATE": "EXPRESS", "LABEL": "LABEL",
              "STRUCTURAL": "STRUCTURAL", "CAPTION": "CAPTION",
              "DIRECT": "DIRECT"}


# ----------------------------------------------------------------------
# similarity machinery

def neg_jsd_matrix(P):
    """Pairwise negative Jensen-Shannon divergence (natural log), diag 0."""
    P = P.astype(np.float32)
    n = len(P)
    logP = np.zeros_like(P)
    np.log(P, where=P > 0, out=logP)
    H = -(P * logP).sum(1)
    S = np.zeros((n, n), np.float32)
    chunk = 32
    for i0 in range(0, n, chunk):
        Pi = P[i0:i0 + chunk]
        M = 0.5 * (Pi[:, None, :] + P[None, :, :])
        logM = np.zeros_like(M)
        np.log(M, where=M > 0, out=logM)
        Hm = -(M * logM).sum(2)
        S[i0:i0 + chunk] = -(Hm - 0.5 * H[i0:i0 + chunk, None] - 0.5 * H[None, :])
    np.fill_diagonal(S, 0.0)
    return S


def cosine_matrix(X):
    X = X.astype(np.float32)
    norms = np.linalg.norm(X, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    Xn = X / norms
    S = Xn @ Xn.T
    np.fill_diagonal(S, 0.0)
    return S.astype(np.float32)


def pair_means(S, mask_a, mask_b=None):
    """Mean similarity over pairs with both in a (within) and, if b given,
    one in a / one in b (between), via quadratic forms; S has zero diag."""
    a = mask_a.astype(np.float32)
    k = a.sum()
    within_sum = float(a @ S @ a) / 2.0
    n_within = k * (k - 1) / 2.0
    if mask_b is None:
        b = 1.0 - a
    else:
        b = mask_b.astype(np.float32)
    between_sum = float(a @ S @ b)
    n_between = k * b.sum()
    mw = within_sum / n_within if n_within else np.nan
    mb = between_sum / n_between if n_between else np.nan
    return mw, mb, int(n_within), int(n_between)


def headline_stat(S, M_bool, n):
    """mean(within) - mean(between) where M_bool is the same-function pair
    matrix (diag True allowed; diagonal of S is zero and excluded)."""
    Mf = M_bool.astype(np.float32)
    np.fill_diagonal(Mf, 0.0)
    w_sum = float((S * Mf).sum()) / 2.0
    w_n = float(Mf.sum()) / 2.0
    tot_sum = float(S.sum()) / 2.0
    tot_n = n * (n - 1) / 2.0
    b_sum = tot_sum - w_sum
    b_n = tot_n - w_n
    if w_n == 0 or b_n == 0:
        return np.nan, w_n, b_n
    return w_sum / w_n - b_sum / b_n, w_n, b_n


def perm_pvalue(obs, null):
    null = np.asarray(null)
    return (1.0 + (null >= obs).sum()) / (len(null) + 1.0)


def add_row(analysis, measure, effect, p, null, n_within=None, n_between=None):
    null = np.asarray(null, dtype=float)
    SUMMARY_ROWS.append({
        "analysis": analysis, "measure": measure,
        "effect": round(float(effect), 6),
        "p_one_sided": round(float(p), 6) if p == p else "",
        "null_q025": round(float(np.quantile(null, 0.025)), 6) if len(null) else "",
        "null_q975": round(float(np.quantile(null, 0.975)), 6) if len(null) else "",
        "n_within": n_within if n_within is not None else "",
        "n_between": n_between if n_between is not None else "",
    })


def run_headline(S_dict, L, n, n_perm, rng, tag):
    """Headline same-function contrast + permutation null for one label
    matrix; returns dict measure -> (obs, p, null). S has zero diagonal."""
    out = {}
    M = (L @ L.T) > 0
    obs = {}
    for meas, S in S_dict.items():
        o, wn, bn = headline_stat(S, M, n)
        obs[meas] = (o, wn, bn)
    nulls = {meas: np.empty(n_perm, np.float32) for meas in S_dict}
    for t in range(n_perm):
        idx = rng.permutation(n)
        Mp = (L[idx] @ L[idx].T) > 0
        for meas, S in S_dict.items():
            nulls[meas][t] = headline_stat(S, Mp, n)[0]
    for meas in S_dict:
        o, wn, bn = obs[meas]
        p = perm_pvalue(o, nulls[meas])
        add_row(tag, meas, o, p, nulls[meas], int(wn), int(bn))
        out[meas] = (o, p, nulls[meas])
    return out


# ----------------------------------------------------------------------
# shared preparation (population, instances, profiles) - 04 sections 0-2

def prepare(emit_fn):
    """Builds the analysis population, stripped/capped instances and format
    profiles. Returns a namespace consumed by main() and the 04B+ blocks."""
    clauses = pd.read_csv(config.OUTPUTS_DIR / "gloss_clauses.csv", dtype=str)
    emit_fn("gloss_clauses.csv columns: {} ({} rows)".format(
        list(clauses.columns), len(clauses)))
    if "label_v2" not in clauses.columns:
        emit_fn("DISCREPANCY: label_v2 absent - run scripts/03b_taxonomy_v2.py "
                "step two first. Stopping.")
        return None

    fmt_labels = defaultdict(set)
    for fid, lab in zip(clauses["entry_id"], clauses["label_v2"]):
        if lab in FAMILIES:
            fmt_labels[fid].add(lab)
    has_usage = set(clauses["entry_id"])

    clause_mass = clauses["label_v2"].value_counts()
    contrast_fams = [f for f in FAMILIES
                     if clause_mass.get(f, 0) >= config.FAMILY_CONTRAST_MIN_CLAUSES]
    emit_fn("- Clause mass per family: {}".format(
        {f: int(clause_mass.get(f, 0)) for f in FAMILIES}))
    emit_fn("- Contrast-eligible families (>= {} clauses): {}; descriptive "
            "only: {}".format(config.FAMILY_CONTRAST_MIN_CLAUSES, contrast_fams,
                              [f for f in FAMILIES if f not in contrast_fams]))

    entries = pd.read_csv(config.ENTRIES_CSV, dtype=str, low_memory=False)
    cm = entries[(entries["Status"] == "Confirmed") &
                 (entries["Entry Type"] == "meme")].copy()
    cm_ids = set(cm["ID"].dropna())

    ocr = pd.read_csv(config.OCR_CONFIRMED_CSV, dtype=str)
    emit_fn("OCR columns: {} ({} rows; join key 'label' per gate validation)".format(
        list(ocr.columns), len(ocr)))
    ocr["format_id"] = ocr["label"]
    ocr["text_raw"] = ocr["Text"].fillna("")
    ocr["n_tokens"] = ocr["text_raw"].str.split().str.len()
    usable = ocr[ocr["format_id"].isin(cm_ids) &
                 (ocr["n_tokens"] >= config.MIN_TOKENS)]
    per_format = usable.groupby("format_id").size()

    F_all = sorted(fid for fid in has_usage
                   if per_format.get(fid, 0) >= config.MIN_INSTANCES)
    unmapped_only = sorted(fid for fid in F_all if not fmt_labels.get(fid))
    F = [fid for fid in F_all if fid not in unmapped_only]
    emit_fn("")
    emit_fn("- Formats with >= 1 usage-family clause AND >= {} usable instances: "
            "{} (spec expectation ~1,607)".format(config.MIN_INSTANCES, len(F_all)))
    emit_fn("- Excluded from pair classification (all clauses OTHER under v2): {}".format(
        len(unmapped_only)))
    emit_fn("- Pair-classification population: {}".format(len(F)))
    n = len(F)
    fid_index = {fid: i for i, fid in enumerate(F)}
    L = np.zeros((n, len(FAMILIES)), np.float32)
    for fid in F:
        for lab in fmt_labels[fid]:
            L[fid_index[fid], FAMILIES.index(lab)] = 1.0
    emit_fn("- Formats per family: " + ", ".join(
        "{} {}".format(fam, int(L[:, j].sum())) for j, fam in enumerate(FAMILIES)))
    emit_fn("")

    # --- instance preparation (04 section 1) ---------------------------
    emit_fn("## 1. Instance-text preparation")
    emit_fn("")
    wm1 = pd.read_csv(config.SAMPLES_DIR / "watermark_candidates.csv", dtype=str)
    token_marks = set(wm1["item"].str.lower()) | EXTRA_TOKEN_STRIPS
    emit_fn("- Token marks ({}): {}".format(len(token_marks), sorted(token_marks)))
    emit_fn("- Phrase marks: {}; conditional (youtooz/cravi texts): {}".format(
        PHRASE_STRIPS, CONDITIONAL_STRIPS))
    phrase_rx = re.compile("|".join(re.escape(p) for p in PHRASE_STRIPS),
                           re.IGNORECASE)
    cond_rx = re.compile("|".join(re.escape(p) for p in CONDITIONAL_STRIPS),
                         re.IGNORECASE)
    strip_log = Counter()

    def strip_text(text):
        t = " ".join(text.split())
        low = t.lower()
        t, k = phrase_rx.subn(" ", t)
        strip_log["phrase"] += k
        if "youtooz" in low or "cravi" in low:
            t, k = cond_rx.subn(" ", t)
            strip_log["conditional_phrase"] += k
        toks = []
        for w in t.split():
            if w.strip(STRIP_CHARS).lower() in token_marks:
                strip_log["token"] += 1
            else:
                toks.append(w)
        return " ".join(toks)

    pool = usable[usable["format_id"].isin(F_all)]
    capped = pool.groupby("format_id", group_keys=False).apply(
        lambda g: g.sample(n=min(config.PER_FORMAT_INSTANCE_CAP, len(g)),
                           random_state=config.RANDOM_SEED))
    emit_fn("- Capped instances (<= {} per format, seeded): {} from {} formats".format(
        config.PER_FORMAT_INSTANCE_CAP, len(capped), capped["format_id"].nunique()))
    capped = capped.copy()
    capped["text_stripped"] = capped["text_raw"].map(strip_text)
    capped["n_tokens_stripped"] = capped["text_stripped"].str.split().str.len()
    kept = capped[capped["n_tokens_stripped"] >= config.MIN_TOKENS]
    emit_fn("- Stripping log: {} phrase hits, {} conditional-phrase hits, {} "
            "token hits".format(strip_log["phrase"], strip_log["conditional_phrase"],
                                strip_log["token"]))
    emit_fn("- Instances dropped by re-applied MIN_TOKENS filter after "
            "stripping: {} ({}); analysis instances: {}".format(
                len(capped) - len(kept), pct((len(capped) - len(kept)) / len(capped)),
                len(kept)))
    emit_fn("- All tagging and counting on lowercased text.")
    emit_fn("")

    # --- profiles (04 section 2) ----------------------------------------
    emit_fn("## 2. Format form profiles")
    emit_fn("")
    import spacy
    nlp = spacy.load("en_core_web_sm", disable=["parser", "ner", "lemmatizer"])
    STOP = sorted(nlp.Defaults.stop_words)
    stop_index = {w: i for i, w in enumerate(STOP)}
    emit_fn("- Function-word list: spaCy {} / en_core_web_sm {} stop words, "
            "n={} (fixed vector order).".format(
                spacy.__version__, nlp.meta.get("version", "?"), len(STOP)))
    emit_fn("- POS trigrams over en_core_web_sm coarse tags, instance-padded "
            "('<s> <s> ... </s>').")
    emit_fn("")

    tri_index = {}

    def profile_texts(texts, want_instances):
        """Returns aggregate fw counts (len STOP), trigram Counter (global
        index), per-instance data (fw vecs, trigram counters, cues) if
        want_instances."""
        fw = np.zeros(len(STOP), np.float64)
        tri = Counter()
        inst = []
        for doc in nlp.pipe([t.lower() for t in texts], batch_size=256):
            toks = [t for t in doc]
            alpha = [t.lower_ for t in toks if t.is_alpha]
            ifw = Counter(stop_index[w] for w in alpha if w in stop_index)
            for i, c in ifw.items():
                fw[i] += c
            tags = ["<s>", "<s>"] + [t.pos_ for t in toks] + ["</s>"]
            itri = Counter(zip(tags, tags[1:], tags[2:]))
            for g, c in itri.items():
                if g not in tri_index:
                    tri_index[g] = len(tri_index)
                tri[tri_index[g]] += c
            if want_instances:
                n_alpha = max(len(alpha), 1)
                cues = (
                    sum(1 for w in alpha if w in FIRST_PERSON) / n_alpha,
                    sum(1 for w in alpha if w in SECOND_THIRD) / n_alpha,
                    sum(1 for t in toks if t.pos_ == "INTJ") / max(len(toks), 1),
                    float(any(t.lower_ == "when" and
                              (t.i == 0 or doc[t.i - 1].is_punct) for t in toks)),
                    float("?" in doc.text),
                )
                inst.append((ifw, itri, cues))
        return fw, tri, inst

    def inst_mean_sims(inst):
        """Mean pairwise instance-level sims within a format (fw -JSD,
        trigram cosine)."""
        k = len(inst)
        if k < 2:
            return np.nan, np.nan
        Pfw = np.zeros((k, len(STOP)), np.float32)
        for i, (ifw, _, _) in enumerate(inst):
            for j, c in ifw.items():
                Pfw[i, j] = c
        rs = Pfw.sum(1, keepdims=True)
        ok = rs[:, 0] > 0
        sim_fw = np.nan
        if ok.sum() >= 2:
            Q = Pfw[ok] / rs[ok]
            Sq = neg_jsd_matrix(Q)
            m = len(Q)
            sim_fw = float(Sq.sum() / (m * (m - 1)))
        vocab = sorted({g for _, itri, _ in inst for g in itri})
        vmap = {g: i for i, g in enumerate(vocab)}
        T = np.zeros((k, len(vocab)), np.float32)
        for i, (_, itri, _) in enumerate(inst):
            for g, c in itri.items():
                T[i, vmap[g]] = c
        Sc = cosine_matrix(T)
        sim_pos = float(Sc.sum() / (k * (k - 1)))
        return sim_fw, sim_pos

    kept_by_fmt = dict(tuple(kept.groupby("format_id")))
    fmt_fw = np.zeros((n, len(STOP)), np.float64)
    fmt_tri = [None] * n
    fmt_cues = np.full((n, 5), np.nan)
    fmt_inst_sim = np.full((n, 2), np.nan)
    skipped_empty = []
    for fid in F:
        g = kept_by_fmt.get(fid)
        if g is None or not len(g):
            skipped_empty.append(fid)
            fmt_tri[fid_index[fid]] = Counter()
            continue
        fw, tri, inst = profile_texts(g["text_stripped"].tolist(), True)
        i = fid_index[fid]
        fmt_fw[i] = fw
        fmt_tri[i] = tri
        cs = np.array([x[2] for x in inst])
        fmt_cues[i] = cs.mean(0)
        fmt_inst_sim[i] = inst_mean_sims(inst)
    if skipped_empty:
        emit_fn("- NOTE: {} formats lost all instances to stripping+refilter; "
                "they keep zero profiles and are excluded from pair stats: {}".format(
                    len(skipped_empty), skipped_empty[:10]))

    valid = np.array([fmt_fw[i].sum() > 0 for i in range(n)])
    drop = (~valid).sum()
    dropped_formats = [F[i] for i in range(n) if not valid[i]]
    if drop:
        emit_fn("- Dropping {} empty-profile formats from pair analyses.".format(drop))
    keep_idx = np.where(valid)[0]
    F = [F[i] for i in keep_idx]
    L = L[keep_idx]
    fmt_fw = fmt_fw[keep_idx]
    fmt_tri = [fmt_tri[i] for i in keep_idx]
    fmt_cues = fmt_cues[keep_idx]
    fmt_inst_sim = fmt_inst_sim[keep_idx]
    n = len(F)
    fid_index = {fid: i for i, fid in enumerate(F)}

    P = fmt_fw / fmt_fw.sum(1, keepdims=True)
    V = len(tri_index)
    X = np.zeros((n, V), np.float32)
    for i, tri in enumerate(fmt_tri):
        for j, c in tri.items():
            X[i, j] = c
    X = X / X.sum(1, keepdims=True)
    emit_fn("- Profiles: {} formats; FW dim {}; POS-trigram vocab {}.".format(
        n, len(STOP), V))
    emit_fn("")
    S_dict = {"fw_negjsd": neg_jsd_matrix(P), "pos_cosine": cosine_matrix(X)}

    # tags / types / titles for the population (used by controls + 04B)
    cm_idx = cm.set_index("ID")
    tags_sets, type_sets, titles = [], [], []
    for fid in F:
        row = cm_idx.loc[fid]
        tg = row["Tags"] if isinstance(row["Tags"], str) else ""
        tags_sets.append(frozenset(t.strip().lower() for t in tg.split("|")
                                   if t.strip()))
        tp = row["Type:"] if isinstance(row["Type:"], str) else ""
        type_sets.append(frozenset(t.strip().lower() for t in tp.split(";")
                                   if t.strip()))
        titles.append(row["Title"] if isinstance(row["Title"], str) else fid)

    return SimpleNamespace(
        clauses=clauses, contrast_fams=contrast_fams, F=F, n=n,
        fid_index=fid_index, L=L, per_format=per_format, capped=capped,
        kept=kept, S_dict=S_dict, P=P, X=X, fmt_cues=fmt_cues,
        fmt_inst_sim=fmt_inst_sim, tags_sets=tags_sets, type_sets=type_sets,
        titles=titles, STOP=STOP, tri_index=tri_index,
        profile_texts=profile_texts, dropped_formats=dropped_formats,
        skipped_empty=skipped_empty,
        # exposed for 04G's uncapped path (no behaviour change here)
        usable=usable, strip_text=strip_text)


def pair_context(ns):
    """Pair-level covariates, regression scaffolding and grouped label
    matrices over the prepared population (04 section 3 preamble)."""
    n = ns.n
    iu = np.triu_indices(n, k=1)
    tag_vocab = {t: i for i, t in enumerate(
        sorted(set().union(*ns.tags_sets) or {""}))}
    B = np.zeros((n, len(tag_vocab)), np.float32)
    for i, ts in enumerate(ns.tags_sets):
        for t in ts:
            B[i, tag_vocab[t]] = 1.0
    inter = B @ B.T
    sizes = B.sum(1)
    union = sizes[:, None] + sizes[None, :] - inter
    jacc = np.where(union > 0, inter / np.maximum(union, 1e-9), 0.0)
    type_vocab = {t: i for i, t in enumerate(
        sorted(set().union(*ns.type_sets) or {""}))}
    Ty = np.zeros((n, len(type_vocab)), np.float32)
    for i, ts in enumerate(ns.type_sets):
        for t in ts:
            Ty[i, type_vocab[t]] = 1.0
    same_type = ((Ty @ Ty.T) > 0).astype(np.float32)

    log_n = np.log(np.array([ns.per_format[fid] for fid in ns.F], np.float64))
    logsum = log_n[:, None] + log_n[None, :]

    jacc_v = jacc[iu].astype(np.float32)
    stype_v = same_type[iu].astype(np.float32)
    lsum_v = logsum[iu].astype(np.float32)
    zerotag = jacc_v == 0
    y_v = {meas: S[iu].astype(np.float64) for meas, S in ns.S_dict.items()}

    Z = np.column_stack([np.ones(len(jacc_v)), jacc_v, stype_v,
                         lsum_v]).astype(np.float64)
    ZtZinv_Zt = np.linalg.pinv(Z)
    ey = {meas: y_v[meas] - Z @ (ZtZinv_Zt @ y_v[meas]) for meas in y_v}

    def fwl_beta(m_v, meas):
        ex = m_v - Z @ (ZtZinv_Zt @ m_v)
        denom = float(ex @ ex)
        return float(ex @ ey[meas]) / denom if denom else np.nan

    L_se = np.zeros((n, len(set(SEARLE_GROUPS.values()))), np.float32)
    se_cols = sorted(set(SEARLE_GROUPS.values()))
    L_me = np.zeros((n, len(set(MERGE_EVAL.values()))), np.float32)
    me_cols = sorted(set(MERGE_EVAL.values()))
    for i in range(n):
        for j, fam in enumerate(FAMILIES):
            if ns.L[i, j]:
                L_se[i, se_cols.index(SEARLE_GROUPS[fam])] = 1.0
                L_me[i, me_cols.index(MERGE_EVAL[fam])] = 1.0

    return SimpleNamespace(
        iu=iu, jacc=jacc, same_type=same_type, log_n=log_n, jacc_v=jacc_v,
        stype_v=stype_v, lsum_v=lsum_v, zerotag=zerotag, y_v=y_v, Z=Z,
        ZtZinv_Zt=ZtZinv_Zt, ey=ey, fwl_beta=fwl_beta, L_se=L_se, L_me=L_me)


def make_all_stats(ns, pc):
    """The combined per-permutation statistic function used by the 04 main
    loop and reproduced verbatim by 04B for two-sided inference."""
    n = ns.n
    S_dict = ns.S_dict
    iu = pc.iu

    def all_stats(Lc, Lsec, Lmec):
        out = {}
        M = (Lc @ Lc.T) > 0
        m_v = M[iu]
        for meas, S in S_dict.items():
            out[("headline", meas)] = headline_stat(S, M, n)[0]
            out[("searle", meas)] = headline_stat(S, (Lsec @ Lsec.T) > 0, n)[0]
            out[("merge_eval", meas)] = headline_stat(S, (Lmec @ Lmec.T) > 0, n)[0]
            out[("mrqap_beta", meas)] = pc.fwl_beta(m_v.astype(np.float64), meas)
            sv = pc.y_v[meas]
            zm = pc.zerotag & m_v
            zb = pc.zerotag & ~m_v
            out[("zerotag", meas)] = (sv[zm].mean() - sv[zb].mean()
                                      if zm.any() and zb.any() else np.nan)
        for j, fam in enumerate(FAMILIES):
            if fam not in ns.contrast_fams:
                continue  # ratified rule: descriptive only below the bar
            a = Lc[:, j]
            if a.sum() < 2 or a.sum() > n - 1:
                for meas in S_dict:
                    out[("fam_" + fam, meas)] = np.nan
                continue
            for meas, S in S_dict.items():
                mw, mb, _, _ = pair_means(S, a)
                out[("fam_" + fam, meas)] = mw - mb
        return out

    return all_stats


def unstripped_sims(ns):
    """Similarity matrices over the unstripped capped instances
    (04 section 7 robustness)."""
    n = ns.n
    fmt_fw_u = np.zeros((n, len(ns.STOP)), np.float64)
    fmt_tri_u = [None] * n
    capped_by_fmt = dict(tuple(ns.capped.groupby("format_id")))
    for fid in ns.F:
        g = capped_by_fmt.get(fid)
        fw, tri, _ = ns.profile_texts(g["text_raw"].tolist(), False)
        i = ns.fid_index[fid]
        fmt_fw_u[i] = fw
        fmt_tri_u[i] = tri
    Pu = fmt_fw_u / np.maximum(fmt_fw_u.sum(1, keepdims=True), 1e-9)
    Xu = np.zeros((n, len(ns.tri_index)), np.float32)
    for i, tri in enumerate(fmt_tri_u):
        for j, c in tri.items():
            Xu[i, j] = c
    Xu = Xu / np.maximum(Xu.sum(1, keepdims=True), 1e-9)
    return {"fw_negjsd": neg_jsd_matrix(Pu), "pos_cosine": cosine_matrix(Xu)}


def main():
    config.OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    figs = config.OUTPUTS_DIR / "figures"
    figs.mkdir(parents=True, exist_ok=True)

    emit("# Analysis report (04_ANALYSIS_SPEC.md)")
    emit()
    emit("Generated by scripts/04_analysis.py on {} with seed {}; "
         "N_PERMUTATIONS={}, BOOTSTRAP_N={}, PER_FORMAT_INSTANCE_CAP={}.".format(
             datetime.now().strftime("%Y-%m-%d %H:%M"), config.RANDOM_SEED,
             config.N_PERMUTATIONS, config.BOOTSTRAP_N,
             config.PER_FORMAT_INSTANCE_CAP))
    emit()

    emit("## 0. Population")
    emit()
    # (sections 0-2 narration and headers come from prepare)
    ns = prepare(emit)
    if ns is None:
        return

    L, n, contrast_fams = ns.L, ns.n, ns.contrast_fams
    S_dict, type_sets = ns.S_dict, ns.type_sets
    fmt_cues, fmt_inst_sim = ns.fmt_cues, ns.fmt_inst_sim

    # ------------------------------------------------------------------
    emit("## 3. Headline test")
    emit()
    rng = np.random.default_rng(config.RANDOM_SEED)
    NP_ = config.N_PERMUTATIONS
    pc = pair_context(ns)
    iu = pc.iu

    M_obs = (L @ L.T) > 0
    res = {}
    for meas, S in S_dict.items():
        o, wn, bn = headline_stat(S, M_obs, n)
        res[meas] = [o, wn, bn]
    emit("Same-function pair := formats sharing >= 1 family of {}; "
         "n pairs within={}, between={}.".format(
             FAMILIES, int(res["fw_negjsd"][1]), int(res["fw_negjsd"][2])))
    emit()

    all_stats = make_all_stats(ns, pc)
    obs_stats = all_stats(L, pc.L_se, pc.L_me)
    null_stats = {k: np.empty(NP_, np.float32) for k in obs_stats}
    for t in range(NP_):
        idx = rng.permutation(n)
        st = all_stats(L[idx], pc.L_se[idx], pc.L_me[idx])
        for k, v in st.items():
            null_stats[k][t] = v
        if (t + 1) % 2000 == 0:
            print("  perm {}/{}".format(t + 1, NP_))

    emit("| Contrast | Measure | Effect (within-between) | one-sided p | null 2.5% | null 97.5% |")
    emit("|----------|---------|-------------------------|-------------|-----------|------------|")
    for key in sorted(set(k[0] for k in obs_stats)):
        for meas in S_dict:
            o = obs_stats[(key, meas)]
            nu = null_stats[(key, meas)]
            nu = nu[~np.isnan(nu)]
            p = perm_pvalue(o, nu) if o == o and len(nu) else np.nan
            emit("| {} | {} | {:.5f} | {:.4f} | {:.5f} | {:.5f} |".format(
                key, meas, o, p, np.quantile(nu, 0.025) if len(nu) else np.nan,
                np.quantile(nu, 0.975) if len(nu) else np.nan))
            add_row(key, meas, o, p, nu)
    emit()
    for fam in FAMILIES:
        if fam in contrast_fams:
            continue
        j = FAMILIES.index(fam)
        a = L[:, j] > 0
        if a.sum() < 2:
            emit("- {} (descriptive only, {} formats): too few for any "
                 "pair description.".format(fam, int(a.sum())))
            continue
        parts = []
        for meas, S in S_dict.items():
            mw, mb, nw, nb = pair_means(S, a.astype(np.float32))
            parts.append("{} within {:.5f} vs between {:.5f} "
                         "(n={}/{})".format(meas, mw, mb, nw, nb))
        emit("- {} (descriptive only, below the {}-clause bar; {} formats): "
             "{}. No inferential contrast per the ratified rule.".format(
                 fam, config.FAMILY_CONTRAST_MIN_CLAUSES, int(a.sum()),
                 "; ".join(parts)))
    emit()
    emit("(fw_negjsd is negative Jensen-Shannon divergence, so positive "
         "effects = same-function pairs more similar on both measures. "
         "mrqap_beta is the same_function coefficient from "
         "similarity ~ same_function + tag_jaccard + same_type + log-size, "
         "with MRQAP inference under the same label permutations. zerotag "
         "is the within-vs-between contrast restricted to pairs with zero "
         "shared tags.)")
    emit()

    emit("### Pair-level regression (observed coefficients)")
    emit()
    emit("| Measure | same_function | tag_jaccard | same_type | log-size sum |")
    emit("|---------|---------------|-------------|-----------|--------------|")
    m_obs_v = M_obs[iu].astype(np.float64)
    for meas in S_dict:
        Xr = np.column_stack([np.ones(len(m_obs_v)), m_obs_v, pc.jacc_v,
                              pc.stype_v, pc.lsum_v])
        beta, *_ = np.linalg.lstsq(Xr, pc.y_v[meas], rcond=None)
        emit("| {} | {:.5f} | {:.5f} | {:.5f} | {:.5f} |".format(
            meas, beta[1], beta[2], beta[3], beta[4]))
    emit()

    # ------------------------------------------------------------------
    emit("## 4b. Type strata (formats carrying the type; multi-typed formats "
         "in every stratum)")
    emit()
    for stratum in ("exploitable", "image macro", "catchphrase"):
        sub = np.array([stratum in ts for ts in type_sets])
        nsb = int(sub.sum())
        if nsb < 10:
            emit("- {}: only {} formats, skipped.".format(stratum, nsb))
            continue
        sub_idx = np.where(sub)[0]
        Ls = L[sub_idx]
        Ss = {meas: S[np.ix_(sub_idx, sub_idx)] for meas, S in S_dict.items()}
        r = run_headline(Ss, Ls, nsb, NP_, np.random.default_rng(config.RANDOM_SEED),
                         "stratum_" + stratum.replace(" ", "_"))
        for meas, (o, p, nu) in r.items():
            emit("- {} (n={}): {} effect {:.5f}, p={:.4f}".format(
                stratum, nsb, meas, o, p))
    emit()

    # ------------------------------------------------------------------
    emit("## 5. Calibration and flagged classes")
    emit()
    emit("Within-format INSTANCE-level mean similarity per format (capped "
         "instances), by normalised type:")
    emit()
    type_rows = []
    for tname in ("copypasta", "exploitable", "image macro", "catchphrase",
                  "reaction", "snowclone", "character", "slang"):
        sel = np.array([tname in ts for ts in type_sets])
        if sel.sum() < 3:
            continue
        type_rows.append((tname, int(sel.sum()),
                          float(np.nanmedian(fmt_inst_sim[sel, 0])),
                          float(np.nanmedian(fmt_inst_sim[sel, 1]))))
    emit("| Type | Formats | median instance fw_negjsd | median instance pos_cosine |")
    emit("|------|---------|---------------------------|----------------------------|")
    for tname, k, a, b in type_rows:
        emit("| {} | {} | {:.4f} | {:.4f} |".format(tname, k, a, b))
    allmed = (float(np.nanmedian(fmt_inst_sim[:, 0])),
              float(np.nanmedian(fmt_inst_sim[:, 1])))
    emit("| (all formats) | {} | {:.4f} | {:.4f} |".format(n, *allmed))
    emit()

    react_sub = np.array(["reaction" not in ts for ts in type_sets])
    sub_idx = np.where(react_sub)[0]
    Ss = {meas: S[np.ix_(sub_idx, sub_idx)] for meas, S in S_dict.items()}
    r = run_headline(Ss, L[sub_idx], len(sub_idx), NP_,
                     np.random.default_rng(config.RANDOM_SEED), "excl_reaction_type")
    emit("Headline excluding reaction-type formats (n={}, co-text caveat):".format(
        len(sub_idx)))
    for meas, (o, p, nu) in r.items():
        emit("- {}: effect {:.5f}, p={:.4f}".format(meas, o, p))
    emit()

    # ------------------------------------------------------------------
    emit("## 6. Directional checks (prespecified, exploratory)")
    emit()
    cue_names = ["first_person", "second_third_person", "intj",
                 "when_clause", "question_mark"]
    DIRECTIONS = {("RESPOND", "when_clause"): "+", ("RESPOND", "second_third_person"): "+",
                  ("EXPRESS", "first_person"): "+", ("EXPRESS", "intj"): "+",
                  ("EVALUATE", "second_third_person"): "+"}
    brng = np.random.default_rng(config.RANDOM_SEED)
    emit("| Family | Cue | Carrier mean [95% CI] | Non-carrier mean | Diff [95% CI] | Direction | Supported |")
    emit("|--------|-----|----------------------|------------------|---------------|-----------|-----------|")
    for j, fam in enumerate(FAMILIES):
        a = L[:, j] > 0
        if a.sum() < 5:
            continue
        for c, cue in enumerate(cue_names):
            va, vb = fmt_cues[a, c], fmt_cues[~a, c]
            va, vb = va[~np.isnan(va)], vb[~np.isnan(vb)]
            bm, bd = [], []
            for _ in range(config.BOOTSTRAP_N):
                ra = va[brng.integers(0, len(va), len(va))]
                rb = vb[brng.integers(0, len(vb), len(vb))]
                bm.append(ra.mean())
                bd.append(ra.mean() - rb.mean())
            lo, hi = np.quantile(bm, [0.025, 0.975])
            if fam in contrast_fams:
                dlo, dhi = np.quantile(bd, [0.025, 0.975])
                d = va.mean() - vb.mean()
                diff_str = "{:+.4f} [{:+.4f}, {:+.4f}]".format(d, dlo, dhi)
                direc = DIRECTIONS.get((fam, cue), "")
                if direc == "+":
                    supported = "yes" if dlo > 0 else ("no" if dhi < 0 else "n.s.")
                else:
                    supported = ""
            else:
                diff_str, direc, supported = "- (descriptive)", "", ""
            emit("| {} | {} | {:.4f} [{:.4f}, {:.4f}] | {:.4f} | {} | {} | {} |".format(
                fam, cue, va.mean(), lo, hi, vb.mean(), diff_str, direc, supported))
    emit()

    # ------------------------------------------------------------------
    emit("## 7. Robustness: unstripped rerun (headline only)")
    emit()
    Su = unstripped_sims(ns)
    r = run_headline(Su, L, n, NP_, np.random.default_rng(config.RANDOM_SEED),
                     "unstripped")
    for meas, (o, p, nu) in r.items():
        emit("- {}: effect {:.5f}, p={:.4f} (stripped: {:.5f})".format(
            meas, o, p, obs_stats[("headline", meas)]))
    emit()
    emit("Searle crosswalk and EVALUATE->EXPRESS merge are in the section 3 "
         "table (rows 'searle', 'merge_eval'); groups: {} / merge: {}.".format(
             SEARLE_GROUPS, "EVALUATE folded into EXPRESS"))
    emit()

    # ------------------------------------------------------------------
    # figures
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    m_v = M_obs[iu]
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    for ax, meas, lab in zip(axes, ["fw_negjsd", "pos_cosine"],
                             ["FW similarity (-JSD, nats)", "POS-trigram cosine"]):
        sv = pc.y_v[meas]
        ax.hist(sv[m_v], bins=60, alpha=0.6, density=True, label="within (share family)")
        ax.hist(sv[~m_v], bins=60, alpha=0.6, density=True, label="between")
        ax.set_xlabel(lab)
        ax.legend(fontsize=8)
    fig.suptitle("Within- vs between-function pair similarity")
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(figs / ("within_between." + ext), dpi=200)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(10, 4), sharey=True)
    for ax, meas in zip(axes, ["fw_negjsd", "pos_cosine"]):
        ys, effs, los, his = [], [], [], []
        for j, fam in enumerate(FAMILIES):
            if ("fam_" + fam, meas) not in obs_stats:
                continue
            o = obs_stats[("fam_" + fam, meas)]
            nu = null_stats[("fam_" + fam, meas)]
            nu = nu[~np.isnan(nu)]
            if o != o or not len(nu):
                continue
            ys.append(fam)
            effs.append(o)
            los.append(np.quantile(nu, 0.025))
            his.append(np.quantile(nu, 0.975))
        ypos = np.arange(len(ys))
        ax.errorbar(effs, ypos, xerr=None, fmt="o", color="tab:blue", label="observed")
        for y, lo, hi in zip(ypos, los, his):
            ax.plot([lo, hi], [y, y], color="grey", alpha=0.7)
        ax.axvline(0, color="black", lw=0.5)
        ax.set_yticks(ypos)
        ax.set_yticklabels(ys)
        ax.set_title(meas)
    fig.suptitle("Per-family one-vs-rest effects (dots) vs permutation null 95% bands (grey)")
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(figs / ("family_forest." + ext), dpi=200)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    data, labels = [], []
    for tname in ("copypasta", "exploitable", "image macro", "catchphrase",
                  "reaction", "snowclone"):
        sel = np.array([tname in ts for ts in type_sets])
        vals = fmt_inst_sim[sel, 1]
        vals = vals[~np.isnan(vals)]
        if len(vals) >= 3:
            data.append(vals)
            labels.append("{} (n={})".format(tname, len(vals)))
    ax.boxplot(data, labels=labels, vert=True, showfliers=False)
    ax.set_ylabel("within-format instance POS-trigram cosine")
    ax.set_title("Copypasta positive control: instance-level reproduction")
    plt.xticks(rotation=20, ha="right")
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(figs / ("copypasta_ceiling." + ext), dpi=200)
    plt.close(fig)
    emit("Figures written to outputs/figures/ (within_between, family_forest, "
         "copypasta_ceiling; PDF+PNG).")
    emit()

    pd.DataFrame(SUMMARY_ROWS).to_csv(
        config.OUTPUTS_DIR / "pair_stats_summary.csv", index=False,
        encoding="utf-8")
    emit("Wrote outputs/pair_stats_summary.csv ({} rows).".format(len(SUMMARY_ROWS)))
    emit()
    emit("Interpretation happens in chat; paper drafting follows.")

    (config.OUTPUTS_DIR / "analysis_report.md").write_text(
        "\n".join(REPORT_LINES), encoding="utf-8")
    print("Report written to outputs/analysis_report.md")


if __name__ == "__main__":
    main()
