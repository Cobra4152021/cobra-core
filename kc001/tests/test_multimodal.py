import torch

from cobra_kc001.multimodal import CobraTinyVisionLM
from cobra_kc001.synthetic import build_color_dataset, make_solid_image, pil_to_tensor


def test_gradient_reaches_projector_not_encoder():
    model = CobraTinyVisionLM(train_mode="A")
    pix, ids, labels = build_color_dataset(n=1)[0]
    out = model(pixel_values=pix, input_ids=ids, labels=labels)
    out["loss"].backward()
    assert any(p.grad is not None and p.grad.abs().sum() > 0 for p in model.projector.parameters())
    # Encoder frozen
    enc_grads = [p.grad for p in model.encoder.parameters() if p.requires_grad]
    assert enc_grads == []


def test_image_changes_logits():
    torch.manual_seed(0)
    model = CobraTinyVisionLM(train_mode="B")
    q = torch.tensor([[10, 11, 12]])
    a = pil_to_tensor(make_solid_image("red", size=112)).unsqueeze(0)
    b = pil_to_tensor(make_solid_image("blue", size=112)).unsqueeze(0)
    with torch.no_grad():
        la = model(pixel_values=a, input_ids=q)["logits"]
        lb = model(pixel_values=b, input_ids=q)["logits"]
        ln = model(pixel_values=None, input_ids=q)["logits"]
    assert not torch.allclose(la, lb)
    assert la.shape[1] != ln.shape[1]  # prepend adds image tokens


def test_trainable_maps():
    model = CobraTinyVisionLM()
    for mode in ("A", "B", "C", "D"):
        model.apply_train_mode(mode)
        m = model.trainable_map()
        assert m.total > 0
        if mode == "A":
            assert m.by_group["projector"]["trainable"] > 0
            assert m.by_group["attention"]["trainable"] == 0
