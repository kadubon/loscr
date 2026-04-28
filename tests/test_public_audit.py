from __future__ import annotations

from typer.testing import CliRunner

from loscr.cli import app
from loscr.security import scan_public_tree


def test_public_audit_detects_local_user_paths(tmp_path) -> None:  # type: ignore[no-untyped-def]
    local_path = "path: C:" + "\\Users\\alice\\secret.txt\n"
    (tmp_path / "README.md").write_text(local_path, encoding="utf-8")
    findings = scan_public_tree(tmp_path)
    assert [(item.rule, item.path, item.line) for item in findings] == [
        ("windows_user_path", "README.md", 1)
    ]


def test_public_audit_cli_passes_clean_tree(tmp_path) -> None:  # type: ignore[no-untyped-def]
    (tmp_path / "README.md").write_text("clean\n", encoding="utf-8")
    result = CliRunner().invoke(app, ["audit-public", str(tmp_path)])
    assert result.exit_code == 0
