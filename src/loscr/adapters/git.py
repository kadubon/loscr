"""Local git adapter.

This adapter invokes only the local ``git`` CLI. By default it records commit
and tree hashes rather than raw private file content.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from loscr.hashing import attach_integrity_hash, canonical_hash
from loscr.models import EdgeEventEnvelope, ResourceRaw


def _git(repo: str | Path, args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=Path(repo),
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def commit_to_edge_event(
    repo: str | Path,
    *,
    rev: str = "HEAD",
    claim_scope_id: str = "default",
    station_id: str = "git",
    policy_id: str = "local-git",
    include_raw_diff: bool = False,
) -> EdgeEventEnvelope:
    """Map a local commit to a Layer 0 edge event."""
    commit = _git(repo, ["rev-parse", rev])
    tree = _git(repo, ["show", "-s", "--format=%T", commit])
    parents = _git(repo, ["show", "-s", "--format=%P", commit]).split()
    timestamp = _git(repo, ["show", "-s", "--format=%cI", commit])
    parent_tree = _git(repo, ["show", "-s", "--format=%T", parents[0]]) if parents else "root"
    if include_raw_diff:
        diff_hash = canonical_hash(_git(repo, ["show", "--format=", "--no-ext-diff", commit]))
    else:
        diff_hash = canonical_hash({"commit": commit, "tree": tree, "parent_tree": parent_tree})
    data = {
        "event_id": f"git:{commit}",
        "event_type": "git_commit",
        "timestamp": timestamp,
        "item_id": commit,
        "parent_event_id": f"git:{parents[0]}" if parents else None,
        "station_id": station_id,
        "policy_id": policy_id,
        "action_type": "commit",
        "substrate_fingerprint": canonical_hash({"git_tree": tree}),
        "status_raw": "committed",
        "resource_raw": ResourceRaw().model_dump(mode="json"),
        "queue_channel": "git",
        "queue_age_raw": 0.0,
        "dependency_flag": bool(parents),
        "reuse_count": 0,
        "input_hash": canonical_hash({"parent_tree": parent_tree}),
        "output_hash": diff_hash,
        "claim_scope_id": claim_scope_id,
    }
    return EdgeEventEnvelope.model_validate(attach_integrity_hash(data))
