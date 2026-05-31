"""
AI创作工坊 - Fine-Tuning Data Preparation

Converts raw text data into instruction-tuned format and splits into train/val sets.
"""

import argparse
import json
import random
from pathlib import Path
from typing import Any


def to_instruction_format(
    text: str,
    instruction: str = "Write a helpful response based on the following context.",
) -> dict[str, str]:
    """Convert raw text to instruction format."""
    return {
        "instruction": instruction,
        "input": "",
        "output": text,
    }


def to_alpaca_format(example: dict[str, Any]) -> dict[str, str]:
    """Convert an example to Alpaca format with prompt field."""
    instruction = example.get("instruction", "")
    inp = example.get("input", "")
    output = example.get("output", "")

    if inp:
        prompt = f"{instruction}\n\nInput: {inp}"
    else:
        prompt = instruction

    return {
        "prompt": prompt,
        "completion": output,
    }


def prepare_dataset(
    input_path: str,
    output_dir: str,
    val_ratio: float = 0.1,
    format_type: str = "alpaca",
    seed: int = 42,
) -> dict[str, int]:
    """
    Prepare dataset for fine-tuning.

    Args:
        input_path: Path to input JSONL file
        output_dir: Output directory for train/val splits
        val_ratio: Fraction of data for validation
        format_type: Output format (alpaca, instruction)
        seed: Random seed for reproducibility

    Returns:
        Dict with train and val counts
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Load examples
    examples: list[dict[str, Any]] = []
    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                examples.append(json.loads(line))

    print(f"Loaded {len(examples)} examples from {input_path}")

    # Convert format
    formatter = to_alpaca_format if format_type == "alpaca" else lambda x: x
    formatted = [formatter(ex) for ex in examples]

    # Shuffle and split
    random.seed(seed)
    random.shuffle(formatted)

    val_count = max(1, int(len(formatted) * val_ratio))
    val_data = formatted[:val_count]
    train_data = formatted[val_count:]

    # Write splits
    for split_name, split_data in [("train", train_data), ("val", val_data)]:
        out_file = output_path / f"{split_name}.jsonl"
        with open(out_file, "w", encoding="utf-8") as f:
            for item in split_data:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        print(f"Wrote {len(split_data)} examples to {out_file}")

    return {"train": len(train_data), "val": len(val_data)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare data for fine-tuning")
    parser.add_argument("--input", required=True, help="Input JSONL file")
    parser.add_argument("--output", default="./prepared", help="Output directory")
    parser.add_argument("--val-ratio", type=float, default=0.1, help="Validation split ratio")
    parser.add_argument("--format", choices=["alpaca", "instruction"], default="alpaca")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    stats = prepare_dataset(args.input, args.output, args.val_ratio, args.format, args.seed)
    print(f"\nDataset prepared: {stats['train']} train, {stats['val']} val")
