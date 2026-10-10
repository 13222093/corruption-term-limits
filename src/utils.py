"""Configuration loading and results I/O (R6: results as data with config hash and commit)."""
from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import time

import numpy as np
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
FIGURES = os.path.join(ROOT, "figures")
CONFIGS = os.path.join(ROOT, "configs")


def deep_update(base: dict, upd: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in (upd or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_update(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def load_config(profile: str = "quick") -> dict:
    """Merge configs/base.yaml with configs/<profile>.yaml."""
    with open(os.path.join(CONFIGS, "base.yaml")) as fh:
        base = yaml.safe_load(fh)
    with open(os.path.join(CONFIGS, f"{profile}.yaml")) as fh:
        prof = yaml.safe_load(fh) or {}
    cfg = deep_update(base, prof)
    cfg["profile"] = profile
    cfg.setdefault("ibm_variant", "si")
    for key in ("ibm_small", "ibm_large"):
        if key in cfg:
            cfg[key].setdefault("ibm_variant", cfg["ibm_variant"])
    _check_numeric(cfg)
    return cfg


def _check_numeric(cfg, path=""):
    """Guard against YAML 1.1 parsing '1.0e10' (no exponent sign) as a string."""
    for k, v in cfg.items():
        if isinstance(v, dict):
            _check_numeric(v, f"{path}{k}.")
        elif isinstance(v, str) and k not in ("profile", "method", "ibm_variant"):
            try:
                float(v)
            except ValueError:
                continue
            raise ValueError(f"config value {path}{k} = {v!r} parsed as string; "
                             "write exponents with a sign, e.g. 1.0e+10")


def config_hash(cfg) -> str:
    s = json.dumps(cfg, sort_keys=True, default=_default)
    return hashlib.sha256(s.encode()).hexdigest()[:12]


def git_commit() -> str:
    try:
        rev = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                                      stderr=subprocess.DEVNULL).decode().strip()
        dirty = subprocess.call(["git", "diff", "--quiet", "--", "src", "experiments"],
                                cwd=ROOT, stderr=subprocess.DEVNULL) != 0
        return rev + ("-dirty" if dirty else "")
    except Exception:
        return "unknown"


def _default(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, complex):
        return [o.real, o.imag]
    raise TypeError(f"not serializable: {type(o)}")


def save_result(name: str, data: dict, cfg: dict, profile: str | None = None) -> str:
    """Write results/<profile>/<name>.json with metadata (config hash, git commit, time)."""
    profile = profile or cfg.get("profile", "quick")
    d = os.path.join(RESULTS, profile)
    os.makedirs(d, exist_ok=True)
    payload = {
        "meta": {"name": name, "config_hash": config_hash(cfg), "git_commit": git_commit(),
                 "profile": profile, "created": time.strftime("%Y-%m-%dT%H:%M:%S"),
                 "config": cfg},
        "data": data,
    }
    path = os.path.join(d, f"{name}.json")
    with open(path, "w") as fh:
        json.dump(payload, fh, indent=1, default=_default)
    return path


def load_result(name: str, profile: str = "full") -> dict:
    with open(os.path.join(RESULTS, profile, f"{name}.json")) as fh:
        return json.load(fh)["data"]


def save_csv(name: str, df, cfg: dict, profile: str | None = None) -> str:
    profile = profile or cfg.get("profile", "quick")
    d = os.path.join(RESULTS, profile)
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, f"{name}.csv")
    with open(path, "w", newline="") as fh:
        fh.write(f"# config_hash={config_hash(cfg)} git_commit={git_commit()} profile={profile}\n")
        df.to_csv(fh, index=False)
    return path


def fig_path(name: str, profile: str) -> str:
    d = FIGURES if profile == "full" else os.path.join(FIGURES, profile)
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, name)
