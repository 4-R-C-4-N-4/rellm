"""Load rellm.toml as typed config."""
from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GuruPaths:
    repo: Path
    db: Path
    corpus_dir: Path
    taxonomy: Path


@dataclass(frozen=True)
class RellmPaths:
    root: Path
    data_dir: Path
    snapshots: Path
    exports: Path


@dataclass(frozen=True)
class ModelCfg:
    base: str
    exclude_model_prefixes: tuple[str, ...]  # student lineage — never distill on
    exclude_models: tuple[str, ...]          # specific weak/experimental teachers


@dataclass(frozen=True)
class PromptCfg:
    version: str


@dataclass(frozen=True)
class Config:
    guru: GuruPaths
    rellm: RellmPaths
    model: ModelCfg
    prompt: PromptCfg


def find_config(start: Path | None = None) -> Path:
    p = (start or Path.cwd()).resolve()
    for d in (p, *p.parents):
        cand = d / "rellm.toml"
        if cand.exists():
            return cand
    raise FileNotFoundError("rellm.toml not found in cwd or any parent")


def load(path: Path | None = None) -> Config:
    cfg_path = path or find_config()
    root = cfg_path.parent
    with cfg_path.open("rb") as f:
        raw = tomllib.load(f)

    def _abs(p: str) -> Path:
        pp = Path(p)
        return pp if pp.is_absolute() else (root / pp).resolve()

    return Config(
        guru=GuruPaths(
            repo=_abs(raw["guru"]["repo"]),
            db=_abs(raw["guru"]["db"]),
            corpus_dir=_abs(raw["guru"]["corpus_dir"]),
            taxonomy=_abs(raw["guru"]["taxonomy"]),
        ),
        rellm=RellmPaths(
            root=root,
            data_dir=_abs(raw["rellm"]["data_dir"]),
            snapshots=_abs(raw["rellm"]["snapshots"]),
            exports=_abs(raw["rellm"]["exports"]),
        ),
        model=ModelCfg(
            base=raw["model"]["base"],
            exclude_model_prefixes=tuple(raw["model"].get("exclude_model_prefixes") or []),
            exclude_models=tuple(raw["model"].get("exclude_models") or []),
        ),
        prompt=PromptCfg(version=raw["prompt"]["version"]),
    )
