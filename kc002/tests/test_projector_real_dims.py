import torch

from cobra_kc001.projector import VisionProjector, ProjectorConfig, expected_projector_params


def test_real_dimension_projector():
    proj = VisionProjector(ProjectorConfig(in_dim=3456, hidden_dim=2880, out_dim=2880))
    y = proj(torch.randn(2, 729, 3456))
    assert y.shape == (2, 729, 2880)
    assert proj.param_count() == expected_projector_params(
        ProjectorConfig(in_dim=3456, hidden_dim=2880, out_dim=2880)
    )
    y.sum().backward()
    assert any(p.grad is not None for p in proj.parameters())


def test_wrong_hidden_dim_raises():
    proj = VisionProjector(ProjectorConfig(in_dim=3456, hidden_dim=2880, out_dim=2880))
    try:
        proj(torch.randn(1, 8, 1152))
        assert False
    except ValueError:
        pass
