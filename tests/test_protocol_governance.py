"""Conformance tests for Protocol V1 governance package (no server/GPU)."""

from __future__ import annotations

from pathlib import Path

from cobra_core.protocol_governance.verify import (
    FIXTURE_SCHEMA_MAP,
    default_protocol_root,
    repo_root_from_here,
    verify_protocol_package,
)


def test_protocol_governance_conformance_pass() -> None:
    errors = verify_protocol_package(default_protocol_root())
    assert errors == [], errors


def test_required_fixtures_present() -> None:
    fixtures = default_protocol_root() / "fixtures"
    for name in FIXTURE_SCHEMA_MAP:
        assert (fixtures / name).is_file(), name


def test_governance_docs_present() -> None:
    docs = repo_root_from_here() / "docs" / "cobra-protocol"
    for name in (
        "README.md",
        "COBRA_PROTOCOL_V1.md",
        "COMPATIBILITY_POLICY.md",
        "VERSIONING.md",
        "ERROR_CODES.md",
        "SECURITY.md",
        "CONFORMANCE_TESTING.md",
    ):
        assert (docs / name).is_file()


def test_no_server_package_mutation_marker() -> None:
    """Governance package must remain separate from protocol_v1 server module."""
    gov = Path(__file__).resolve().parents[1] / "src" / "cobra_core" / "protocol_governance"
    server = Path(__file__).resolve().parents[1] / "src" / "cobra_core" / "protocol_v1"
    assert gov.is_dir()
    assert server.is_dir()
    assert gov.resolve() != server.resolve()
