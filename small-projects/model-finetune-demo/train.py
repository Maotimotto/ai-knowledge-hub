"""LoRA fine-tuning with HuggingFace PEFT."""

import json
import os
from pathlib import Path
from typing import Optional

import torch
from dotenv import load_dotenv

load_dotenv()


def load_dataset(data_path: str = "data/instruction_data.json") -> list[dict]:
    """Load instruction dataset from JSON file."""
    if not Path(data_path).exists():
        print(f"⚠️  Dataset not found at {data_path}. Running prepare_data.py first...")
        from prepare_data import create_sample_dataset, save_dataset
        examples = create_sample_dataset()
        save_dataset(examples, data_path)
        return examples

    with open(data_path, "r", encoding="utf-8") as f:
        return json.load(f)


def format_prompt(example: dict) -> str:
    """Format a single example into training prompt."""
    text = f"### Instruction:\n{example['instruction']}\n\n"
    if example.get("input"):
        text += f"### Input:\n{example['input']}\n\n"
    text += f"### Response:\n{example['output']}"
    return text


def train(
    base_model: Optional[str] = None,
    data_path: str = "data/instruction_data.json",
    output_dir: Optional[str] = None,
    epochs: int = 3,
    batch_size: int = 2,
    learning_rate: float = 2e-4,
    lora_rank: int = 8,
    lora_alpha: int = 16,
) -> str:
    """
    Fine-tune a model using LoRA (Low-Rank Adaptation).

    Args:
        base_model: HuggingFace model name or path
        data_path: Path to instruction dataset JSON
        output_dir: Where to save the fine-tuned model
        epochs: Number of training epochs
        batch_size: Training batch size
        learning_rate: Learning rate
        lora_rank: LoRA rank (r)
        lora_alpha: LoRA alpha scaling parameter

    Returns:
        Path to saved model
    """
    from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, Trainer
    from peft import LoraConfig, get_peft_model, TaskType

    base_model = base_model or os.getenv("BASE_MODEL", "facebook/opt-350m")
    output_dir = output_dir or os.getenv("OUTPUT_DIR", "./output")

    print(f"📦 Loading base model: {base_model}")
    tokenizer = AutoTokenizer.from_pretrained(base_model)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        base_model,
        torch_dtype=torch.float32,
        device_map="auto" if torch.cuda.is_available() else None,
    )

    # Configure LoRA
    lora_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=lora_rank,
        lora_alpha=lora_alpha,
        lora_dropout=0.1,
        target_modules=["q_proj", "v_proj"] if "opt" in base_model.lower() else None,
    )

    model = get_peft_model(model, lora_config)
    trainable, total = model.get_nb_trainable_parameters()
    print(f"🔧 LoRA configured: {trainable:,} trainable / {total:,} total ({100*trainable/total:.2f}%)")

    # Load and format dataset
    examples = load_dataset(data_path)
    texts = [format_prompt(ex) for ex in examples]

    # Tokenize
    def tokenize(text: str) -> dict:
        result = tokenizer(
            text,
            truncation=True,
            max_length=512,
            padding="max_length",
            return_tensors="pt",
        )
        result["labels"] = result["input_ids"].clone()
        return {k: v.squeeze() for k, v in result.items()}

    tokenized = [tokenize(t) for t in texts]

    # Create simple dataset
    class SimpleDataset:
        def __init__(self, data: list[dict]):
            self.data = data
        def __len__(self) -> int:
            return len(self.data)
        def __getitem__(self, idx: int) -> dict:
            return self.data[idx]

    dataset = SimpleDataset(tokenized)

    # Training arguments
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=epochs,
        per_device_train_batch_size=batch_size,
        learning_rate=learning_rate,
        warmup_steps=10,
        logging_steps=5,
        save_strategy="epoch",
        remove_unused_columns=False,
        no_cuda=not torch.cuda.is_available(),
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
    )

    print(f"\n🚀 Starting fine-tuning...")
    print(f"   Epochs: {epochs}, Batch size: {batch_size}, LR: {learning_rate}")
    trainer.train()

    # Save model
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    print(f"\n✅ Model saved to {output_dir}")
    return output_dir


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="LoRA Fine-tuning")
    parser.add_argument("--model", type=str, default=None, help="Base model name")
    parser.add_argument("--data", type=str, default="data/instruction_data.json", help="Dataset path")
    parser.add_argument("--output", type=str, default=None, help="Output directory")
    parser.add_argument("--epochs", type=int, default=3, help="Number of epochs")
    parser.add_argument("--batch-size", type=int, default=2, help="Batch size")
    parser.add_argument("--lr", type=float, default=2e-4, help="Learning rate")
    parser.add_argument("--lora-rank", type=int, default=8, help="LoRA rank")
    args = parser.parse_args()

    train(
        base_model=args.model,
        data_path=args.data,
        output_dir=args.output,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr,
        lora_rank=args.lora_rank,
    )
