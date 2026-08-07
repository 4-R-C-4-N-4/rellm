"""Hidden-state extraction: every corpus chunk → pooled residual-stream states.

One forward pass per chunk caches all layers × both poolings, so the whole
layer/pooling sweep downstream is array math against a single artifact:

    <out>/states.npy      float16 memmap, shape (n_chunks, n_layers, 2, dim)
                          pooling axis: 0 = mean over content tokens, 1 = last token
    <out>/manifest.json   chunk id order + provenance (artifact identity)
"""
from __future__ import annotations

import json
import time
from datetime import date
from pathlib import Path

import numpy as np

from ..config import Config
from ..corpus import chunk_body
from ..db import open_db

POOLINGS = ("mean", "last")


def corpus_chunks(cfg: Config) -> list[tuple[str, str]]:
    """[(chunk_id, body)] for every chunk node with a resolvable body."""
    with open_db(cfg.guru.db) as db:
        ids = [r["id"] for r in db.execute(
            "SELECT id FROM nodes WHERE type='chunk' ORDER BY id")]
    out = []
    for cid in ids:
        body = chunk_body(cid, cfg.guru.corpus_dir)
        if body:
            out.append((cid, body))
    return out


def extract(cfg: Config, model_id: str, out_dir: Path,
            max_tokens: int = 1024, batch_tokens: int = 8192) -> Path:
    import torch
    from transformers import AutoModel, AutoTokenizer

    chunks = corpus_chunks(cfg)
    tok = AutoTokenizer.from_pretrained(model_id)
    model = AutoModel.from_pretrained(model_id, dtype=torch.bfloat16).to("cuda").eval()

    n_layers = model.config.num_hidden_layers + 1  # + embedding layer
    dim = model.config.hidden_size

    out_dir.mkdir(parents=True, exist_ok=True)
    states = np.lib.format.open_memmap(
        out_dir / "states.npy", mode="w+", dtype=np.float16,
        shape=(len(chunks), n_layers, len(POOLINGS), dim))

    # tokenize once, then bucket by length so batches stay dense
    encoded = [tok(body, truncation=True, max_length=max_tokens)["input_ids"]
               for _, body in chunks]
    order = sorted(range(len(chunks)), key=lambda i: len(encoded[i]))

    t0, done = time.time(), 0
    batch: list[int] = []

    def flush(batch: list[int]) -> None:
        nonlocal done
        if not batch:
            return
        maxlen = max(len(encoded[i]) for i in batch)
        ids = torch.full((len(batch), maxlen), tok.pad_token_id, dtype=torch.long)
        mask = torch.zeros((len(batch), maxlen), dtype=torch.long)
        for r, i in enumerate(batch):
            seq = torch.tensor(encoded[i])
            ids[r, :len(seq)] = seq
            mask[r, :len(seq)] = 1
        ids, mask = ids.to("cuda"), mask.to("cuda")
        with torch.inference_mode():
            hs = model(input_ids=ids, attention_mask=mask,
                       output_hidden_states=True).hidden_states
        # pool one layer at a time: a single fp32 layer is ~100 MB, the full
        # fp32 stack (~3 GB x2) OOMs next to the bf16 weights
        B = ids.shape[0]
        m = mask[:, :, None].float()
        denom = m.sum(1)                            # (B, 1)
        last_idx = mask.sum(1) - 1                  # (B,)
        rows = torch.arange(B, device=ids.device)
        pooled = np.empty((B, len(hs), len(POOLINGS), hs[0].shape[-1]),
                          dtype=np.float16)
        for li, h in enumerate(hs):
            hf = h.float()                          # (B, T, D)
            pooled[:, li, 0] = ((hf * m).sum(1) / denom).to(torch.float16).cpu().numpy()
            pooled[:, li, 1] = hf[rows, last_idx].to(torch.float16).cpu().numpy()
        del hs
        for r, i in enumerate(batch):
            states[i] = pooled[r]
        done += len(batch)
        if done % 500 < len(batch):
            rate = done / (time.time() - t0)
            print(f"  {done}/{len(chunks)} chunks  ({rate:.1f}/s)", flush=True)

    for i in order:
        cand = batch + [i]
        if cand and len(cand) * max(len(encoded[j]) for j in cand) > batch_tokens:
            flush(batch)
            batch = [i]
        else:
            batch = cand
    flush(batch)
    states.flush()

    manifest = {
        "model": model_id,
        "extracted_at": date.today().isoformat(),
        "n_chunks": len(chunks),
        "n_layers": n_layers,
        "dim": dim,
        "poolings": list(POOLINGS),
        "max_tokens": max_tokens,
        "chunk_ids": [cid for cid, _ in chunks],
        "guru_db": str(cfg.guru.db),
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=1))
    print(f"wrote {states.shape} float16 -> {out_dir}")
    return out_dir
