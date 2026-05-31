"""
AI创作工坊 - Fine-Tuning Evaluation

Evaluate a fine-tuned model using perplexity calculation and sample generation.
"""

import argparse
import json
import math
from typing import Any

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel


def calculate_perplexity(
    model: Any,
    tokenizer: Any,
    test_data: list[str],
    max_length: int = 512,
) -> float:
    """
    Calculate perplexity on test data.

    Args:
        model: Loaded model
        tokenizer: Loaded tokenizer
        test_data: List of text strings
        max_length: Maximum sequence length

    Returns:
        Average perplexity
    """
    model.eval()
    total_loss = 0.0
    total_tokens = 0

    with torch.no_grad():
        for text in test_data:
            inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=max_length)
            input_ids = inputs["input_ids"].to(model.device)

            outputs = model(input_ids=input_ids, labels=input_ids)
            total_loss += outputs.loss.item() * input_ids.numel()
            total_tokens += input_ids.numel()

    avg_loss = total_loss / total_tokens
    perplexity = math.exp(avg_loss)
    return perplexity


def generate_samples(
    model: Any,
    tokenizer: Any,
    prompts: list[str],
    max_new_tokens: int = 200,
    temperature: float = 0.7,
) -> list[str]:
    """
    Generate sample outputs for qualitative evaluation.

    Args:
        model: Loaded model
        tokenizer: Loaded tokenizer
        prompts: List of input prompts
        max_new_tokens: Max tokens to generate
        temperature: Sampling temperature

    Returns:
        List of generated texts
    """
    model.eval()
    results = []

    for prompt in prompts:
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=max(temperature, 1e-7),
                do_sample=temperature > 0,
            )
        generated = tokenizer.decode(outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
        results.append(generated)

    return results


def evaluate(model_path: str, base_model: str, test_file: str) -> dict[str, Any]:
    """
    Run full evaluation on a fine-tuned model.

    Args:
        model_path: Path to LoRA adapter or merged model
        base_model: Base model name (for LoRA models)
        test_file: Path to test JSONL file

    Returns:
        Evaluation results
    """
    print(f"Loading tokenizer: {base_model}")
    tokenizer = AutoTokenizer.from_pretrained(base_model, trust_remote_code=True)

    print(f"Loading model: {base_model} + {model_path}")
    base = AutoModelForCausalLM.from_pretrained(base_model, torch_dtype=torch.float16, device_map="auto")
    model = PeftModel.from_pretrained(base, model_path)
    model.eval()

    # Load test data
    test_texts: list[str] = []
    with open(test_file, "r") as f:
        for line in f:
            entry = json.loads(line.strip())
            prompt = entry.get("prompt", "")
            completion = entry.get("completion", "")
            test_texts.append(f"{prompt}\n{completion}")

    print(f"Calculating perplexity on {len(test_texts)} examples...")
    ppl = calculate_perplexity(model, tokenizer, test_texts)

    # Sample generation
    sample_prompts = [t.split("\n")[0] for t in test_texts[:3]]
    print("Generating samples...")
    samples = generate_samples(model, tokenizer, sample_prompts)

    results = {
        "perplexity": round(ppl, 2),
        "test_samples": len(test_texts),
        "generations": [{"prompt": p, "output": s} for p, s in zip(sample_prompts, samples)],
    }

    print(f"\nPerplexity: {ppl:.2f}")
    for i, gen in enumerate(results["generations"]):
        print(f"\n--- Sample {i+1} ---")
        print(f"Prompt: {gen['prompt'][:100]}...")
        print(f"Output: {gen['output'][:200]}...")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate fine-tuned model")
    parser.add_argument("--model", required=True, help="Path to LoRA adapter")
    parser.add_argument("--base-model", default="meta-llama/Llama-3.2-1B", help="Base model")
    parser.add_argument("--test-data", required=True, help="Test JSONL file")
    args = parser.parse_args()

    results = evaluate(args.model, args.base_model, args.test_data)

    output_file = "evaluation_results.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {output_file}")
