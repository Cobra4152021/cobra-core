import torch

from cobra_kc001.projector import VisionProjector, expected_projector_params, assert_finite


def test_projector_shapes_and_params():
    proj = VisionProjector()
    x = torch.randn(2, 729, 3456)
    y = proj(x)
    assert y.shape == (2, 729, 2880)
    assert proj.param_count() == expected_projector_params()
    assert_finite(y)


def test_projector_deterministic_and_grad():
    torch.manual_seed(0)
    proj = VisionProjector()
    x = torch.randn(1, 8, 3456, requires_grad=True)
    y1 = proj(x)
    y2 = proj(x)
    assert torch.allclose(y1, y2)
    y1.sum().backward()
    assert x.grad is not None
    assert any(p.grad is not None for p in proj.parameters())


def test_batch_and_variable_tokens():
    proj = VisionProjector()
    for t in (1, 16, 729):
        y = proj(torch.randn(3, t, 3456))
        assert y.shape == (3, t, 2880)
