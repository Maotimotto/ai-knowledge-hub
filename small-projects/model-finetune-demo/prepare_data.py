"""Prepare instruction dataset from custom text for fine-tuning."""

import json
import os
from pathlib import Path
from typing import Optional


def create_sample_dataset() -> list[dict[str, str]]:
    """Create a sample instruction dataset for AI assistant training."""
    return [
        {
            "instruction": "Explain what machine learning is in simple terms.",
            "input": "",
            "output": "Machine learning is a type of artificial intelligence where computers learn patterns from data instead of being explicitly programmed. Think of it like teaching a child: instead of giving rules, you show examples, and the computer figures out the patterns itself."
        },
        {
            "instruction": "What is the difference between AI, ML, and deep learning?",
            "input": "",
            "output": "AI (Artificial Intelligence) is the broadest concept — machines mimicking human intelligence. ML (Machine Learning) is a subset of AI where systems learn from data. Deep Learning is a subset of ML using neural networks with many layers. Think of it as: AI ⊃ ML ⊃ Deep Learning."
        },
        {
            "instruction": "How does a neural network work?",
            "input": "",
            "output": "A neural network works like a chain of simple decisions. Data enters through input neurons, passes through hidden layers where each neuron applies a weighted calculation and activation function, and produces output. During training, the network adjusts its weights based on errors, gradually improving its predictions."
        },
        {
            "instruction": "What is transfer learning?",
            "input": "",
            "output": "Transfer learning reuses a model trained on one task for a different but related task. For example, a model trained on millions of images can be fine-tuned to recognize specific objects with just a few hundred examples. This saves time, compute, and data."
        },
        {
            "instruction": "Explain the concept of embeddings.",
            "input": "",
            "output": "Embeddings are numerical representations of data (text, images, etc.) in a high-dimensional space where similar items are close together. For example, 'king' and 'queen' would have similar embeddings. They capture semantic meaning, making them essential for search, recommendations, and NLP tasks."
        },
        {
            "instruction": "What is RAG in the context of LLMs?",
            "input": "",
            "output": "RAG (Retrieval-Augmented Generation) combines a language model with a knowledge retrieval system. Instead of relying solely on the model's training data, RAG retrieves relevant documents from a database and uses them as context to generate more accurate, up-to-date, and verifiable answers."
        },
        {
            "instruction": "How do transformers work in NLP?",
            "input": "",
            "output": "Transformers use a mechanism called 'attention' to process all words in a sentence simultaneously, rather than one by one. Self-attention lets each word consider every other word to understand context. This parallel processing and contextual understanding makes transformers the foundation of modern NLP models like GPT and BERT."
        },
        {
            "instruction": "What is prompt engineering?",
            "input": "",
            "output": "Prompt engineering is the practice of designing input prompts to get better outputs from language models. Techniques include: being specific, providing examples (few-shot), setting a role, breaking complex tasks into steps, and specifying output format. It's the art of communicating effectively with AI."
        },
        {
            "instruction": "Explain fine-tuning vs few-shot learning.",
            "input": "",
            "output": "Fine-tuning updates a model's weights by training it on domain-specific data, permanently changing its behavior. Few-shot learning provides examples in the prompt without changing the model. Fine-tuning is better for consistent domain expertise; few-shot is better for flexibility and quick adaptation."
        },
        {
            "instruction": "What are AI agents?",
            "input": "",
            "output": "AI agents are autonomous systems that can perceive their environment, make decisions, and take actions to achieve goals. Unlike simple chatbots, agents can use tools (search, code, APIs), maintain memory, plan multi-step tasks, and adapt their strategy based on feedback. They represent the next evolution beyond simple LLM interactions."
        },
    ]


def text_to_instructions(text: str, chunk_size: int = 300) -> list[dict[str, str]]:
    """Convert raw text into instruction-format examples using simple heuristics."""
    sentences = [s.strip() for s in text.replace("\n", " ").split(". ") if len(s.strip()) > 20]
    examples = []

    for i in range(0, len(sentences) - 1, 2):
        context = sentences[i]
        if i + 1 < len(sentences):
            answer = sentences[i + 1]
        else:
            continue

        examples.append({
            "instruction": f"Explain the following concept: {context[:100]}",
            "input": "",
            "output": f"{context} {answer}"
        })

    return examples


def save_dataset(examples: list[dict[str, str]], output_path: str = "data/instruction_data.json") -> str:
    """Save dataset in JSON format for fine-tuning."""
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(examples, f, indent=2, ensure_ascii=False)
    return output_path


def format_for_training(examples: list[dict[str, str]]) -> list[str]:
    """Format examples into training text with instruction template."""
    formatted = []
    for ex in examples:
        text = f"### Instruction:\n{ex['instruction']}\n\n"
        if ex.get("input"):
            text += f"### Input:\n{ex['input']}\n\n"
        text += f"### Response:\n{ex['output']}"
        formatted.append(text)
    return formatted


if __name__ == "__main__":
    # Generate sample dataset
    examples = create_sample_dataset()
    path = save_dataset(examples)
    print(f"✅ Created dataset with {len(examples)} examples at {path}")

    # Show sample
    print("\n📝 Sample entry:")
    print(json.dumps(examples[0], indent=2))

    # Show formatted version
    formatted = format_for_training(examples)
    print(f"\n📋 Formatted training text (first entry):")
    print(formatted[0][:300] + "...")
