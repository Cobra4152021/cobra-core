import torch
import torch.nn as nn

from cobra_kc001.integration import (
    EmbeddingInjector,
    assert_labels_mask_image_positions,
    build_prepend_sequence,
    replace_image_pad_embeddings,
)


def test_prepend_masks_image_labels():
    vis = torch.randn(1, 4, 8)
    txt = torch.randn(1, 3, 8)
    labels = torch.tensor([[1, 2, 3]])
    seq = build_prepend_sequence(vis, txt, labels=labels)
    assert seq.inputs_embeds.shape == (1, 7, 8)
    assert seq.labels is not None
    assert (seq.labels[0, :4] == -100).all()
    assert torch.equal(seq.labels[0, 4:], labels[0])


def test_replace_pad_count_mismatch_asserts():
    emb = nn.Embedding(20, 8)
    ids = torch.tensor([[1, 9, 9, 2]])  # two pads
    embeds = emb(ids)
    vis = torch.randn(1, 3, 8)  # three tokens — mismatch
    try:
        replace_image_pad_embeddings(ids, embeds, vis, image_pad_id=9)
        assert False, "expected AssertionError"
    except AssertionError:
        pass


def test_text_only_does_not_inject():
    emb = nn.Embedding(20, 8)
    inj = EmbeddingInjector(emb, image_pad_id=9)
    ids = torch.tensor([[1, 2, 3]])
    vis = torch.randn(1, 2, 8)
    # replace mode with no pads leaves text embeds
    seq = inj.build(ids, vis, mode="replace_pad")
    assert torch.allclose(seq.inputs_embeds, emb(ids))


def test_device_mismatch_raises():
    if not torch.cuda.is_available():
        return
    vis = torch.randn(1, 2, 4, device="cuda")
    txt = torch.randn(1, 2, 4, device="cpu")
    try:
        build_prepend_sequence(vis, txt)
        assert False
    except RuntimeError:
        pass


def test_labels_on_image_positions_fail():
    labels = torch.tensor([[5, 6, 7]])
    mask = torch.tensor([[True, False, False]])
    try:
        assert_labels_mask_image_positions(labels, mask)
        assert False
    except AssertionError:
        pass
