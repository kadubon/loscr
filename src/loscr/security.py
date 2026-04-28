"""Lightweight public-release audit helpers."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


DEFAULT_EXCLUDES = {
    ".venv",
    ".git",
    ".loscr",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "__pycache__",
}

TEXT_SUFFIXES = {
    ".cff",
    ".cfg",
    ".ini",
    ".json",
    ".jsonl",
    ".md",
    ".py",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}

PUBLIC_AUDIT_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("private_key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("openai_key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("github_token", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{20,}\b")),
    ("slack_token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b")),
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("windows_user_path", re.compile(r"\b[A-Za-z]:\\Users\\[^\\\s]+", re.IGNORECASE)),
    ("posix_home_path", re.compile(r"(?<![A-Za-z0-9_])/(?:Users|home)/[^/\s]+")),
)


@dataclass(frozen=True)
class PublicAuditFinding:
    path: str
    line: int
    rule: str
    excerpt: str


def scan_public_tree(root: str | Path = ".") -> list[PublicAuditFinding]:
    """Scan repository text files for high-confidence secrets or local paths."""
    base = Path(root)
    findings: list[PublicAuditFinding] = []
    for path in sorted(base.rglob("*")):
        if not path.is_file() or _is_excluded(path, base):
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        for line_number, line in enumerate(lines, start=1):
            for rule, pattern in PUBLIC_AUDIT_PATTERNS:
                if pattern.search(line):
                    findings.append(
                        PublicAuditFinding(
                            path=str(path.relative_to(base).as_posix()),
                            line=line_number,
                            rule=rule,
                            excerpt=_redact(line),
                        )
                    )
    return findings


def _is_excluded(path: Path, base: Path) -> bool:
    try:
        relative = path.relative_to(base)
    except ValueError:
        return True
    return any(part in DEFAULT_EXCLUDES for part in relative.parts)


def _redact(line: str) -> str:
    redacted = line.strip()
    for _, pattern in PUBLIC_AUDIT_PATTERNS:
        redacted = pattern.sub("[REDACTED]", redacted)
    return redacted[:160]
