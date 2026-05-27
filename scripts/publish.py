"""Publish a trained model to its HuggingFace repo.

The publish *target* (which HF repo, which artifacts, which model card) lives in
the model's training config under a `publish:` block — so shipping a new model
is a new config, not a new script. Only the release tag changes per version, so
it's a CLI flag.

    publish:
      hf_repo: 4rc4n4/qwen2.5-7b-rellm
      model_card: MODEL_CARD.md
      artifacts: ["adapter/**", "merged/**", "gguf/**", "README.md"]

What it does: copies the model card to <output-dir>/README.md (so the HF repo's
front page is the card), uploads the artifacts, and creates the release tag on
the resulting commit.

Usage:
    uv run python scripts/publish.py \
        --config configs/qwen25-7b-distill-v3.yml \
        --output-dir out/qwen25-7b-r32-v3 \
        --tag v3 [--message MSG] [--dry-run]

Scope: this touches only the model's HF repo. The git side (commit + git tag +
push of the rellm repo) is a separate, repo-level step — run it yourself; this
tool prints the matching git commands as a reminder.
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

import yaml

DEFAULT_ARTIFACTS = ["adapter/**", "merged/**", "gguf/**", "README.md"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True, help="model config yml with a publish: block")
    ap.add_argument("--output-dir", required=True, help="trained model dir (adapter/ merged/ gguf/)")
    ap.add_argument("--tag", required=True, help="release tag, e.g. v3 or qwen-3-4b-guru-v1")
    ap.add_argument("--message", default=None, help="HF commit message (default: derived from tag)")
    ap.add_argument("--allow-existing-tag", action="store_true",
                    help="move the tag if it already exists (default: refuse, to protect releases)")
    ap.add_argument("--dry-run", action="store_true", help="print the plan and exit; no upload")
    args = ap.parse_args()

    cfg = yaml.safe_load(Path(args.config).read_text())
    pub = cfg.get("publish")
    if not pub or not pub.get("hf_repo"):
        sys.exit(f"{args.config} has no publish.hf_repo — add a publish: block (see scripts/publish.py)")

    repo = pub["hf_repo"]
    artifacts = pub.get("artifacts", DEFAULT_ARTIFACTS)
    card = Path(pub.get("model_card", "MODEL_CARD.md"))
    out = Path(args.output_dir)
    message = args.message or f"{args.tag}: publish via scripts/publish.py"

    if not out.is_dir():
        sys.exit(f"output dir not found: {out}")
    if not card.is_file():
        sys.exit(f"model card not found: {card}")

    print(f"  repo      : {repo}")
    print(f"  tag       : {args.tag}")
    print(f"  output dir: {out}")
    print(f"  model card: {card}  ->  {out / 'README.md'}")
    print(f"  artifacts : {artifacts}")
    present = sorted(p.name for p in out.iterdir() if p.name in {"adapter", "merged", "gguf"})
    print(f"  found     : {present}")

    if args.dry_run:
        print("\n[dry-run] no files copied, nothing uploaded.")
        return

    shutil.copyfile(card, out / "README.md")
    print(f"→ copied {card} to {out / 'README.md'}")

    from huggingface_hub import HfApi
    api = HfApi()
    api.create_repo(repo_id=repo, repo_type="model", exist_ok=True)  # no-op if it exists
    print(f"→ uploading to {repo} …")
    info = api.upload_folder(
        repo_id=repo,
        folder_path=str(out),
        allow_patterns=artifacts,
        commit_message=message,
    )
    oid = getattr(info, "oid", None) or "main"
    print(f"→ upload commit: {oid}")
    api.create_tag(repo_id=repo, tag=args.tag, revision=oid, exist_ok=args.allow_existing_tag)
    print(f"→ created HF tag {args.tag} at {oid}")
    print("\nPUBLISH COMPLETE")
    print("\nGit side (run yourself, repo-level):")
    print(f"  git add -A && git commit -m {message!r}")
    print(f"  git tag {args.tag} && git push origin HEAD --tags")


if __name__ == "__main__":
    main()
