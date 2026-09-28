"""Mandatory parity gate, 177-label expansion, reload and gradient checks."""

import argparse
import csv
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import torch

from .features import single_line, tokens
from .model import ContinualLID, pack_features, write_json

PROBES = [
    "This is a language identification example.", "සිංහල භාෂාව ශ්‍රී ලංකාවේ භාවිතා වේ.",
    "නමෝ තස්ස භගවතෝ අරහතෝ සම්මාසම්බුද්ධස්ස", "संस्कृतभाषा अतीव सुन्दरा अस्ति।",
    "यह हिन्दी भाषा का एक उदाहरण है।", "தமிழ் ஒரு பழமையான மொழி.",
    "বাংলা একটি সুন্দর ভাষা।", "هذه جملة مكتوبة باللغة العربية.",
    "Ceci est une phrase française.", "Das ist ein deutscher Beispielsatz.",
    "日本語の文章です。", "这是一个中文句子。", "Это предложение на русском языке.",
    "한국어 문장입니다.", "ภาษาไทยเป็นภาษาที่สวยงาม", "Hii ni sentensi ya Kiswahili.",
    "", "   ", "hello\tworld\rnext\vword\fmore\0end", "word\u00a0word",
    "é e\u0301 සිංහල 😀", "__label__en hello", "hello </s> ignored tail",
    "zzzzUnseenWord🙂012345", "a a a a", "a\nb",
]


def sample_texts(paths, limit, seed=42):
    rng, samples, counts = random.Random(seed), defaultdict(list), Counter()
    for path in paths:
        with Path(path).open(encoding="utf-8-sig", newline="") as f:
            rows = csv.DictReader(f) if str(path).endswith(".csv") else (json.loads(s) for s in f if s.strip())
            for row in rows:
                text = row.get("text")
                if not isinstance(text, str) or not text.strip():
                    continue
                group = str(row.get("group") or row.get("label") or "unknown")
                counts[group] += 1
                if len(samples[group]) < limit:
                    samples[group].append(text)
                else:
                    j = rng.randrange(counts[group])
                    if j < limit:
                        samples[group][j] = text
    return PROBES + [t for group in sorted(samples) for t in samples[group]]


@torch.no_grad()
def check_import(model, native, texts):
    texts = [single_line(t) for t in texts]
    assert torch.equal(model.embedding.weight, torch.from_numpy(native.get_input_matrix())), "Input rows changed on import"
    assert torch.equal(model.output_weight, torch.from_numpy(native.get_output_matrix())), "Output rows changed on import"
    rng = random.Random(42)
    words = rng.sample(model.encoder.words, min(1000, len(model.encoder.words)))
    words += list(dict.fromkeys(w for t in texts for w in tokens(t) if not w.startswith("__label__")))[:2000]
    for word in words:
        expected = native.get_subwords(word)[1].tolist()
        assert list(model.encoder.word_ids(word)) == expected, f"Feature IDs differ: {word!r}"
    hidden_error, score_error, compared, correct = 0.0, 0.0, 0, 0
    for start in range(0, len(texts), 64):
        batch = texts[start:start + 64]
        ids, offsets = pack_features([model.encoder.encode(t) for t in batch])
        hidden = model.hidden(ids, offsets).numpy()
        reference_hidden = np.stack([native.get_sentence_vector(t) for t in batch])
        hidden_error = max(hidden_error, float(np.abs(hidden - reference_hidden).max()))
        np.testing.assert_allclose(hidden, reference_hidden, rtol=2e-5, atol=2e-6)
        scores = model.leaf_log_scores(ids, offsets).exp().numpy()
        ref_labels, ref_scores = native.predict(batch, k=176, threshold=0.0)
        for i, (labels, values) in enumerate(zip(ref_labels, ref_scores)):
            expected_top = labels[0].removeprefix("__label__")
            actual_top = model.labels[int(scores[i].argmax())]
            assert actual_top == expected_top, f"Top-1 parity failed for sample {start+i}: {actual_top} != {expected_top}"
            correct += 1
            # Native DFS prunes scores below ~1e-5 even at threshold=0.
            # Compare every returned score; do not pretend pruned scores are 0.
            indices = [model.label_to_id[label.removeprefix("__label__")] for label in labels]
            actual = scores[i, indices]
            np.testing.assert_allclose(actual, values, rtol=2e-4, atol=2e-5)
            score_error = max(score_error, float(np.abs(actual - np.asarray(values)).max()))
            compared += len(values)
    return {"passed": True, "examples": len(texts), "top1_matches": correct,
            "tokens_with_exact_feature_ids": len(words), "compared_native_scores": compared,
            "max_hidden_absolute_error": hidden_error, "max_score_absolute_error": score_error,
            "input_weights_identical": True, "output_weights_identical": True,
            "note": "Native epsilon scores compared, including its threshold pruning behavior."}


def gradient_check(model):
    # This is a structural check, not an accuracy experiment. Called on a
    # RELOADED model so exported initialization weights remain untouched.
    seq = [model.encoder.encode("නමෝ තස්ස භගවතෝ අරහතෝ සම්මාසම්බුද්ධස්ස")]
    ids, offsets = pack_features(seq, model.device)
    used = ids.unique()
    before_input = model.embedding.weight[used].detach().clone()
    before_output = model.output_weight.detach().clone()
    target = torch.tensor([model.label_to_id["pi"]], device=model.device)
    optimizer = torch.optim.SGD(model.parameters(), lr=0.01, momentum=0, weight_decay=0, foreach=False)
    model.train()
    optimizer.zero_grad(set_to_none=True)
    loss = model.nll(ids, offsets, target).mean()
    assert torch.isfinite(loss)
    loss.backward()
    assert model.embedding.weight.grad is not None and model.embedding.weight.grad.is_sparse
    assert torch.isfinite(model.embedding.weight.grad.coalesce().values()).all()
    assert torch.isfinite(model.output_weight.grad).all()
    optimizer.step()
    old_rows = model.config["original_output_rows"]
    checks = {
        "inherited_input_rows_changed": bool((model.embedding.weight[used] != before_input).any()),
        "inherited_decision_rows_changed": bool((model.output_weight[:old_rows] != before_output[:old_rows]).any()),
        "new_pali_node_changed": bool((model.output_weight[old_rows:] != before_output[old_rows:]).any()),
        "all_parameters_trainable": all(p.requires_grad for p in model.parameters()),
        "finite_loss": float(loss.detach()),
    }
    assert all(v for k, v in checks.items() if k != "finite_loss"), checks
    return checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-bin", required=True)
    parser.add_argument("--data", action="append", default=[], help="Repeat for train/validation JSONL or CSV")
    parser.add_argument("--per-group", type=int, default=32)
    parser.add_argument("--out", required=True, help="Creates base176/, init177/, parity_report.json")
    parser.add_argument("--threads", type=int, default=2)
    args = parser.parse_args()
    torch.set_num_threads(args.threads)
    out = Path(args.out)
    if (out / "base176").exists() or (out / "init177").exists():
        raise FileExistsError("Choose a fresh --out directory; existing checkpoints are preserved")
    texts = sample_texts(args.data, args.per_group)
    model, native = ContinualLID.from_fasttext(args.base_bin)
    report = check_import(model, native, texts)
    del native
    model.config["parity_verified"] = True
    model.config["parity_report"] = report.copy()
    model.save_pretrained(out / "base176")
    with torch.no_grad():
        ids, offsets = pack_features([model.encoder.encode(t) for t in PROBES])
        old_probs = model.leaf_log_scores(ids, offsets, native_scores=False).exp()
        old_weights = model.output_weight.detach().clone()
        model.add_pali()
        new_probs = model.leaf_log_scores(ids, offsets, native_scores=False).exp()
        si, pi = model.label_to_id["si"], model.label_to_id["pi"]
        others = [i for i in range(176) if i != si]
        torch.testing.assert_close(new_probs[:, others], old_probs[:, others], rtol=1e-6, atol=1e-7)
        torch.testing.assert_close(new_probs[:, si] + new_probs[:, pi], old_probs[:, si], rtol=2e-6, atol=1e-7)
        torch.testing.assert_close(new_probs.sum(1), torch.ones(len(PROBES)), rtol=2e-6, atol=2e-6)
        assert torch.equal(model.output_weight[:len(old_weights)], old_weights)
    model.save_pretrained(out / "init177")
    restored = ContinualLID.from_pretrained(out / "init177")
    assert torch.equal(restored.embedding.weight, model.embedding.weight)
    assert torch.equal(restored.output_weight, model.output_weight)
    assert restored.config == model.config
    with torch.no_grad():
        torch.testing.assert_close(restored.leaf_log_scores(ids, offsets), model.leaf_log_scores(ids, offsets), rtol=0, atol=0)
    report.update(expanded_labels=len(model.labels), expansion_invariants_passed=True,
                  checkpoint_roundtrip_passed=True, gradient_check=gradient_check(restored),
                  base_sha256=model.config["source"]["sha256"], torch_version=torch.__version__)
    write_json(out / "parity_report.json", report)
    print(json.dumps(report, indent=2))
    print(f"PASS: original weights imported; untrained 177-label model: {out / 'init177'}")


if __name__ == "__main__":
    main()
