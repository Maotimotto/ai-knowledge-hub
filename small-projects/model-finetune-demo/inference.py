"""Inference with fine-tuned model - compare before/after."""

import os
from pathlib import Path
from typing import Optional

import torch
from dotenv import load_dotenv

load_dotenv()


def generate_response(
    prompt: str,
    model_path: Optional[str] = None,
    max_new_tokens: int = 200,
    temperature: float = 0.7,
) -> str:
    """Generate a response using the fine-tuned (or base) model."""
    from transformers import AutoModelForCausalLM, AutoTokenizer

    base_model = os.getenv("BASE_MODEL", "facebook/opt-350m")
    tokenizer = AutoTokenizer.from_pretrained(base_model)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(base_model, torch_dtype=torch.float32)

    # Load LoRA weights if available
    if model_path and Path(model_path).exists():
        try:
            from peft import PeftModel
            model = PeftModel.from_pretrained(model, model_path)
            print(f"✅ Loaded fine-tuned model from {model_path}")
        except Exception as e:
            print(f"⚠️  Could not load fine-tuned model: {e}. Using base model.")
    else:
        print(f"📦 Using base model: {base_model}")

    model.eval()

    # Format prompt
    formatted = f"### Instruction:\n{prompt}\n\n### Response:\n"
    inputs = tokenizer(formatted, return_tensors="pt")

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            do_sample=True,
            top_p=0.9,
            pad_token_id=tokenizer.eos_token_id,
        )

    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    # Extract only the response part
    if "### Response:" in response:
        response = response.split("### Response:")[-1].strip()
    return response


def compare_before_after(prompt: str, model_path: str = "./output") -> dict:
    """Compare base model vs fine-tuned model responses."""
    print(f"\n{'='*60}")
    print(f"📝 Prompt: {prompt}")
    print(f"{'='*60}")

    # Base model
    print("\n🔵 BASE MODEL:")
    base_response = generate_response(prompt, model_path=None)
    print(f"   {base_response[:300]}")

    # Fine-tuned model
    print("\n🟢 FINE-TUNED MODEL:")
    ft_response = generate_response(prompt, model_path=model_path)
    print(f"   {ft_response[:300]}")

    return {"prompt": prompt, "base": base_response, "finetuned": ft_response}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Model Inference")
    parser.add_argument("--prompt", type=str, default="What is machine learning?", help="Input prompt")
    parser.add_argument("--model", type=str, default="./output", help="Fine-tuned model path")
    parser.add_argument("--compare", action="store_true", help="Compare base vs fine-tuned")
    args = parser.parse_args()

    if args.compare:
        prompts = [
            "What is machine learning?",
            "Explain how neural networks work.",
            "What are AI agents?",
        ]
        for p in prompts:
            compare_before_after(p, args.model)
    else:
        response = generate_response(args.prompt, model_path=args.model)
        print(f"\n📝 Response:\n{response}")
