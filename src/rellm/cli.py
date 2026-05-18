"""rellm CLI."""
from __future__ import annotations

import json
import shutil
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import typer

from rellm.config import load as load_config
from rellm.corpus import chunk_body, chunk_citation
from rellm.db import open_db
from rellm.extract import iter_teacher_chunks
from rellm.formats import (
    SYSTEM_PROMPT,
    build_user_prompt,
    parse_model_tags,
    write_sft_jsonl,
)
from rellm.splits import write_split_manifest
from rellm.taxonomy import load_taxonomy


app = typer.Typer(
    help="rellm — distill the guru chunk→concept tagger.",
    no_args_is_help=True,
    add_completion=False,
)


def _resolve_db(cfg, snapshot: Path | None) -> Path:
    if snapshot is not None:
        return snapshot / "guru.db" if snapshot.is_dir() else snapshot
    latest = _latest_snapshot(cfg.rellm.snapshots)
    if latest is not None:
        return latest / "guru.db"
    fallback = cfg.rellm.data_dir / "guru.db"
    if fallback.exists():
        return fallback
    raise typer.BadParameter(
        f"no snapshot found in {cfg.rellm.snapshots} and no {fallback}; "
        f"run `rellm snapshot` first"
    )


def _latest_snapshot(snapshots_dir: Path) -> Path | None:
    if not snapshots_dir.exists():
        return None
    cands = sorted(d for d in snapshots_dir.iterdir() if d.is_dir())
    return cands[-1] if cands else None


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")


@app.command()
def stats(
    snapshot: Path = typer.Option(None, help="Snapshot path (file or dir); else latest, else data/guru.db"),
):
    """Counts of teacher data available for distillation."""
    cfg = load_config()
    db = _resolve_db(cfg, snapshot)
    typer.echo(f"snapshot: {db}")
    with open_db(db) as conn:
        rows = conn.execute("""
            SELECT model, prompt_version, status, COUNT(*) AS n
            FROM staged_tags
            GROUP BY model, prompt_version, status
            ORDER BY n DESC
        """).fetchall()
        for r in rows:
            typer.echo(
                f"  {r['model']:<42} {r['prompt_version']:<6} "
                f"{r['status']:<10} {r['n']:>6}"
            )
        typer.echo("")
        teacher_total = conn.execute(
            "SELECT COUNT(*) FROM staged_tags WHERE model = ? AND prompt_version = ?",
            (cfg.model.teacher, cfg.prompt.version),
        ).fetchone()[0]
        chunks_with_teacher = conn.execute(
            "SELECT COUNT(DISTINCT chunk_id) FROM staged_tags "
            "WHERE model = ? AND prompt_version = ?",
            (cfg.model.teacher, cfg.prompt.version),
        ).fetchone()[0]
        typer.echo(
            f"teacher={cfg.model.teacher} prompt={cfg.prompt.version}: "
            f"{teacher_total} tags across {chunks_with_teacher} chunks"
        )


@app.command()
def snapshot(
    label: str = typer.Option(None, help="Optional label suffix"),
):
    """Mirror the live guru.db into data/snapshots/<ts>/."""
    cfg = load_config()
    if not cfg.guru.db.exists():
        raise typer.BadParameter(f"guru.db not found at {cfg.guru.db}")
    name = f"{_ts()}-{label}" if label else _ts()
    dst = cfg.rellm.snapshots / name
    dst.mkdir(parents=True, exist_ok=True)
    shutil.copy2(cfg.guru.db, dst / "guru.db")

    manifest: dict = {"created_at": _ts(), "source": str(cfg.guru.db)}
    with open_db(dst / "guru.db") as conn:
        for q, k in [
            ("SELECT COUNT(*) FROM nodes WHERE type='chunk'", "chunks"),
            ("SELECT COUNT(*) FROM nodes WHERE type='concept'", "concepts"),
            ("SELECT COUNT(*) FROM staged_tags WHERE status='pending'", "staged_pending"),
            ("SELECT COUNT(*) FROM staged_tags WHERE status='accepted'", "staged_accepted"),
            ("SELECT COUNT(*) FROM staged_tags WHERE status='rejected'", "staged_rejected"),
            ("SELECT COUNT(*) FROM edges WHERE type='EXPRESSES'", "edges_expresses"),
        ]:
            manifest[k] = conn.execute(q).fetchone()[0]
    (dst / "manifest.json").write_text(json.dumps(manifest, indent=2))
    typer.echo(f"wrote {dst}")
    typer.echo(json.dumps(manifest, indent=2))


@app.command()
def export(
    snapshot: Path = typer.Option(None, help="Snapshot path; else latest"),
    limit: int = typer.Option(0, help="Max chunks (0 = no limit)"),
    out: Path = typer.Option(None, help="Output jsonl; else data/exports/<ts>/sft.jsonl"),
    status: str = typer.Option("pending,accepted", help="Comma-separated staged_tags statuses to include"),
):
    """Emit SFT jsonl: (chunk + full taxonomy) → teacher JSON tags."""
    cfg = load_config()
    db_path = _resolve_db(cfg, snapshot)

    if out is None:
        out_dir = cfg.rellm.exports / _ts()
        out_dir.mkdir(parents=True, exist_ok=True)
        out = out_dir / "sft.jsonl"
    else:
        out.parent.mkdir(parents=True, exist_ok=True)

    statuses = tuple(s.strip() for s in status.split(",") if s.strip())
    concepts = load_taxonomy(cfg.guru.taxonomy)

    with open_db(db_path) as conn:
        chunks = iter_teacher_chunks(
            conn,
            cfg.guru.corpus_dir,
            teacher_model=cfg.model.teacher,
            prompt_version=cfg.prompt.version,
            status=statuses,
            limit=limit or None,
        )
        n = write_sft_jsonl(chunks, concepts, out)

    manifest = {
        "created_at": _ts(),
        "snapshot": str(db_path),
        "teacher": cfg.model.teacher,
        "prompt_version": cfg.prompt.version,
        "status_filter": list(statuses),
        "n_examples": n,
        "n_concepts": len(concepts),
    }
    (out.parent / "export-manifest.json").write_text(json.dumps(manifest, indent=2))
    typer.echo(f"wrote {n} examples to {out}")


@app.command()
def splits(
    export_dir: Path = typer.Argument(..., help="Export dir containing sft.jsonl"),
    val: float = typer.Option(0.05),
    test: float = typer.Option(0.05),
):
    """Write a chunk-id split manifest alongside an existing export."""
    jsonl = export_dir / "sft.jsonl"
    if not jsonl.exists():
        raise typer.BadParameter(f"{jsonl} not found")
    chunk_ids: list[str] = []
    with jsonl.open() as f:
        for line in f:
            chunk_ids.append(json.loads(line)["chunk_id"])
    manifest = write_split_manifest(chunk_ids, export_dir / "splits.json", val=val, test=test)
    typer.echo(json.dumps(manifest["counts"], indent=2))


def _call_server(
    endpoint: str, system: str, user: str,
    temperature: float, max_tokens: int, timeout: float,
) -> str:
    body = json.dumps({
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }).encode()
    req = urllib.request.Request(
        f"{endpoint.rstrip('/')}/v1/chat/completions",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())["choices"][0]["message"]["content"]


@app.command()
def tag(
    chunk_ids: list[str] = typer.Argument(
        None, help="Chunk IDs to tag; omit to read one per line from stdin",
    ),
    endpoint: str = typer.Option(
        "http://127.0.0.1:8080", help="llama-server base URL",
    ),
    snapshot: Path = typer.Option(
        None, help="Snapshot path (file or dir); else latest, else data/guru.db",
    ),
    out: Path = typer.Option(None, help="Output JSONL path; default stdout"),
    text_file: Path = typer.Option(
        None, "--text-file",
        help="Tag arbitrary text from FILE instead of looking up chunk IDs",
    ),
    citation: str = typer.Option(
        "ad-hoc passage", "--citation",
        help="Citation string when using --text-file",
    ),
    tradition: str = typer.Option(
        None, "--tradition",
        help="Tradition id when using --text-file",
    ),
    temperature: float = typer.Option(0.0),
    max_tokens: int = typer.Option(4096),
    timeout: float = typer.Option(180.0),
):
    """Tag chunks via a running llama-server.

    Chunk-id mode (default): looks each ID up in the latest snapshot,
    builds the standard rellm prompt, and prints a JSONL record per chunk.

        rellm tag <chunk_id> [<chunk_id> ...]
        sqlite3 guru.db "SELECT id FROM nodes WHERE ..." | rellm tag

    Ad-hoc mode (--text-file): tags one passage from a file, using --citation
    and --tradition you provide.
    """
    cfg = load_config()
    concepts = load_taxonomy(cfg.guru.taxonomy)
    sink = out.open("w") if out else sys.stdout

    def emit(record: dict) -> None:
        sink.write(json.dumps(record, ensure_ascii=False) + "\n")
        sink.flush()

    def tag_one(body: str, cite: str, *, chunk_id: str, tradition_id: str | None) -> dict:
        user = build_user_prompt(body, cite, concepts)
        t0 = time.monotonic()
        raw, err = "", None
        try:
            raw = _call_server(endpoint, SYSTEM_PROMPT, user,
                               temperature, max_tokens, timeout)
        except (urllib.error.URLError, TimeoutError, KeyError, json.JSONDecodeError) as e:
            err = f"{type(e).__name__}: {e}"
        dt = time.monotonic() - t0
        parse_ok, scores = parse_model_tags(raw)
        return {
            "chunk_id": chunk_id,
            "tradition_id": tradition_id,
            "citation": cite,
            "latency_s": round(dt, 2),
            "parse_ok": parse_ok,
            "error": err,
            "tags": [{"concept_id": k, "score": v} for k, v in sorted(scores.items())],
        }

    try:
        if text_file is not None:
            body = text_file.read_text()
            emit(tag_one(body, citation, chunk_id="ad-hoc", tradition_id=tradition))
            return

        if not chunk_ids:
            chunk_ids = [line.strip() for line in sys.stdin if line.strip()]
        if not chunk_ids:
            typer.echo("no chunk IDs given (positional args or stdin)", err=True)
            raise typer.Exit(2)

        db = _resolve_db(cfg, snapshot)
        with open_db(db) as conn:
            for cid in chunk_ids:
                body = chunk_body(cid, cfg.guru.corpus_dir)
                if body is None:
                    typer.echo(f"# skipped {cid}: body not on disk", err=True)
                    continue
                cite = chunk_citation(cid, cfg.guru.corpus_dir)
                row = conn.execute(
                    "SELECT tradition_id FROM nodes WHERE id = ?", (cid,)
                ).fetchone()
                trad = row["tradition_id"] if row else None
                emit(tag_one(body, cite, chunk_id=cid, tradition_id=trad))
    finally:
        if out:
            sink.close()


if __name__ == "__main__":
    app()
