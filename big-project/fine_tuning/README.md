# Fine-Tuning Guide

## What is Fine-Tuning?

Fine-tuning adapts a pre-trained LLM to your specific task by continuing training on your own data. Instead of training from scratch, you start with a model that already understands language and teach it your domain.

## When to Use Fine-Tuning

- **RAG is not enough**: When your task requires a specific output format or style
- **Domain expertise**: Medical, legal, financial jargon
- **Consistent format**: JSON output, specific writing style
- **Few-shot doesn't work**: When prompt engineering can't achieve your goals

## When NOT to Use Fine-Tuning

- Simple Q&A → Use RAG instead
- General knowledge → Use a better base model
- Small datasets (<100 examples) → Use few-shot prompting

## LoRA (Low-Rank Adaptation)

LoRA is a parameter-efficient fine-tuning method:

- Instead of updating all model weights, LoRA adds small trainable matrices
- Typically 0.1-1% of total parameters are trained
- Reduces memory requirements by 10-100x
- Results are often comparable to full fine-tuning

```
Original: W (d × d)
LoRA:     W + ΔW = W + B × A
          where A is (d × r) and B is (r × d), r << d
```

## Step-by-Step Process

### 1. Prepare Your Data

Convert your data to instruction format:

```json
{"instruction": "Summarize this text", "input": "Long text...", "output": "Summary..."}
```

Run: `python prepare_data.py --input data.jsonl --output prepared/`

### 2. Configure Training

Edit `train.py` hyperparameters:
- `LORA_RANK`: Higher = more capacity (8-64)
- `LEARNING_RATE`: Start with 2e-4
- `NUM_EPOCHS`: 1-3 for LoRA
- `BATCH_SIZE`: Based on GPU memory

### 3. Train

```bash
python train.py --config config.yaml
```

Monitor: `tensorboard --logdir ./logs`

### 4. Evaluate

```bash
python evaluate.py --model ./output --test-data test.jsonl
```

### 5. Deploy

Merge LoRA weights into base model:
```python
model = model.merge_and_unload()
model.save_pretrained("./merged_model")
```

## Tips

- Start with a small dataset (1000-5000 examples) to validate
- Use validation loss to detect overfitting
- LoRA rank 16 is a good starting point
- Train for 1-3 epochs; more epochs risk overfitting
- Always compare against the base model
