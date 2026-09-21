"""Supervised continuation: inherited embeddings + inherited HS nodes + Pali node."""

import argparse
import json
import math
import platform
import random
import shutil
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader
from tqdm.auto import tqdm

from .data import EncodedDataset, check_splits, collate, load_records, subset_per_group
from .evaluate import evaluate_encoded
from .model import ContinualLID, sha256, write_json


def copy_model(source, destination):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    for name in ["weights.pt", "vocab.json", "config.json"]:
        temp = destination / (name + ".tmp")
        shutil.copyfile(Path(source) / name, temp)
        temp.replace(destination / name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--init", required=True, help="Verified init177 directory")
    parser.add_argument("--train", required=True)
    parser.add_argument("--val", required=True)
    parser.add_argument("--out", required=True, help="Use a NEW run directory; Drive path works in Colab")
    parser.add_argument("--epochs", type=int, default=5, help="Total epochs, including completed ones when resuming")
    parser.add_argument("--lr", type=float, default=0.01)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--threads", type=int, default=2)
    parser.add_argument("--balance", choices=["none", "group"], default="none")
    parser.add_argument("--pilot-per-group", type=int)
    parser.add_argument("--pilot-val-per-group", type=int)
    parser.add_argument("--resume", action="store_true", help="Continue from the last COMPLETE epoch in --out")
    args = parser.parse_args()
    if args.epochs < 1 or args.batch_size < 1 or not math.isfinite(args.lr) or args.lr <= 0:
        raise ValueError("epochs, batch size and learning rate must be positive")
    if args.device.startswith("cuda") and not torch.cuda.is_available():
        raise RuntimeError("CUDA is unavailable; select a GPU runtime or use --device cpu")
    torch.set_num_threads(args.threads)
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(args.seed)
        # Record that parallel embedding operations may still vary on GPU.
        torch.backends.cudnn.benchmark = False
    out = Path(args.out)
    if out.exists() and any(out.iterdir()) and not args.resume:
        raise FileExistsError("Nonempty run directory: choose a new --out or use --resume")
    if args.resume and not (out / "last.json").exists():
        raise FileNotFoundError("No complete epoch to resume (last.json is missing)")
    train_records, val_records = load_records(args.train), load_records(args.val)
    split_report = check_splits(train_records, val_records)
    train_records = subset_per_group(train_records, args.pilot_per_group, args.seed)
    val_records = subset_per_group(val_records, args.pilot_val_per_group, args.seed)
    settings = {
        "train_sha256": sha256(args.train), "val_sha256": sha256(args.val),
        "init_weights_sha256": sha256(Path(args.init) / "weights.pt"),
        "init_config_sha256": sha256(Path(args.init) / "config.json"),
        "lr": args.lr, "batch_size": args.batch_size, "seed": args.seed,
        "balance": args.balance, "pilot_per_group": args.pilot_per_group,
        "pilot_val_per_group": args.pilot_val_per_group,
        "optimizer": "SGD; momentum=0; weight_decay=0; constant learning rate",
        "loss": "mean of per-example hierarchical NLL; exact sigmoid",
    }
    start_epoch, best_score, best_epoch, history = 0, -1.0, None, []
    if args.resume:
        run = json.loads((out / "run.json").read_text())
        if settings != run["settings"]:
            raise ValueError("Resume settings/data differ from the saved run; start a new run instead")
        last = json.loads((out / "last.json").read_text())
        checkpoint = out / last["checkpoint"]
        model = ContinualLID.from_pretrained(checkpoint, device=args.device)
        state = model.config["training"]
        start_epoch, best_score, best_epoch = state["epoch"], state["best_macro_f1"], state["best_epoch"]
        history = json.loads((checkpoint / "history.json").read_text())
        # Recover a best/ copy interrupted while writing; complete epoch
        # directories are the authoritative checkpoints.
        copy_model(out / f"epoch-{best_epoch:03d}", out / "best")
    else:
        model = ContinualLID.from_pretrained(args.init, device=args.device)
        out.mkdir(parents=True, exist_ok=True)
        write_json(out / "run.json", {"settings": settings, "split_validation": split_report,
                   "train_records_used": len(train_records), "val_records_used": len(val_records),
                   "python_version": platform.python_version(), "torch_version": torch.__version__,
                   "numpy_version": np.__version__, "device": args.device,
                   "reproducibility": "Seeded sampling and epoch shuffles; GPU reductions may be nondeterministic."})
    if not model.config.get("parity_verified") or len(model.labels) != 177 or "pi" not in model.labels:
        raise ValueError("Run verify.py first and use its init177 output")
    if not all(p.requires_grad for p in model.parameters()):
        raise RuntimeError("Inherited parameters must be trainable")
    if start_epoch >= args.epochs:
        print(f"Already completed {start_epoch} epochs; best checkpoint: {out / 'best'}")
        return
    train_set = EncodedDataset(train_records, model, args.balance, "Training feature IDs")
    val_set = EncodedDataset(val_records, model, "none", "Validation feature IDs")
    val_loader = DataLoader(val_set, batch_size=args.batch_size, shuffle=False, collate_fn=collate, num_workers=0)
    # Cached IDs still look up TRAINABLE embeddings every batch.
    optimizer = torch.optim.SGD(model.parameters(), lr=args.lr, momentum=0, weight_decay=0, foreach=False)
    # This SGD has no momentum/optimizer tensors to restore. The next epoch's
    # shuffle is determined by seed+epoch, so resuming uses the same order.
    if not args.resume:
        initial = evaluate_encoded(model, val_loader, val_records)
        write_json(out / "validation_before_training.json", initial)
        print(f"Untrained expanded model: macro-F1={initial['language_macro_f1']:.6f}", flush=True)
    for epoch in range(start_epoch + 1, args.epochs + 1):
        generator = torch.Generator().manual_seed(args.seed + epoch)
        loader = DataLoader(train_set, batch_size=args.batch_size, shuffle=True,
                            generator=generator, collate_fn=collate, num_workers=0)
        model.train()
        total_loss, examples = 0.0, 0
        progress = tqdm(loader, desc=f"Epoch {epoch}/{args.epochs}")
        for ids, offsets, targets, weights in progress:
            ids, offsets = ids.to(model.device), offsets.to(model.device)
            targets, weights = targets.to(model.device), weights.to(model.device)
            optimizer.zero_grad(set_to_none=True)
            losses = model.nll(ids, offsets, targets)
            loss = (losses * weights).mean()
            if not torch.isfinite(loss):
                raise FloatingPointError("Non-finite loss; last complete epoch remains available")
            loss.backward()
            optimizer.step()
            total_loss += float(loss.detach()) * targets.numel()
            examples += targets.numel()
            progress.set_postfix(loss=f"{total_loss/examples:.4f}")
        result = evaluate_encoded(model, val_loader, val_records)
        score = result["language_macro_f1"]
        improved = score > best_score
        if improved:
            best_score, best_epoch = score, epoch
        model.config["training"] = {"epoch": epoch, "best_epoch": best_epoch,
                                    "best_macro_f1": best_score, "settings": settings,
                                    "train_records": len(train_records), "val_records": len(val_records)}
        entry = {"epoch": epoch, "train_objective": total_loss/examples,
                 "validation_macro_f1": score, "validation_accuracy": result["accuracy"]}
        history.append(entry)
        checkpoint = out / f"epoch-{epoch:03d}"
        model.save_pretrained(checkpoint)
        write_json(checkpoint / "validation.json", result)
        write_json(checkpoint / "history.json", history)
        # Update pointer only AFTER all checkpoint files are complete.
        write_json(out / "last.json", {"checkpoint": checkpoint.name, "epoch": epoch})
        if improved:
            copy_model(checkpoint, out / "best")
        write_json(out / "history.json", history)
        write_json(out / "best.json", {"checkpoint": f"epoch-{best_epoch:03d}", "macro_f1": best_score})
        print(json.dumps(entry), flush=True)
    print(f"Done. Best TRAINED epoch: {best_epoch}; validation macro-F1={best_score:.6f}")
    print(f"Load {out / 'best'} (compare it separately with the untrained expansion).")


if __name__ == "__main__":
    main()
