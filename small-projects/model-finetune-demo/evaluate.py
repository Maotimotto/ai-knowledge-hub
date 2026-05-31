"""Simple evaluation metrics for fine-tuned model."""

import json
import os
from pathlib import Path
from typing import Optional

import torch
from dotenv import load_dotenv

load_dotenv()


def compute_perplexity(model_path: str, test_texts: list[str]) -> dict:
    """Compute perplexity on test texts (lower is better)."""
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel

    base_model = os.getenv("BASE_MODEL", "facebook/opt-350m")
    tokenizer = AutoTokenizer.from_pretrained(base_model)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Load base model
    base = AutoModelForCausalLM.from_pretrained(base_model, torch_dtype=torch.float32)

    # Load fine-tuned model
    if Path(model_path).exists():
        ft_model = PeftModel.from_pretrained(base, model_path)
    else:
        print(f"⚠️  Model path {model_path} not found, evaluating base model only")
        ft_model = base

    ft_model.eval()
    base.eval()

    results = {"base_perplexities": [], "finetuned_perplexities": []}

    for text in test_texts:
        inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=256)
        with torch.no_grad():
            # Base model perplexity
            base_outputs = base(**inputs, labels=inputs["input_ids"])
            base_ppl = torch.exp(base_outputs.loss).item()
            results["base_perplexities"].append(base_ppl)

            # Fine-tuned model perplexity
            ft_outputs = ft_model(**inputs, labels=inputs["input_ids"])
            ft_ppl = torch.exp(ft_outputs.loss).item()
            results["finetuned_perplexities"].append(ft_ppl)

    results["avg_base_perplexity"] = sum(results["base_perplexities"]) / len(results["base_perplexities"])
    results["avg_finetuned_perplexity"] = sum(results["finetuned_perplexities"]) / len(results["finetuned_perplexities"])
    results["improvement"] = (
        (results["avg_base_perplexity"] - results["avg_finetuned_perplexity"])
        / results["avg_base_perplexity"] * 100
    )
    return results


def keyword_match_score(predictions: list[str], references: list[str]) -> dict:
    """Simple keyword overlap score between predictions and references."""
    scores = []
    for pred, ref in zip(predictions, references):
        pred_words = set(pred.lower().split())
        ref_words = set(ref.lower().split())
        if not ref_words:
            scores.append(0.0)
            continue
        overlap = pred_words & ref_words
        precision = len(overlap) / len(pred_words) if pred_words else 0
        recall = len(overlap) / len(ref_words)
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        scores.append(f1)

    return {
        "scores": scores,
        "avg_score": sum(scores) / len(scores) if scores else 0,
        "min_score": min(scores) if scores else 0,
        "max_score": max(scores) if scores else 0,
    }


def evaluate(model_path: str = "./output") -> dict:
    """Run full evaluation suite."""
    from prepare_data import create_sample_dataset
    from inference import generate_response

    test_examples = create_sample_dataset()[:3]

    predictions = []
    references = []
    for ex in test_examples:
        pred = generate_response(ex["instruction"], model_path=model_path)
        predictions.append(pred)
        references.append(ex["output"])

    kw_scores = keyword_match_score(predictions, references)

    return {
        "keyword_match": kw_scores,
        "predictions": predictions,
        "references": references,
    }


if __name__ == "__main__":
    results = evaluate()
    print("\n📊 Evaluation Results:")
    print(f"   Keyword Match F1: {results['keyword_match']['avg_score']:.3f}")
    print(f"\n📝 Sample predictions:")
    for i, (pred, ref) in enumerate(zip(results["predictions"], results["references"])):
        print(f"\n  [{i+1}] Prediction: {pred[:150]}...")
        print(f"      Reference:  {ref[:150]}...")
