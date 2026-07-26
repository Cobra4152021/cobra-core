"""KC-033 Plugin & Extension Framework tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cobra_core.plugins.audit import PLUGIN_AUDIT
from cobra_core.plugins.config import PluginConfig, load_plugin_config
from cobra_core.plugins.errors import PluginError, PluginErrorCode
from cobra_core.plugins.http_api import (
    handle_plugin_disable,
    handle_plugin_enable,
    handle_plugin_get,
    handle_plugins_list,
    handle_plugins_status,
)
from cobra_core.plugins.loader import PluginLoader
from cobra_core.plugins.manager import PLUGIN_MANAGER, PluginManager
from cobra_core.plugins.manifest import normalize_manifest
from cobra_core.plugins.metrics import PLUGIN_METRICS
from cobra_core.plugins.permissions import parse_permissions, require_type_permission
from cobra_core.plugins.registry import PluginRegistry
from cobra_core.plugins.schemas import PluginState, PluginType
from cobra_core.plugins.validator import validate_manifest


@pytest.fixture(autouse=True)
def _reset_pef():
    PLUGIN_MANAGER.reset_for_tests()
    yield
    PLUGIN_MANAGER.reset_for_tests()


def _sample_manifest(**overrides):
    base = {
        "plugin_id": "sample.test_plugin",
        "name": "Test",
        "version": "1.0.0",
        "author": "test",
        "description": "unit test",
        "license": "UNLICENSED",
        "supported_core_version": "0.9.x",
        "plugin_type": "isf_skill",
        "entry_point": "cobra_core.plugins.samples.sample_vehicle_skill.extension",
        "required_permissions": ["register_skill"],
        "dependencies": [],
        "checksum": "",
        "signature": "",
    }
    base.update(overrides)
    return normalize_manifest(base)


def test_registry_put_get_remove():
    reg = PluginRegistry()
    from cobra_core.plugins.schemas import PluginRecord

    rec = PluginRecord(
        plugin_id="sample.a",
        state=PluginState.DISCOVERED,
        manifest=_sample_manifest(plugin_id="sample.a"),
    )
    reg.put(rec)
    assert reg.get("sample.a").plugin_id == "sample.a"
    assert "sample.a" in reg.ids()
    reg.remove("sample.a")
    with pytest.raises(PluginError) as exc:
        reg.get("sample.a")
    assert exc.value.code == PluginErrorCode.NOT_FOUND


def test_manifest_missing_fields():
    with pytest.raises(PluginError) as exc:
        normalize_manifest({"plugin_id": "x"})
    assert exc.value.code == PluginErrorCode.MANIFEST_INVALID


def test_manifest_unsupported_type():
    with pytest.raises(PluginError) as exc:
        normalize_manifest(
            {
                **{
                    k: v
                    for k, v in _sample_manifest().items()
                    if k
                    not in {
                        "checksum",
                        "signature",
                        "min_core_version",
                        "max_core_version",
                        "required_apis",
                        "schema_version",
                        "dependencies",
                    }
                },
                "plugin_type": "marketplace_bundle",
                "required_permissions": ["register_skill"],
            }
        )
    assert exc.value.code == PluginErrorCode.TYPE_UNSUPPORTED


def test_permissions_type_mapping():
    granted = parse_permissions(["register_skill"])
    require_type_permission(PluginType.ISF_SKILL, granted)
    with pytest.raises(PluginError) as exc:
        require_type_permission(PluginType.REPORT, granted)
    assert exc.value.code == PluginErrorCode.PERMISSION_DENIED


def test_validation_reserved_namespace():
    cfg = PluginConfig()
    with pytest.raises(PluginError) as exc:
        validate_manifest(
            _sample_manifest(plugin_id="cobra.evil"),
            config=cfg,
        )
    assert exc.value.code == PluginErrorCode.RESERVED_NAMESPACE


def test_validation_duplicate_id():
    cfg = PluginConfig()
    with pytest.raises(PluginError) as exc:
        validate_manifest(
            _sample_manifest(plugin_id="sample.vehicle_skill"),
            config=cfg,
            known_ids={"sample.vehicle_skill"},
        )
    assert exc.value.code == PluginErrorCode.DUPLICATE_ID


def test_compatibility_core_version():
    cfg = PluginConfig(core_version="0.9.0rc1")
    validate_manifest(_sample_manifest(supported_core_version="0.9.x"), config=cfg)
    with pytest.raises(PluginError) as exc:
        validate_manifest(
            _sample_manifest(supported_core_version="1.0.x"),
            config=cfg,
        )
    assert exc.value.code == PluginErrorCode.COMPATIBILITY_FAILED


def test_compatibility_min_max():
    cfg = PluginConfig(core_version="0.9.0rc1")
    with pytest.raises(PluginError) as exc:
        validate_manifest(
            _sample_manifest(min_core_version="1.0.0"),
            config=cfg,
        )
    assert exc.value.code == PluginErrorCode.COMPATIBILITY_FAILED


def test_entry_point_must_be_allowed():
    cfg = PluginConfig()
    with pytest.raises(PluginError) as exc:
        validate_manifest(
            _sample_manifest(entry_point="os.path"),
            config=cfg,
        )
    assert exc.value.code == PluginErrorCode.VALIDATION_FAILED


def test_validation_does_not_import_or_execute_plugin(monkeypatch):
    loader = PluginLoader(config=PluginConfig(), registry=PluginRegistry())
    loader.discover()

    def _unexpected_import(_entry_point: str):
        raise AssertionError("plugin code executed before validation completed")

    monkeypatch.setattr("cobra_core.plugins.loader.importlib.import_module", _unexpected_import)
    rec = loader.validate("sample.vehicle_skill")
    assert rec.state == PluginState.VALIDATED


def test_discover_load_enable_disable_unload_samples():
    ids = PLUGIN_MANAGER.bootstrap_samples()
    assert "sample.vehicle_skill" in ids
    assert "sample.policy_report" in ids
    assert "sample.budget_dataset" in ids
    assert "sample.case_template" in ids
    listed = PLUGIN_MANAGER.list_plugins()
    assert len(listed) >= 4
    assert all(p["state"] == PluginState.ENABLED.value for p in listed)
    PLUGIN_MANAGER.disable("sample.vehicle_skill")
    assert PLUGIN_MANAGER.get("sample.vehicle_skill")["state"] == PluginState.DISABLED.value
    PLUGIN_MANAGER.enable("sample.vehicle_skill")
    assert PLUGIN_MANAGER.get("sample.vehicle_skill")["state"] == PluginState.ENABLED.value
    PLUGIN_MANAGER.unload("sample.vehicle_skill")
    with pytest.raises(PluginError):
        PLUGIN_MANAGER.get("sample.vehicle_skill")


def test_reload_hot_load():
    PLUGIN_MANAGER.bootstrap_samples()
    rec = PLUGIN_MANAGER.reload("sample.policy_report")
    assert rec.state == PluginState.ENABLED
    PLUGIN_MANAGER.config = PluginConfig(hot_load=False, enabled=True)
    PLUGIN_MANAGER.loader = PluginLoader(
        config=PLUGIN_MANAGER.config, registry=PLUGIN_MANAGER.registry
    )
    with pytest.raises(PluginError) as exc:
        PLUGIN_MANAGER.reload("sample.policy_report")
    assert exc.value.code == PluginErrorCode.STATE_INVALID


def test_audit_and_metrics():
    PLUGIN_MANAGER.bootstrap_samples()
    snap = PLUGIN_METRICS.snapshot()
    assert snap["plugins_loaded"] >= 4
    assert snap["plugins_enabled"] >= 4
    assert "plugin_load_latency" in snap
    events = {e["event"] for e in PLUGIN_AUDIT.recent(limit=100)}
    assert "plugin_loaded" in events
    assert "plugin_enabled" in events
    PLUGIN_MANAGER.disable("sample.budget_dataset")
    events2 = {e["event"] for e in PLUGIN_AUDIT.recent(limit=100)}
    assert "plugin_disabled" in events2


def test_permission_denial_audited(tmp_path: Path):
    bad = tmp_path / "bad_perm"
    bad.mkdir()
    (bad / "plugin.json").write_text(
        json.dumps(
            {
                "plugin_id": "sample.bad_perm",
                "name": "Bad",
                "version": "1.0.0",
                "author": "t",
                "description": "d",
                "license": "UNLICENSED",
                "supported_core_version": "0.9.x",
                "plugin_type": "report",
                "entry_point": "cobra_core.plugins.samples.sample_policy_report.extension",
                "required_permissions": ["register_skill"],
                "dependencies": [],
            }
        ),
        encoding="utf-8",
    )
    mgr = PluginManager(
        config=PluginConfig(plugins_root=str(tmp_path)),
        registry=PluginRegistry(),
    )
    mgr.discover()
    with pytest.raises(PluginError) as exc:
        mgr.load("sample.bad_perm")
    assert exc.value.code == PluginErrorCode.PERMISSION_DENIED
    assert any(e["event"] == "permission_denial" for e in PLUGIN_AUDIT.recent(limit=50))


def test_http_handlers():
    body = handle_plugins_list()
    assert body["ok"] is True
    assert len(body["plugins"]) >= 4
    st = handle_plugins_status()
    assert st["ok"] is True
    assert st["registry"]["total"] >= 4
    code, got = handle_plugin_get("sample.vehicle_skill")
    assert code == 200
    assert got["plugin"]["plugin_id"] == "sample.vehicle_skill"
    code, _ = handle_plugin_disable("sample.vehicle_skill")
    assert code == 200
    code, enabled = handle_plugin_enable("sample.vehicle_skill")
    assert code == 200
    assert enabled["plugin"]["state"] == "enabled"
    code, missing = handle_plugin_get("does.not.exist")
    assert code == 404
    assert missing["ok"] is False


def test_extensions_do_not_mutate_skill_registry():
    from cobra_core.isf.registry import SKILL_REGISTRY

    before = {s.id for s in SKILL_REGISTRY.list_skills()}
    PLUGIN_MANAGER.bootstrap_samples()
    after = {s.id for s in SKILL_REGISTRY.list_skills()}
    assert before == after
    exts = PLUGIN_MANAGER.registry.extensions_by_type(PluginType.ISF_SKILL)
    assert any(e.plugin_id == "sample.vehicle_skill" for e in exts)


def test_config_env(monkeypatch):
    monkeypatch.setenv("PEF_ENABLED", "false")
    monkeypatch.setenv("PEF_HOT_LOAD", "false")
    cfg = load_plugin_config()
    assert cfg.enabled is False
    assert cfg.hot_load is False


def test_regression_kc_021_through_032():
    """Smoke: prior King Cobra surfaces remain importable beside PEF."""
    from cobra_core.air import bridge as air_bridge
    from cobra_core.benchmark.runner import BenchmarkRunner
    from cobra_core.cial.config import load_cial_config
    from cobra_core.isf.registry import SKILL_REGISTRY
    from cobra_core.kef.config import load_kef_config
    from cobra_core.operations.health import collect_health, overall_status
    from cobra_core.operations.schemas import ComponentHealth
    from cobra_core.resilience.config import rrf_enabled

    assert load_cial_config() is not None
    assert air_bridge is not None
    assert len(SKILL_REGISTRY.list_skills()) >= 1
    assert load_kef_config() is not None
    assert isinstance(rrf_enabled(), bool)
    result = BenchmarkRunner().run_dataset("policy_review_v1")
    assert result.overall_score >= 0.0
    assert overall_status() in set(ComponentHealth)
    assert len(collect_health()) >= 1
    PLUGIN_MANAGER.bootstrap_samples()
    assert len(PLUGIN_MANAGER.list_plugins()) >= 4
