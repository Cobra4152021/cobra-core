import os

import pytest

from cobra_kc002.env_gate import EnvironmentGateError, collect_env, require_real_weight_env


def test_collect_env_reports_cpu_failure_locally():
    os.environ["COBRA_REQUIRE_CUDA"] = "1"
    os.environ["COBRA_ALLOW_SURROGATE"] = "0"
    os.environ["COBRA_MIN_VRAM_GB"] = "20"
    report = collect_env()
    # On the local KC-001 host this should fail closed.
    if not report.cuda_available:
        assert report.ok is False
        assert any("CUDA" in f or "CPU-only" in f or "VRAM" in f for f in report.failures)


def test_require_real_weight_env_raises_without_cuda():
    os.environ["COBRA_REQUIRE_CUDA"] = "1"
    os.environ["COBRA_ALLOW_SURROGATE"] = "0"
    report = collect_env()
    if report.ok:
        pytest.skip("CUDA host available")
    with pytest.raises(EnvironmentGateError):
        require_real_weight_env()


def test_surrogate_forbidden_even_if_flag_set_with_ok_env():
    # If somehow env ok but surrogate allowed, require_real_weight_env still blocks.
    os.environ["COBRA_ALLOW_SURROGATE"] = "1"
    report = collect_env()
    if not report.ok:
        # Still ensure collect marks allow_surrogate
        assert report.allow_surrogate is True
    else:
        with pytest.raises(EnvironmentGateError):
            require_real_weight_env()
