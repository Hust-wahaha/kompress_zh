from __future__ import annotations

import argparse
import json
import platform
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from zh_plaintext_compressor.common.naming import (
    DEFAULT_DATASET_TAG,
    dataset_file,
    make_experiment_dir,
    normalize_model_tag,
)
from zh_plaintext_compressor.common.schema import DEFAULT_SYSTEM_PROMPT

MODEL_ID = "Qwen/Qwen3.5-0.8B"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-tag", type=str, default=DEFAULT_DATASET_TAG)
    parser.add_argument("--model-id", type=str, default=MODEL_ID)
    parser.add_argument("--model-tag", type=str, default=None)
    parser.add_argument("--train-file", type=Path, default=None)
    parser.add_argument("--val-file", type=Path, default=None)
    parser.add_argument("--run-tag", type=str, default="baseline")
    parser.add_argument("--system", type=str, default=DEFAULT_SYSTEM_PROMPT)
    parser.add_argument("--max-length", type=int, default=2048)
    parser.add_argument("--learning-rate", type=float, default=1e-4)
    parser.add_argument("--train-batch-size", type=int, default=1)
    parser.add_argument("--eval-batch-size", type=int, default=1)
    parser.add_argument("--gradient-accumulation-steps", type=int, default=16)
    parser.add_argument("--num-train-epochs", type=float, default=1.0)
    parser.add_argument("--save-steps", type=int, default=25)
    parser.add_argument("--eval-steps", type=int, default=25)
    parser.add_argument("--logging-steps", type=int, default=5)
    parser.add_argument(
        "--language-model-only",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Must remain enabled for this plain-text compressor; vision encoder is not used.",
    )
    _default_workers = 0 if platform.system() == "Windows" else 1
    parser.add_argument(
        "--dataloader-num-workers",
        type=int,
        default=_default_workers,
        help="Number of DataLoader workers. Must be 0 on Windows (multiprocessing spawn limitation).",
    )
    return parser.parse_args()


def resolve_dataset_path(args: argparse.Namespace, split: str) -> Path:
    if split == "train" and args.train_file is not None:
        return args.train_file
    if split == "val" and args.val_file is not None:
        return args.val_file
    return dataset_file(split, args.dataset_tag)


def main() -> None:
    from datasets import load_dataset as hf_load_dataset
    from peft import LoraConfig, get_peft_model
    from swift import get_template
    from swift.dataset import EncodePreprocessor
    from swift.trainers import Seq2SeqTrainer, Seq2SeqTrainingArguments
    from swift.utils import find_all_linears, get_logger, get_model_parameter_info, seed_everything

    from zh_plaintext_compressor.common.swift_compat import get_model_processor_language_only

    logger = get_logger()
    seed_everything(42)

    args = parse_args()
    if not args.language_model_only:
        raise SystemExit("`--no-language-model-only` is forbidden for this project.")
    train_path = resolve_dataset_path(args, "train")
    val_path = resolve_dataset_path(args, "val")
    model_tag = normalize_model_tag(args.model_id, args.model_tag)
    run_dir = make_experiment_dir(
        stage="train",
        dataset_tag=args.dataset_tag,
        model_tag=model_tag,
        suffix=args.run_tag,
    )
    output_dir = run_dir / "checkpoints"

    with (run_dir / "metrics" / "run_config.json").open("w", encoding="utf-8") as handle:
        json.dump(
            {
                "model_id": args.model_id,
                "model_tag": model_tag,
                "dataset_tag": args.dataset_tag,
                "train_dataset": str(train_path),
                "val_dataset": str(val_path),
                "run_dir": str(run_dir),
                "system": args.system,
                "max_length": args.max_length,
                "learning_rate": args.learning_rate,
                "gradient_accumulation_steps": args.gradient_accumulation_steps,
                "num_train_epochs": args.num_train_epochs,
                "language_model_only": args.language_model_only,
            },
            handle,
            ensure_ascii=False,
            indent=2,
        )

    model, tokenizer = get_model_processor_language_only(
        args.model_id,
        enabled=args.language_model_only,
    )
    template = get_template(tokenizer, default_system=args.system, max_length=args.max_length)
    template.set_mode("train")

    target_modules = find_all_linears(model)
    model = get_peft_model(
        model,
        LoraConfig(
            task_type="CAUSAL_LM",
            r=8,
            lora_alpha=32,
            target_modules=target_modules,
        ),
    )
    logger.info(get_model_parameter_info(model))

    train_dataset = hf_load_dataset("json", data_files=str(train_path), split="train")
    val_dataset = hf_load_dataset("json", data_files=str(val_path), split="train")
    train_dataset = EncodePreprocessor(template=template)(train_dataset)
    val_dataset = EncodePreprocessor(template=template)(val_dataset)

    training_args = Seq2SeqTrainingArguments(
        output_dir=str(output_dir),
        learning_rate=args.learning_rate,
        per_device_train_batch_size=args.train_batch_size,
        per_device_eval_batch_size=args.eval_batch_size,
        gradient_checkpointing=True,
        weight_decay=0.1,
        lr_scheduler_type="cosine",
        warmup_ratio=0.05,
        report_to=["tensorboard"],
        logging_first_step=True,
        save_strategy="steps",
        save_steps=args.save_steps,
        eval_strategy="steps",
        eval_steps=args.eval_steps,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        num_train_epochs=args.num_train_epochs,
        save_total_limit=2,
        logging_steps=args.logging_steps,
        dataloader_num_workers=args.dataloader_num_workers,
        data_seed=42,
    )

    model.enable_input_require_grads()
    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        template=template,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
    )
    trainer.train()

    with (run_dir / "metrics" / "last_checkpoint.txt").open("w", encoding="utf-8") as handle:
        handle.write(str(trainer.state.last_model_checkpoint or output_dir))


if __name__ == "__main__":
    if "--help" in sys.argv or "-h" in sys.argv:
        parse_args()
        raise SystemExit(0)
    main()
