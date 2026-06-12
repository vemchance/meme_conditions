"""05b_exhibits.py - qualitative exhibits per 05B_EXHIBITS_SPEC.md.

Run: python scripts/05b_exhibits.py
Read-only over existing data and the 04-prepared texts; no statistics, no
new claims. Seeded throughout.

Outputs: outputs/exhibits/family_<NAME>.csv (one per family),
outputs/exhibits/shortlists.md, outputs/exhibits/exhibits_index.md.

Safety flag pass (coarse by design; final selection in chat):
- OFFENSIVE: text hits the better_profanity wordlist (LDNOOBW-derived).
- UNCLEAR: text clean but the format carries the KYM 'Sensitive' badge
  (badge inheritance; the dataset has no literal 'NSFW' badge).
- SAFE: neither.
"""
import importlib
import json
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import config

A = importlib.import_module("04_analysis")

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

BINDING_LAYER = {"EVALUATE": "pos", "LABEL": "pos",
                 "EXPRESS": "content", "RESPOND": "content",
                 "CAPTION": "content", "STRUCTURAL": "content",
                 "DIRECT": "content"}
WHEN_RX = re.compile(r"(?:^|[.!?,;:]\s*)when\b", re.IGNORECASE)
LABELLING_RX = re.compile(
    r"\b(?:be like|is a|are a|called|literally|me as|that one)\b",
    re.IGNORECASE)


def log(line=""):
    print(line)


def neg_jsd_to_centroid(P, cent):
    """-JSD of each row of P against the centroid distribution."""
    out = np.zeros(len(P))
    cl = np.zeros_like(cent)
    np.log(cent, where=cent > 0, out=cl)
    Hc = -(cent * cl).sum()
    for i in range(len(P)):
        p = P[i]
        m = 0.5 * (p + cent)
        lm = np.zeros_like(m)
        np.log(m, where=m > 0, out=lm)
        lp = np.zeros_like(p)
        np.log(p, where=p > 0, out=lp)
        Hm = -(m * lm).sum()
        Hp = -(p * lp).sum()
        out[i] = -(Hm - 0.5 * Hp - 0.5 * Hc)
    return out


def cos_to_centroid(M, cent):
    cn = cent / max(np.linalg.norm(cent), 1e-9)
    Mn = M / np.maximum(np.linalg.norm(M, axis=1, keepdims=True), 1e-9)
    return Mn @ cn


def trunc(t, n=250):
    t = " ".join(str(t).split())
    return t if len(t) <= n else t[:n] + "..."


def main():
    out_dir = config.OUTPUTS_DIR / "exhibits"
    out_dir.mkdir(parents=True, exist_ok=True)

    ns = A.prepare(log)
    if ns is None:
        return
    n, L = ns.n, ns.L
    Fset = set(ns.F)
    rng = np.random.default_rng(config.RANDOM_SEED)

    from better_profanity import profanity
    profanity.load_censor_words()

    entries = pd.read_csv(config.ENTRIES_CSV, dtype=str, low_memory=False,
                          usecols=["ID", "Badges:"])
    sensitive = set(entries.loc[
        entries["Badges:"].fillna("").str.contains("Sensitive"), "ID"])

    def flag_text(text, fid):
        if profanity.contains_profanity(str(text)):
            return "OFFENSIVE"
        if fid in sensitive:
            return "UNCLEAR"
        return "SAFE"

    # layers
    inst = ns.kept[ns.kept["format_id"].isin(Fset)].reset_index(drop=True)
    fmt_rows = np.array([ns.fid_index[f] for f in inst["format_id"]])
    kept_counts = inst.groupby("format_id").size()

    log("  encoding content embeddings (deterministic repeat)...")
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(config.CONTENT_MODEL, device="cuda")
    emb = model.encode(inst["text_stripped"].tolist(), batch_size=256,
                       convert_to_numpy=True, normalize_embeddings=True
                       ).astype(np.float32)
    Cc = np.zeros((n, emb.shape[1]), np.float32)
    np.add.at(Cc, fmt_rows, emb)
    Cc /= np.maximum(np.bincount(fmt_rows, minlength=n)[:, None], 1.0)

    log("  loading visual centroids...")
    meta_files = sorted(config.VISION_METADATA_DIR.glob("metadata_chunk_*.json"))
    emb_files = sorted(config.VISION_EMBEDDINGS_DIR.glob("embeddings_chunk_*.npy"))
    fname_to_loc = {}
    for ci, mf in enumerate(meta_files):
        m = json.loads(Path(mf).read_text())
        for ri, im in enumerate(m["valid_images"]):
            fname_to_loc[im["filename"]] = (ci, ri)
    by_chunk = defaultdict(list)
    locs = inst["file"].map(fname_to_loc.get)
    for pos, loc in enumerate(locs):
        if isinstance(loc, tuple):
            by_chunk[loc[0]].append((loc[1], pos))
    V = np.zeros((len(inst), 768), np.float32)
    have = np.zeros(len(inst), bool)
    for ci, pairs in sorted(by_chunk.items()):
        arr = np.load(emb_files[ci], mmap_mode="r")
        rows = np.array([r for r, _ in pairs])
        poss = np.array([p for _, p in pairs])
        order = np.argsort(rows)
        V[poss[order]] = np.asarray(arr[rows[order]])
        have[poss] = True
    V /= np.maximum(np.linalg.norm(V, axis=1, keepdims=True), 1e-9)
    Cv = np.zeros((n, 768), np.float32)
    cntv = np.zeros(n, np.float32)
    np.add.at(Cv, fmt_rows[have], V[have])
    np.add.at(cntv, fmt_rows[have], 1.0)
    Cv /= np.maximum(cntv[:, None], 1.0)

    texts_by_fmt = dict(tuple(inst.groupby("format_id")))
    clauses = ns.clauses
    clause_by_fid_fam = defaultdict(list)
    for _, r in clauses.iterrows():
        if r["entry_id"] in Fset and r["label_v2"] in A.FAMILIES:
            clause_by_fid_fam[(r["entry_id"], r["label_v2"])].append(
                (r["clause"], r["predicate"], r["comp_head"]))

    index_lines = ["# Exhibits index (05B_EXHIBITS_SPEC.md)", "",
                   "Generated {} with seed {}. Read-only; no statistics. "
                   "Safety flags: {} + KYM 'Sensitive' badge inheritance "
                   "(dataset has no literal NSFW badge); coarse by design, "
                   "final selection in chat.".format(
                       datetime.now().strftime("%Y-%m-%d %H:%M"),
                       config.RANDOM_SEED, config.EXHIBIT_SLUR_LIST), ""]
    md = ["# Shortlists and cell illustrations (05B_EXHIBITS_SPEC.md)", "",
          "Safety flags inline: [SAFE] / [OFFENSIVE] / [UNCLEAR]. "
          "Texts are the post-stripping fills actually analysed, "
          "truncated to 250 chars.", ""]

    shortlists = {}
    for j, fam in enumerate(A.FAMILIES):
        carriers = [i for i in range(n) if L[i, j] > 0]
        if not carriers:
            continue
        car_ids = [ns.F[i] for i in carriers]

        # family centroids per layer
        sim = {}
        Pp = ns.P[carriers]
        sim["fw"] = neg_jsd_to_centroid(ns.P, Pp.mean(0))
        sim["pos"] = cos_to_centroid(ns.X, ns.X[carriers].mean(0))
        sim["content"] = cos_to_centroid(Cc, Cc[carriers].mean(0))
        sim["visual"] = cos_to_centroid(Cv, Cv[carriers].mean(0))

        # §1 full carrier table
        rows = []
        for i, fid in zip(carriers, car_ids):
            cls = clause_by_fid_fam.get((fid, fam), [])
            rows.append({
                "title": ns.titles[i],
                "entry_id": fid,
                "types": ";".join(sorted(ns.type_sets[i])),
                "n_instances_prepared": int(kept_counts.get(fid, 0)),
                "clauses": " || ".join(
                    "{} [{}/{}]".format(" ".join(str(c).split()), p, h)
                    for c, p, h in cls),
                "sensitive_badge": fid in sensitive,
                "sim_fw_centroid": round(float(sim["fw"][i]), 5),
                "sim_pos_centroid": round(float(sim["pos"][i]), 5),
                "sim_content_centroid": round(float(sim["content"][i]), 5),
                "sim_visual_centroid": round(float(sim["visual"][i]), 5),
            })
        fam_csv = out_dir / "family_{}.csv".format(fam)
        pd.DataFrame(rows).to_csv(fam_csv, index=False, encoding="utf-8")
        index_lines.append("- family_{}.csv - all {} population carriers "
                           "({} rows) with clauses, badges, centroid "
                           "similarities".format(fam, fam, len(rows)))

        # §2 shortlist: 4 closest on binding layer + 4 seeded-random
        lay = BINDING_LAYER[fam]
        order = sorted(carriers, key=lambda i: -sim[lay][i])
        closest = order[:4]
        rest = [i for i in carriers if i not in closest]
        rand = list(rng.choice(rest, size=min(4, len(rest)), replace=False)) \
            if rest else []
        shortlists[fam] = (closest, rand, lay)

        md.append("## {} (binding layer for shortlist: {})".format(fam, lay))
        md.append("")
        for group, members in (("closest to family centroid", closest),
                               ("seeded random carriers", rand)):
            for i in members:
                fid = ns.F[int(i)]
                md.append("### {} - {} [{}] ({}; {} prepared instances; "
                          "centroid sim {} = {:.4f})".format(
                              fam, ns.titles[int(i)], fid, group,
                              int(kept_counts.get(fid, 0)), lay,
                              float(sim[lay][int(i)])))
                if fid in sensitive:
                    md.append("(Sensitive badge - texts inherit UNCLEAR)")
                md.append("")
                g = texts_by_fmt[fid]
                pick = g.sample(n=min(config.EXHIBIT_TEXTS_PER_FORMAT, len(g)),
                                random_state=config.RANDOM_SEED)
                for t in pick["text_stripped"]:
                    md.append("- [{}] {}".format(flag_text(t, fid), trunc(t)))
                md.append("")

    # ------------------------------------------------------------------
    # §3 cell illustrations
    md.append("# Cell illustrations")
    md.append("")

    def fam_short_ids(fam):
        closest, rand, _ = shortlists[fam]
        return [ns.F[int(i)] for i in list(closest) + list(rand)]

    md.append("## EVALUATE: question-mark fills (up to 5 per shortlist format)")
    md.append("")
    for fid in fam_short_ids("EVALUATE"):
        g = texts_by_fmt[fid]
        qs = g[g["text_stripped"].str.contains(r"\?", regex=True)]
        if not len(qs):
            continue
        md.append("**{}** [{}]:".format(
            ns.titles[ns.fid_index[fid]], fid))
        pick = qs.sample(n=min(5, len(qs)), random_state=config.RANDOM_SEED)
        for t in pick["text_stripped"]:
            md.append("- [{}] {}".format(flag_text(t, fid), trunc(t)))
        md.append("")

    md.append("## RESPOND: when-clause fills (up to 5 per shortlist format)")
    md.append("")
    for fid in fam_short_ids("RESPOND"):
        g = texts_by_fmt[fid]
        ws = g[g["text_stripped"].str.contains(WHEN_RX)]
        if not len(ws):
            continue
        md.append("**{}** [{}]:".format(ns.titles[ns.fid_index[fid]], fid))
        pick = ws.sample(n=min(5, len(ws)), random_state=config.RANDOM_SEED)
        for t in pick["text_stripped"]:
            md.append("- [{}] {}".format(flag_text(t, fid), trunc(t)))
        md.append("")

    md.append("## LABEL: fills matching labelling-construction cues "
              "(heuristic patterns: be like / is a / are a / called / "
              "literally / me as / that one; up to 5 per shortlist format)")
    md.append("")
    for fid in fam_short_ids("LABEL"):
        g = texts_by_fmt[fid]
        ls = g[g["text_stripped"].str.contains(LABELLING_RX)]
        if not len(ls):
            continue
        md.append("**{}** [{}]:".format(ns.titles[ns.fid_index[fid]], fid))
        pick = ls.sample(n=min(5, len(ls)), random_state=config.RANDOM_SEED)
        for t in pick["text_stripped"]:
            md.append("- [{}] {}".format(flag_text(t, fid), trunc(t)))
        md.append("")

    md.append("## EXPRESS: discrete-head groups (content binding with form "
              "variety; heads with >= {} formats)".format(
                  config.COMPLEMENT_MIN_FORMATS_PER_HEAD))
    md.append("")
    stop = set(config.COMPLEMENT_HEAD_STOPLIST)
    jx = A.FAMILIES.index("EXPRESS")
    ex = clauses[(clauses["label_v2"] == "EXPRESS") &
                 clauses["entry_id"].isin(Fset)]
    head_formats = defaultdict(set)
    for fid, h in zip(ex["entry_id"], ex["comp_head"]):
        if (isinstance(h, str) and h.strip()
                and h.strip().lower() not in stop
                and fid in ns.fid_index
                and L[ns.fid_index[fid], jx] > 0):
            head_formats[h.strip().lower()].add(fid)
    for h in sorted(head_formats, key=lambda x: -len(head_formats[x])):
        fids = sorted(head_formats[h])
        if len(fids) < config.COMPLEMENT_MIN_FORMATS_PER_HEAD:
            continue
        md.append("### head: {} ({} formats)".format(h, len(fids)))
        md.append("")
        for fid in fids:
            md.append("**{}** [{}]:".format(ns.titles[ns.fid_index[fid]], fid))
            g = texts_by_fmt.get(fid)
            if g is None:
                continue
            pick = g.sample(n=min(3, len(g)), random_state=config.RANDOM_SEED)
            for t in pick["text_stripped"]:
                md.append("- [{}] {}".format(flag_text(t, fid), trunc(t)))
        md.append("")

    md.append("## CAPTION: anti-coherence (two lowest within-format form "
              "self-similarity carriers, ten texts each)")
    md.append("")
    jc = A.FAMILIES.index("CAPTION")
    cap = [i for i in range(n) if L[i, jc] > 0
           and ns.fmt_inst_sim[i, 1] == ns.fmt_inst_sim[i, 1]]
    for i in sorted(cap, key=lambda i: ns.fmt_inst_sim[i, 1])[:2]:
        fid = ns.F[i]
        md.append("**{}** [{}] (within-format instance POS cosine = "
                  "{:.4f}):".format(ns.titles[i], fid, ns.fmt_inst_sim[i, 1]))
        g = texts_by_fmt[fid]
        pick = g.sample(n=min(10, len(g)), random_state=config.RANDOM_SEED)
        for t in pick["text_stripped"]:
            md.append("- [{}] {}".format(flag_text(t, fid), trunc(t)))
        md.append("")

    md.append("## Copypasta ceiling: near-verbatim repetition")
    md.append("")
    cp = [i for i in range(n) if "copypasta" in ns.type_sets[i]
          and ns.fmt_inst_sim[i, 1] == ns.fmt_inst_sim[i, 1]]
    if cp:
        i = max(cp, key=lambda i: ns.fmt_inst_sim[i, 1])
        fid = ns.F[i]
        md.append("**{}** [{}] (within-format instance POS cosine = "
                  "{:.4f}):".format(ns.titles[i], fid, ns.fmt_inst_sim[i, 1]))
        g = texts_by_fmt[fid]
        pick = g.sample(n=min(10, len(g)), random_state=config.RANDOM_SEED)
        for t in pick["text_stripped"]:
            md.append("- [{}] {}".format(flag_text(t, fid), trunc(t)))
        md.append("")

    (out_dir / "shortlists.md").write_text("\n".join(md), encoding="utf-8")
    index_lines += [
        "- shortlists.md - per-family shortlists (4 centroid-closest + 4 "
        "seeded-random, {} texts each, safety flags inline) and the cell "
        "illustrations (EVALUATE question-marks, RESPOND when-clauses, "
        "LABEL labelling cues, EXPRESS discrete-head groups, CAPTION "
        "anti-coherence, copypasta ceiling)".format(
            config.EXHIBIT_TEXTS_PER_FORMAT),
        "- exhibits_index.md - this file", ""]
    (out_dir / "exhibits_index.md").write_text(
        "\n".join(index_lines), encoding="utf-8")
    print("Wrote outputs/exhibits/ ({} family CSVs + shortlists.md + "
          "exhibits_index.md)".format(
              len([f for f in A.FAMILIES if (out_dir / (
                  'family_' + f + '.csv')).exists()])))


if __name__ == "__main__":
    main()
