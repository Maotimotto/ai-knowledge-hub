# Model Fine-tune Demo (模型微调演示)

End-to-end fine-tuning pipeline demonstrating **LoRA (Low-Rank Adaptation)** — the most practical approach for customizing large language models with minimal compute.

## What It Does

Prepare instruction datasets, fine-tune a language model using LoRA, evaluate results, and compare before/after performance. All with a small model that runs on CPU.

## Architecture

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Raw Text /   │    │  Instruction │    │  Tokenize &  │
│  Custom Data  │───▶│  Format      │───▶│  Dataset     │
│              │    │  (JSON)      │    │              │
└──────────────┘    └──────────────┘    └──────┬───────┘
                                               │
                    ┌──────────────┐    ┌──────▼───────┐
                    │  LoRA        │◀──│  Base Model   │
                    │  Adapters    │    │  (OPT-350M)  │
                    │  (rank=8)    │    │              │
                    └──────┬───────┘    └──────────────┘
                           │
                    ┌──────▼───────┐    ┌──────────────┐
                    │  Fine-tuned  │───▶│  Evaluate &  │
                    │  Model       │    │  Compare     │
                    └──────────────┘    └──────────────┘
```

## Setup

```bash
cd model-finetune-demo
pip install -r requirements.txt
cp .env.example .env
# Optional: Set HUGGINGFACE_TOKEN for gated models
```

## Run

### Step 1: Prepare Data
```bash
python prepare_data.py
# Creates data/instruction_data.json with sample AI knowledge Q&A
```

### Step 2: Fine-tune
```bash
python train.py --epochs 3 --batch-size 2 --lr 2e-4
# Fine-tunes OPT-350M with LoRA (runs on CPU in ~10 minutes)
```

### Step 3: Evaluate
```bash
python evaluate.py
# Computes keyword match scores and shows sample predictions
```

### Step 4: Compare
```bash
python inference.py --compare
# Shows side-by-side base vs fine-tuned model responses
```

## Demo Scenarios

### 1. Fine-tune on AI Knowledge
```bash
python prepare_data.py && python train.py --epochs 3
```

### 2. Use Custom Data
```bash
# Add your own instruction data to data/instruction_data.json
# Format: [{"instruction": "...", "input": "", "output": "..."}]
python train.py --data data/your_data.json
```

### 3. Adjust LoRA Parameters
```bash
# Higher rank = more capacity, more parameters
python train.py --lora-rank 16 --epochs 5
```

## What You Learn

- **LoRA**: Low-rank adaptation for parameter-efficient fine-tuning
- **Instruction Tuning**: Converting raw text to instruction format
- **PEFT Library**: HuggingFace's Parameter-Efficient Fine-Tuning toolkit
- **Training Hyperparameters**: Learning rate, batch size, epochs effects
- **Evaluation**: Perplexity, keyword matching, qualitative comparison
- **Trade-offs**: Quality vs compute cost, rank vs performance

## Commercial Applications

| Use Case | Description | Market |
|----------|-------------|--------|
| Legal AI | Fine-tune on legal documents and case law | LegalTech |
| Medical QA | Domain-specific medical knowledge models | HealthTech |
| Finance | Financial analysis and reporting models | FinTech |
| Customer Service | Company-specific support models | CX automation |
| Code Assistant | Language/framework-specific coding models | DevTools |

## Key Design Decisions

1. **LoRA over full fine-tuning** — 99% fewer trainable parameters
2. **Small base model (OPT-350M)** — runs on CPU for accessibility
3. **Instruction format** — standard `### Instruction / ### Response` template
4. **Simple evaluation** — keyword match + perplexity (no GPU-heavy metrics)
5. **Before/after comparison** — intuitive quality assessment
