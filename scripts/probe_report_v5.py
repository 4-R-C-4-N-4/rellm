"""Analyze v5 backfill probe: did held-out older-tradition cells fire the target
backfill concept, v5 vs v4 vs base? And did the guards stay silent?

Usage: python scripts/probe_report_v5.py <probe_dir> <manifest.json>
  <probe_dir> holds base.jsonl / v4.jsonl / v5.jsonl from `rellm tag`.
"""
import json, sys, collections
from pathlib import Path

probe_dir = Path(sys.argv[1])
manifest = json.load(open(sys.argv[2]))
MODELS = ["base", "v4", "v5"]


def load(model):
    p = probe_dir / f"{model}.jsonl"
    out = {}
    if not p.exists():
        return out
    for line in p.open():
        r = json.loads(line)
        out[r["chunk_id"]] = {t["concept_id"]: t["score"] for t in r.get("tags", [])}
    return out


tagged = {m: load(m) for m in MODELS}
fire = [m for m in manifest if m["expect"] == "FIRE"]
guards = [m for m in manifest if m["expect"] == "SILENT"]

# ---- FIRE: per-concept recall (target scored >=2, and >=1) ----
by_concept = collections.defaultdict(list)
for cell in fire:
    by_concept[cell["target"]].append(cell["chunk_id"])

print(f"FIRE — {len(fire)} held-out older-tradition cells across {len(by_concept)} backfill concepts")
print("(recall = target concept fired on the cell; the tag is a vetted positive there)\n")
hdr = f"  {'concept':<20} {'n':>2}  " + "  ".join(f"{m:>11}" for m in MODELS)
print(hdr); print("  " + "-" * (len(hdr) - 2))
tot = {m: [0, 0, 0] for m in MODELS}  # fired>=2, fired>=1, n
for c in sorted(by_concept, key=lambda k: -len(by_concept[k])):
    cids = by_concept[c]
    row = f"  {c:<20} {len(cids):>2}  "
    parts = []
    for m in MODELS:
        f2 = sum(1 for cid in cids if tagged[m].get(cid, {}).get(c, 0) >= 2)
        f1 = sum(1 for cid in cids if tagged[m].get(cid, {}).get(c, 0) >= 1)
        parts.append(f"{f2}/{f1}/{len(cids):>2}")
        tot[m][0] += f2; tot[m][1] += f1; tot[m][2] += len(cids)
    print(row + "  ".join(f"{p:>11}" for p in parts))
print("  " + "-" * (len(hdr) - 2))
print(f"  {'TOTAL (≥2 / ≥1 / n)':<20} {len(fire):>2}  " +
      "  ".join(f"{tot[m][0]}/{tot[m][1]}/{tot[m][2]:>2}".rjust(11) for m in MODELS))

# ---- per-cell detail (score grid) ----
print("\nPer-cell target score (0 = missed):")
print(f"  {'target':<18} {'split':<5} {'chunk':<52} " + " ".join(f"{m:>4}" for m in MODELS))
for cell in sorted(fire, key=lambda x: (x["target"], x["chunk_id"])):
    cid, c = cell["chunk_id"], cell["target"]
    scores = " ".join(f"{tagged[m].get(cid, {}).get(c, 0):>4}" for m in MODELS)
    print(f"  {c:<18} {cell['split']:<5} {cid:<52} {scores}")

# ---- guards ----
print("\nGUARDS — kalevala: psychic_attack must be SILENT, route to word_power_incantation")
print(f"  {'chunk':<24} " + " ".join(f"{m+':pa/wp':>12}" for m in MODELS))
for cell in guards:
    cid = cell["chunk_id"]
    cols = []
    for m in MODELS:
        pa = tagged[m].get(cid, {}).get("psychic_attack", 0)
        wp = tagged[m].get(cid, {}).get("word_power_incantation", 0)
        cols.append(f"{pa}/{wp}")
    print(f"  {cid:<24} " + " ".join(f"{c:>12}" for c in cols))

# ---- occult_police must fire NOWHERE across all probe chunks ----
print("\nHallucination guard — occult_police anywhere in probe:")
for m in MODELS:
    hits = [cid for cid, tg in tagged[m].items() if tg.get("occult_police", 0) >= 1]
    print(f"  {m:<6} {'CLEAN (0)' if not hits else 'FIRED: ' + ', '.join(hits)}")
