"""
AI创作工坊 - LoRA Fine-Tuning Script

Fine-tune a model using LoRA (Low-Rank Adaptation) with PEFT library.
Supports configurable hyperparameters via command-line or config file.
"""

import argparse
import os
from pathlib import Path
from typing import Any, Optional

import yaml


# Default hyperparameters
DEFAULTS: dict[str, Any] = {
    "base_model": "meta-llama/Llama-3.2-1B",
    "lora_rank": 16,
    "lora_alpha": 32,
    "lora_dropout": 0.05,
    "target_modules": ["q_proj", "v_proj", "k_proj", "o_proj"],
    "learning_rate": 2e-4,
    "num_epochs": 3,
    "batch_size": 4,
    "gradient_accumulation_steps": 4,
    "max_seq_length": 1024,
    "warmup_steps": 100,
    "output_dir": "./output",
    "logging_steps": 10,
    "save_steps": 500,
}


def train(config: dict[str, Any]) -> None:
    """
    Run LoRA fine-tuning.

    Args:
        config: Training configuration dict
    """
    from datasets import load_dataset
    from peft import LoraConfig, get_peft_model, TaskType
    from transformers import (
        AutoModelForCausalLM, AutoTokenizer, TrainingArguments, Trainer,
        DataCollatorForLanguageModeling,
    )
    import torch

    # Merge defaults
    cfg = {**DEFAULTS, **config}
    print(f"Training config: {cfg}")

    # Load model and tokenizer
    print(f"Loading base model: {cfg['base_model']}")
    tokenizer = AutoTokenizer.from_pretrained(cfg["base_model"], trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        cfg["base_model"],
        torch_dtype=torch.float16,
        device_map="auto",
        trust_remote_code=True,
    )

    # Configure LoRA
    peft_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=cfg["lora_rank"],
        lora_alpha=cfg["lora_alpha"],
        lora_dropout=cfg["lora_dropout"],
        target_modules=cfg["target_modules"],
        bias="none",
    )
    model = get_peft_model(model, peft_config)
    model.print_trainable_parameters()

    # Load dataset
    data_dir = cfg.get("data_dir", "./prepared")
    dataset = load_dataset("json", data_files={
        "train": os.path.join(data_dir, "train.jsonl"),
        "validation": os.path.join(data_dir, "val.jsonl"),
    })

    def tokenize(examples: dict) -> dict:
        prompts = [f"{p}\n{c}" for p, c in zip(examples["prompt"], examples["completion"])]
        return tokenizer(prompts, truncation=True, max_length=cfg["max_seq_length"], padding="max_length")

    tokenized = dataset.map(tokenize, batched=True, remove_columns=dataset["train"].column_names)

    # Training arguments
    output_dir = cfg["output_dir"]
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=cfg["num_epochs"],
        per_device_train_batch_size=cfg["batch_size"],
        gradient_accumulation_steps=cfg["gradient_accumulation_steps"],
        learning_rate=cfg["learning_rate"],
        warmup_steps=cfg["warmup_steps"],
        logging_steps=cfg["logging_steps"],
        save_steps=cfg["save_steps"],
        evaluation_strategy="steps",
        eval_steps=cfg["save_steps"],
        fp16=True,
        report_to="tensorboard",
        run_name="ai-workshop-lora",
    )

    # Train
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized["train"],
        eval_dataset=tokenized["validation"],
        data_collator=DataCollatorForLanguageModeling(tokenizer, mlm=False),
    )

    print("Starting training...")
    trainer.train()

    # Save
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    print(f"Model saved to {output_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LoRA fine-tuning")
    parser.add_argument("--config", help="YAML config file path")
    parser.add_argument("--base-model", help="Base model name or path")
    parser.add_argument("--data-dir", help="Training data directory")
    parser.add_argument("--output-dir", help="Output directory")
    parser.add_argument("--epochs", type=int, help="Number of epochs")
    parser.add_argument("--lr", type=float, help="Learning rate")
    parser.add_argument("--lora-rank", type=int, help="LoRA rank")
    args = parser.parse_args()

    # Load config file
    config: dict[str, Any] = {}
    if args.config:
        with open(args.config, "r") as f:
            config = yaml.safe_load(f) or {}

    # Override with CLI args
    if args.base_model:
        config["base_model"] = args.base_model
    if args.data_dir:
        config["data_dir"] = args.data_dir
    if args.output_dir:
        config["output_dir"] = args.output_dir
    if args.epochs:
        config["num_epochs"] = args.epochs
    if args.lr:
        config["learning_rate"] = args.lr
    if args.lora_rank:
        config["lora_rank"] = args.lora_rank

    train(config)
