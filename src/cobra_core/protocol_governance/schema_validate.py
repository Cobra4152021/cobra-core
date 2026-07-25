"""Minimal JSON Schema subset validator for Protocol V1 governance fixtures."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class SchemaValidationError(ValueError):
    pass


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_ref(ref: str, base_dir: Path, cache: dict[str, Any]) -> tuple[Any, Path]:
    if ref.startswith("#"):
        raise SchemaValidationError(f"Unsupported local fragment ref: {ref}")
    target = (base_dir / ref).resolve()
    key = str(target)
    if key not in cache:
        cache[key] = _load_json(target)
    return cache[key], target.parent


def _type_ok(value: Any, expected: str | list[str]) -> bool:
    types = expected if isinstance(expected, list) else [expected]
    for t in types:
        if t == "object" and isinstance(value, dict):
            return True
        if t == "array" and isinstance(value, list):
            return True
        if t == "string" and isinstance(value, str):
            return True
        if t == "boolean" and isinstance(value, bool):
            return True
        if t == "integer" and isinstance(value, int) and not isinstance(value, bool):
            return True
        if t == "number" and isinstance(value, (int, float)) and not isinstance(value, bool):
            return True
        if t == "null" and value is None:
            return True
    return False


def validate_instance(
    instance: Any,
    schema: dict[str, Any],
    *,
    base_dir: Path,
    path: str = "$",
    cache: dict[str, Any] | None = None,
) -> None:
    cache = cache if cache is not None else {}

    if "$ref" in schema:
        ref_schema, ref_dir = _resolve_ref(str(schema["$ref"]), base_dir, cache)
        validate_instance(instance, ref_schema, base_dir=ref_dir, path=path, cache=cache)
        return

    if "const" in schema and instance != schema["const"]:
        raise SchemaValidationError(f"{path}: expected const {schema['const']!r}, got {instance!r}")

    if "enum" in schema and instance not in schema["enum"]:
        raise SchemaValidationError(f"{path}: value not in enum")

    if "type" in schema and not _type_ok(instance, schema["type"]):
        raise SchemaValidationError(f"{path}: type mismatch (expected {schema['type']})")

    if (
        isinstance(instance, str)
        and "minLength" in schema
        and len(instance) < int(schema["minLength"])
    ):
        raise SchemaValidationError(f"{path}: shorter than minLength")

    if (
        isinstance(instance, (int, float))
        and not isinstance(instance, bool)
        and "minimum" in schema
        and instance < schema["minimum"]
    ):
        raise SchemaValidationError(f"{path}: below minimum")

    if isinstance(instance, list):
        if "minItems" in schema and len(instance) < int(schema["minItems"]):
            raise SchemaValidationError(f"{path}: fewer than minItems")
        if "items" in schema:
            item_schema = schema["items"]
            if not isinstance(item_schema, dict):
                raise SchemaValidationError(f"{path}: items must be an object schema")
            for i, item in enumerate(instance):
                validate_instance(
                    item,
                    item_schema,
                    base_dir=base_dir,
                    path=f"{path}[{i}]",
                    cache=cache,
                )

    if isinstance(instance, dict):
        required = schema.get("required") or []
        for key in required:
            if key not in instance:
                raise SchemaValidationError(f"{path}: missing required property {key!r}")

        properties = schema.get("properties") or {}
        for key, value in instance.items():
            if key in properties:
                prop_schema = properties[key]
                if not isinstance(prop_schema, dict):
                    raise SchemaValidationError(f"{path}.{key}: invalid property schema")
                validate_instance(
                    value,
                    prop_schema,
                    base_dir=base_dir,
                    path=f"{path}.{key}",
                    cache=cache,
                )
            else:
                additional = schema.get("additionalProperties", True)
                if additional is False:
                    raise SchemaValidationError(f"{path}: unexpected property {key!r}")
                if isinstance(additional, dict):
                    validate_instance(
                        value,
                        additional,
                        base_dir=base_dir,
                        path=f"{path}.{key}",
                        cache=cache,
                    )


def validate_file_against_schema(instance_path: Path, schema_path: Path) -> None:
    instance = _load_json(instance_path)
    schema = _load_json(schema_path)
    if not isinstance(schema, dict):
        raise SchemaValidationError(f"{schema_path}: schema root must be object")
    validate_instance(instance, schema, base_dir=schema_path.parent)
