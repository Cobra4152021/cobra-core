"""Protocol V1 governance conformance: hashes, schemas, fixtures, OpenAPI, types."""

from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from cobra_core.protocol_governance.hashing import (
    hash_files,
    list_fixture_files,
    list_schema_files,
)
from cobra_core.protocol_governance.schema_validate import (
    SchemaValidationError,
    validate_file_against_schema,
)

PROTOCOL_VERSION = "1"
COMPATIBILITY_VERSION = "1"
SCHEMA_VERSION = "1.0.0"

REQUIRED_MANIFEST_KEYS = (
    "protocolVersion",
    "compatibilityVersion",
    "schemaVersion",
    "schemaHash",
    "fixtureHash",
    "generatedAt",
    "sourceCommit",
)

FIXTURE_SCHEMA_MAP: dict[str, str] = {
    "health.success.json": "health.response.schema.json",
    "completion.success.json": "completion.response.schema.json",
    "authentication.failure.json": "error.schema.json",
    "context.limit.json": "limit.case.schema.json",
    "output.limit.json": "limit.case.schema.json",
    "timeout.json": "error.schema.json",
    "usage.json": "usage.schema.json",
    "latency.json": "latency.schema.json",
    "streaming.json": "streaming.events.schema.json",
}

REQUIRED_TS_EXPORTS = (
    "COBRA_PROTOCOL_VERSION",
    "COBRA_COMPATIBILITY_VERSION",
    "HealthResponse",
    "CompletionRequest",
    "CompletionResponse",
    "NormalizedError",
    "Latency",
    "Usage",
    "Capabilities",
    "StreamEvent",
    "ProtocolManifest",
)


def repo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[3]


def default_protocol_root(repo_root: Path | None = None) -> Path:
    root = repo_root or repo_root_from_here()
    return root / "protocol" / "v1"


def _git_sha(repo_root: Path) -> str:
    try:
        out = subprocess.check_output(
            ["git", "-c", f"safe.directory={repo_root}", "rev-parse", "HEAD"],
            cwd=repo_root,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        return out.strip()
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return "unknown"


def compute_hashes(protocol_root: Path) -> tuple[str, str]:
    schema_hash = hash_files(protocol_root, list_schema_files(protocol_root))
    fixture_hash = hash_files(protocol_root, list_fixture_files(protocol_root))
    return schema_hash, fixture_hash


def build_manifest(protocol_root: Path, *, repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or repo_root_from_here()
    schema_hash, fixture_hash = compute_hashes(protocol_root)
    return {
        "protocolVersion": PROTOCOL_VERSION,
        "compatibilityVersion": COMPATIBILITY_VERSION,
        "schemaVersion": SCHEMA_VERSION,
        "schemaHash": schema_hash,
        "fixtureHash": fixture_hash,
        "generatedAt": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "sourceCommit": _git_sha(root),
    }


def write_manifest(protocol_root: Path, *, repo_root: Path | None = None) -> Path:
    manifest = build_manifest(protocol_root, repo_root=repo_root)
    path = protocol_root / "MANIFEST.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return path


def _fail(errors: list[str], msg: str) -> None:
    errors.append(msg)


def verify_protocol_package(protocol_root: Path, *, repo_root: Path | None = None) -> list[str]:
    errors: list[str] = []
    root = repo_root or repo_root_from_here()

    if not protocol_root.is_dir():
        return [f"protocol root missing: {protocol_root}"]

    manifest_path = protocol_root / "MANIFEST.json"
    if not manifest_path.is_file():
        return [f"MANIFEST missing: {manifest_path}"]

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"MANIFEST invalid JSON: {exc}"]

    if not isinstance(manifest, dict):
        return ["MANIFEST root must be an object"]

    for key in REQUIRED_MANIFEST_KEYS:
        if key not in manifest or manifest[key] in ("", None):
            _fail(errors, f"MANIFEST missing/empty field: {key}")

    if manifest.get("protocolVersion") != PROTOCOL_VERSION:
        _fail(errors, f"protocolVersion expected {PROTOCOL_VERSION!r}")
    if manifest.get("compatibilityVersion") != COMPATIBILITY_VERSION:
        _fail(errors, f"compatibilityVersion expected {COMPATIBILITY_VERSION!r}")
    if manifest.get("schemaVersion") != SCHEMA_VERSION:
        _fail(errors, f"schemaVersion expected {SCHEMA_VERSION!r}")

    schema_files = list_schema_files(protocol_root)
    fixture_files = list_fixture_files(protocol_root)
    if not schema_files:
        _fail(errors, "no schema files found")
    if not fixture_files:
        _fail(errors, "no fixture files found")

    expected_fixtures = set(FIXTURE_SCHEMA_MAP)
    actual_fixtures = {p.name for p in fixture_files}
    for name in sorted(expected_fixtures - actual_fixtures):
        _fail(errors, f"missing fixture: {name}")
    for name in sorted(actual_fixtures - expected_fixtures):
        _fail(errors, f"unexpected fixture: {name}")

    for schema_path in schema_files:
        try:
            doc = json.loads(schema_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            _fail(errors, f"schema JSON invalid ({schema_path.name}): {exc}")
            continue
        if not isinstance(doc, dict) or "$schema" not in doc:
            _fail(errors, f"schema missing $schema: {schema_path.name}")

    for fixture_name, schema_name in FIXTURE_SCHEMA_MAP.items():
        fixture_path = protocol_root / "fixtures" / fixture_name
        schema_path = protocol_root / "schemas" / schema_name
        if not fixture_path.is_file() or not schema_path.is_file():
            continue
        try:
            validate_file_against_schema(fixture_path, schema_path)
        except (SchemaValidationError, json.JSONDecodeError, OSError) as exc:
            _fail(errors, f"fixture schema check failed ({fixture_name}): {exc}")

    schema_hash, fixture_hash = compute_hashes(protocol_root)
    if manifest.get("schemaHash") != schema_hash:
        _fail(
            errors,
            f"schemaHash mismatch: manifest={manifest.get('schemaHash')} computed={schema_hash}",
        )
    if manifest.get("fixtureHash") != fixture_hash:
        _fail(
            errors,
            f"fixtureHash mismatch: manifest={manifest.get('fixtureHash')} computed={fixture_hash}",
        )

    openapi_path = protocol_root / "openapi.yaml"
    if not openapi_path.is_file():
        _fail(errors, "openapi.yaml missing")
    else:
        try:
            openapi = yaml.safe_load(openapi_path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            _fail(errors, f"openapi.yaml invalid: {exc}")
            openapi = None
        if not isinstance(openapi, dict):
            _fail(errors, "openapi.yaml root must be a mapping")
        else:
            if openapi.get("openapi") not in {"3.1.0", "3.0.3", "3.0.0"}:
                _fail(errors, "openapi.yaml missing/unsupported openapi version")
            paths = openapi.get("paths") or {}
            if "/health" not in paths or "/v1/chat/completions" not in paths:
                _fail(errors, "openapi.yaml must define /health and /v1/chat/completions")

    types_path = protocol_root / "types" / "cobra-protocol-v1.ts"
    if not types_path.is_file():
        _fail(errors, "TypeScript types missing: types/cobra-protocol-v1.ts")
    else:
        text = types_path.read_text(encoding="utf-8")
        for symbol in REQUIRED_TS_EXPORTS:
            if symbol not in text:
                _fail(errors, f"TypeScript types missing export/symbol: {symbol}")

    # Drift protection: docs package existence (governance docs live outside protocol/v1).
    docs_dir = root / "docs" / "cobra-protocol"
    required_docs = (
        "README.md",
        "COBRA_PROTOCOL_V1.md",
        "COMPATIBILITY_POLICY.md",
        "VERSIONING.md",
        "ERROR_CODES.md",
        "SECURITY.md",
        "CONFORMANCE_TESTING.md",
    )
    for name in required_docs:
        if not (docs_dir / name).is_file():
            _fail(errors, f"governance doc missing: docs/cobra-protocol/{name}")

    return errors
