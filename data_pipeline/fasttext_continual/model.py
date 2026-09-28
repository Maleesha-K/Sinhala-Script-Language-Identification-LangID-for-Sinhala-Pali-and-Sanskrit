"""Pretrained feature mean + inherited hierarchical-softmax decision weights.

The saved model includes explicit paths. It is not a native fastText .bin.
"""

import copy
import hashlib
import json
import os
import struct
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.nn import functional as F

from .features import FeatureEncoder

BASE_URL = "https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin"
FORMAT_VERSION = 1


def sha256(path):
    with open(path, "rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temporary, path)


def huffman_paths(counts):
    """Match fastText v0.9.2 buildTree, including strict '<' tie breaking.

    Paths go from each leaf toward the root. Row IDs refer to the ORIGINAL
    output matrix, not to language indices. Do not re-sort the labels.
    """
    n = len(counts)
    sizes = [int(x) for x in counts] + [10**15] * (n - 1)
    parent = [-1] * (2 * n - 1)
    bits = [0] * (2 * n - 1)
    leaf, node = n - 1, n
    for i in range(n, 2 * n - 1):
        children = []
        for _ in range(2):
            if leaf >= 0 and sizes[leaf] < sizes[node]:
                children.append(leaf)
                leaf -= 1
            else:
                children.append(node)
                node += 1
        a, b = children
        sizes[i] = sizes[a] + sizes[b]
        parent[a] = parent[b] = i
        bits[b] = 1
    paths, codes = [], []
    for i in range(n):
        path, code = [], []
        while parent[i] != -1:
            path.append(parent[i] - n)
            code.append(bits[i])
            i = parent[i]
        paths.append(path)
        codes.append(code)
    return paths, codes


def pack_features(sequences, device="cpu"):
    lengths = np.asarray([len(s) for s in sequences], dtype=np.int64)
    offsets = np.concatenate(([0], np.cumsum(lengths)))
    flat = np.concatenate(sequences).astype(np.int64, copy=False)
    return (torch.from_numpy(flat).to(device), torch.from_numpy(offsets).to(device))


class ContinualLID(nn.Module):
    def __init__(self, config, words, input_weight, output_weight):
        super().__init__()
        self.config = copy.deepcopy(config)
        self.encoder = FeatureEncoder(words, config["args"])
        self.labels = list(config["labels"])
        self.label_to_id = {label: i for i, label in enumerate(self.labels)}
        # from_pretrained(freeze=False) keeps ALL input rows trainable.
        self.embedding = nn.EmbeddingBag.from_pretrained(
            input_weight, freeze=False, mode="mean", sparse=True,
            include_last_offset=True,
        )
        self.output_weight = nn.Parameter(output_weight)
        self._install_paths()

    def _install_paths(self):
        paths, codes = self.config["paths"], self.config["codes"]
        if not (len(paths) == len(codes) == len(self.labels)):
            raise ValueError("Label/path counts differ")
        width = max(map(len, paths))
        rows = torch.zeros((len(paths), width), dtype=torch.long)
        targets = torch.zeros_like(rows, dtype=torch.float32)
        mask = torch.zeros_like(rows, dtype=torch.bool)
        for i, (path, code) in enumerate(zip(paths, codes)):
            if len(path) != len(code) or not path or not set(code) <= {0, 1}:
                raise ValueError("Invalid hierarchical path")
            if min(path) < 0 or max(path) >= self.output_weight.shape[0]:
                raise ValueError("Path references a missing decision row")
            # Root-to-leaf order for inference, matching the native DFS.
            rows[i, :len(path)] = torch.tensor(path[::-1])
            targets[i, :len(code)] = torch.tensor(code[::-1], dtype=torch.float32)
            mask[i, :len(path)] = True
        device = self.output_weight.device
        for name, tensor in [("path_rows", rows), ("path_codes", targets), ("path_mask", mask)]:
            if name in self._buffers:
                self._buffers[name] = tensor.to(device)
            else:
                self.register_buffer(name, tensor.to(device), persistent=False)

    @property
    def device(self):
        return self.output_weight.device

    def hidden(self, features, offsets):
        return self.embedding(features, offsets)

    def logits(self, features, offsets):
        return F.linear(self.hidden(features, offsets), self.output_weight)

    def nll(self, features, offsets, targets):
        logits = self.logits(features, offsets)
        rows = self.path_rows[targets]
        values = logits.gather(1, rows)
        losses = F.binary_cross_entropy_with_logits(
            values, self.path_codes[targets], reduction="none")
        return (losses * self.path_mask[targets]).sum(dim=1)

    def leaf_log_scores(self, features, offsets, native_scores=True):
        logits = self.logits(features, offsets)
        selected = logits[:, self.path_rows]
        if native_scores:
            # Native HS prediction uses log(sigmoid(x) + 1e-5), not the
            # sigmoid lookup table used by its training loop. These scores
            # are slightly unnormalized; preserve them for comparisons.
            right = torch.sigmoid(selected)
            branches = torch.where(self.path_codes.bool(), right, 1.0 - right)
            terms = torch.log(branches + 1e-5)
        else:
            signed = selected * (2 * self.path_codes - 1)
            terms = F.logsigmoid(signed)
        return (terms * self.path_mask).sum(dim=2)

    @torch.no_grad()
    def predict(self, texts, k=1, batch_size=128, native_scores=True):
        """Return (labels, scores), or lists of those for a list of texts.

        Labels are plain ISO-2 codes, e.g. 'si', 'pi', 'sa'. Scores use the
        native epsilon convention by default. native_scores=False returns
        mathematically normalized hierarchical probabilities.
        """
        scalar = isinstance(texts, str)
        texts = [texts] if scalar else list(texts)
        if not 1 <= k <= len(self.labels):
            raise ValueError("k must be between 1 and the number of labels")
        self.eval()
        all_labels, all_scores = [], []
        for start in range(0, len(texts), batch_size):
            seq = [self.encoder.encode(t) for t in texts[start:start + batch_size]]
            ids, offsets = pack_features(seq, self.device)
            scores = self.leaf_log_scores(ids, offsets, native_scores).exp()
            values, indices = scores.topk(k, dim=1)
            all_labels.extend([[self.labels[j] for j in row] for row in indices.cpu().tolist()])
            all_scores.extend(values.cpu().tolist())
        return (all_labels[0], all_scores[0]) if scalar else (all_labels, all_scores)

    def add_pali(self):
        """Replace the Sinhala leaf with Sinhala(left)/Pali(right).

        All old decision rows and all input rows are retained. A zero NEW
        node divides the old Sinhala mass equally until training starts.
        The old matrix's unused final row is also retained unchanged.
        """
        if "pi" in self.labels or len(self.labels) != 176:
            raise ValueError("Expected original 176 labels, without Pali")
        si = self.label_to_id["si"]
        old_path = list(self.config["paths"][si])
        old_code = list(self.config["codes"][si])
        new_row = self.output_weight.shape[0]
        self.output_weight = nn.Parameter(torch.cat([
            self.output_weight.detach(), self.output_weight.new_zeros((1, self.output_weight.shape[1]))
        ]))
        self.config["paths"][si] = [new_row] + old_path
        self.config["codes"][si] = [0] + old_code
        self.config["paths"].append([new_row] + old_path)
        self.config["codes"].append([1] + old_code)
        self.labels.append("pi")
        self.config["labels"] = list(self.labels)
        self.label_to_id = {label: i for i, label in enumerate(self.labels)}
        self.config["expansion"] = {"parent_language": "si", "new_language": "pi",
                                    "new_decision_row": new_row, "initialization": "zeros"}
        self._install_paths()
        return self

    def save_pretrained(self, directory):
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        state = {"input": self.embedding.weight.detach().cpu().contiguous(),
                 "output": self.output_weight.detach().cpu().contiguous()}
        temporary = directory / "weights.pt.tmp"
        torch.save(state, temporary)
        os.replace(temporary, directory / "weights.pt")
        # Metadata includes explicit tree paths; no reconstruction from NEW
        # label frequencies occurs when loading an expanded checkpoint.
        write_json(directory / "vocab.json", self.encoder.words)
        write_json(directory / "config.json", self.config)

    @classmethod
    def from_pretrained(cls, directory_or_repo, device="cpu", revision=None):
        directory = Path(directory_or_repo)
        if not directory.is_dir():
            # Local-looking paths must fail locally, rather than becoming Hub IDs.
            if directory.is_absolute() or str(directory_or_repo).startswith(".") or len(directory.parts) != 2:
                raise FileNotFoundError(directory)
            from huggingface_hub import snapshot_download
            directory = Path(snapshot_download(
                repo_id=str(directory_or_repo), revision=revision,
                allow_patterns=["config.json", "vocab.json", "weights.pt"]))
        config = json.loads((directory / "config.json").read_text(encoding="utf-8"))
        if config.get("format_version") != FORMAT_VERSION:
            raise ValueError("Unsupported checkpoint format")
        words = json.loads((directory / "vocab.json").read_text(encoding="utf-8"))
        state = torch.load(directory / "weights.pt", map_location="cpu", weights_only=True)
        if state["input"].shape != (len(words) + config["args"]["bucket"], config["args"]["dim"]):
            raise ValueError("Input matrix and vocabulary/settings do not match")
        return cls(config, words, state["input"], state["output"]).to(device)

    @classmethod
    def from_fasttext(cls, path):
        """Import the complete official, unquantized checkpoint; verify separately."""
        import fasttext
        from fasttext.FastText import loss_name, model_name
        path = Path(path)
        with path.open("rb") as f:
            header = f.read(8)
        if struct.unpack("<ii", header) != (793712314, 12):
            raise ValueError("Expected fastText version-12 lid.176.bin")
        native = fasttext.load_model(str(path))
        if native.is_quantized():
            raise ValueError("Use lid.176.bin, not lid.176.ftz")
        a = native.f.getArgs()
        if a.loss != loss_name.hs or a.model != model_name.supervised:
            raise ValueError("Expected supervised hierarchical softmax")
        args = {k: getattr(a, k) for k in ["dim", "minn", "maxn", "bucket", "wordNgrams", "label"]}
        if [args[k] for k in ["dim", "minn", "maxn", "bucket", "wordNgrams"]] != [16, 2, 4, 2000000, 1]:
            raise ValueError(f"Unexpected LID-176 configuration: {args}")
        labels, counts = native.get_labels(include_freq=True)
        labels = [s.removeprefix(args["label"]) for s in labels]
        if len(labels) != 176 or not {"si", "sa"} <= set(labels) or "pi" in labels:
            raise ValueError("Unexpected original label inventory")
        words = native.get_words()
        input_weight = torch.from_numpy(native.get_input_matrix())
        output_weight = torch.from_numpy(native.get_output_matrix())
        if input_weight.shape != (len(words) + args["bucket"], args["dim"]):
            raise ValueError("Pruned/unexpected input matrix is not supported")
        if output_weight.shape != (176, args["dim"]):
            raise ValueError("Unexpected original output matrix")
        paths, codes = huffman_paths(counts)
        config = {"format_version": FORMAT_VERSION, "architecture": "fasttext_hierarchical_softmax",
                  "args": args, "labels": labels, "paths": paths, "codes": codes,
                  "original_label_counts": [int(x) for x in counts],
                  "original_output_rows": int(output_weight.shape[0]),
                  "source": {"url": BASE_URL, "sha256": sha256(path)},
                  "preprocessing": "replace LF with ASCII space; otherwise preserve text",
                  "prediction_scores": "fastText log(branch_probability + 1e-5)",
                  "parity_verified": False}
        return cls(config, words, input_weight, output_weight), native
