from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_single_windows_launcher_entry_is_built_and_targets_dashboard():
    source = (ROOT / "tools" / "launcher" / "QuantDataGatewayLauncher.cs").read_text(encoding="utf-8")
    executable = ROOT / "QuantDataGateway.exe"

    assert executable.exists()
    assert executable.stat().st_size > 10_000
    assert '"/auto-trading"' in source
    assert '".venv", "Scripts", "python.exe"' in source
    assert "MutexName" in source
    assert "--no-access-log" in source
    assert "--log-level warning" in source
    assert "workspaceFrame" in source
    assert list(ROOT.glob("*.bat")) == []
