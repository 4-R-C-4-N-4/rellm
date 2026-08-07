#!/usr/bin/env python3
"""Layer x pooling x method sweep of concept directions against the gold set.

    .venv/bin/python tools/homology_sweep.py --states data/homology/directions/<slug>

Selection tunes on the TUNE half only; the winning config is then reported on
the held-out TEST half (amendment A5). Baseline to beat (nomic embedding
centroids): Spearman +0.15, tail AUC 0.61.
"""
import argparse
import json
from pathlib import Path

from rellm.config import load
from rellm.homology.directions import build_directions, cell_table, load_states
from rellm.homology.geometry import Scorer
from rellm.homology.goldset import load_gold, metrics, pair_key, split


def evaluate(scorer: Scorer, gold: list[dict]) -> tuple[dict, list[dict]]:
    scored, rows = [], []
    for g in gold:
        a, b = pair_key(g)
        pct = scorer.percentile(a, b)
        rows.append({"id": g["id"], "rating": g["verdict"],
                     "cosine": scorer.cosine(a, b), "percentile": pct})
        if pct is not None:
            scored.append((g["verdict"], pct))
    return metrics(scored), rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--states", required=True)
    ap.add_argument("--methods", default="dom,cen")
    args = ap.parse_args()

    cfg = load()
    states_dir = Path(args.states)
    states, manifest, row = load_states(states_dir)
    cells, tagged, trad_rows, row_work = cell_table(cfg, row)

    gold_path = cfg.rellm.root / "data" / "homology" / "gold" / "ratified.jsonl"
    gold = load_gold(gold_path)
    tune, test = split(gold)
    print(f"model={manifest['model']}  layers={manifest['n_layers']}  "
          f"cells={len(cells)}  gold tune/test={len(tune)}/{len(test)}")

    results = []
    for layer in range(manifest["n_layers"]):
        for p_i, pooling in enumerate(manifest["poolings"]):
            sl = states[:, layer, p_i, :].astype("float32")
            for method in args.methods.split(","):
                dirs = build_directions(sl, cells, tagged, trad_rows, row_work, method)
                m, _ = evaluate(Scorer(dirs), tune)
                results.append({"layer": layer, "pooling": pooling,
                                "method": method, "tune": m})
        best_here = max((r for r in results if r["layer"] == layer),
                        key=lambda r: r["tune"]["spearman"])
        print(f"  L{layer:2d} best: {best_here['method']}/{best_here['pooling']} "
              f"rho={best_here['tune']['spearman']:+.3f} "
              f"auc={best_here['tune']['tail_auc']:.3f}", flush=True)

    best = max(results, key=lambda r: r["tune"]["spearman"])
    sl = states[:, best["layer"], manifest["poolings"].index(best["pooling"]), :].astype("float32")
    dirs = build_directions(sl, cells, tagged, trad_rows, row_work, best["method"])
    scorer = Scorer(dirs)
    test_m, test_rows = evaluate(scorer, test)
    full_m, full_rows = evaluate(scorer, gold)

    report = {
        "model": manifest["model"],
        "extracted_at": manifest["extracted_at"],
        "selected": {k: best[k] for k in ("layer", "pooling", "method")},
        "tune_metrics": best["tune"],
        "test_metrics": test_m,
        "full_metrics": full_m,
        "baseline_to_beat": {"spearman": 0.147, "tail_auc": 0.606},
        "sweep": results,
        "pairs_full": sorted(full_rows,
                             key=lambda r: -(r["percentile"] or 0)),
    }
    out = cfg.rellm.root / "data" / "homology" / "baseline" / (
        "sweep-" + manifest["model"].replace("/", "--") + ".json")
    out.write_text(json.dumps(report, indent=1))

    print(f"\nselected: layer {best['layer']}  {best['method']}/{best['pooling']}")
    print(f"tune : {best['tune']}")
    print(f"test : {test_m}")
    print(f"full : {full_m}")
    print(f"report -> {out}")


if __name__ == "__main__":
    main()
