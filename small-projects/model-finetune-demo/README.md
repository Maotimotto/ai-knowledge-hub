# Model Fine-tune Demo (模型微调演示)

> 端到端LoRA微调管线，演示参数高效微调的完整流程

## 项目简介

准备指令数据集、使用LoRA微调语言模型、评估结果并对比前后效果。使用小模型(OPT-350M)在CPU上即可运行，10分钟内完成微调。

## 架构图

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

---

## 代码走读 (Code Walkthrough)

### `prepare_data.py` — 数据准备与格式化

将原始文本转换为**指令微调格式**(instruction/input/output)。`create_sample_dataset()`生成10条AI知识Q&A样本。`text_to_instructions()`将任意长文本自动切分为指令格式——每两句组成一个instruction-output对。`format_for_training()`将数据格式化为 `### Instruction: ... ### Response: ...` 的标准模板。

- **关键函数**: `text_to_instructions()` — 自动将文本转为指令格式, `save_dataset()` — JSON持久化
- **核心模式**: 指令微调数据格式、自动数据增强

### `train.py` — LoRA微调训练

使用HuggingFace PEFT库实现LoRA微调。`train()`函数加载基础模型，配置LoRA适配器(rank=8, alpha=16, dropout=0.1)，然后用HuggingFace Trainer训练。关键参数：`target_modules=["q_proj", "v_proj"]`表示只在注意力的Q和V矩阵上添加LoRA。训练后只保存LoRA权重（通常几十MB），而非完整模型。

- **关键函数**: `train()` — LoRA微调主函数, `format_prompt()` — 数据格式化
- **关键参数**: `lora_rank`(低秩维度), `lora_alpha`(缩放因子), `target_modules`(适配目标层)
- **核心模式**: PEFT(参数高效微调)、LoRA(低秩适配)、HuggingFace Trainer API

### `evaluate.py` — 模型评估

提供两种评估方式：`compute_perplexity()`计算困惑度（越低越好），`keyword_match_score()`计算预测与参考答案的关键词重叠F1分数。评估流程同时加载基础模型和微调模型进行对比，计算改进百分比。

- **关键函数**: `compute_perplexity()` — 困惑度计算, `keyword_match_score()` — 关键词匹配F1
- **核心模式**: 困惑度评估、Before/After对比、关键词F1

### `inference.py` — 推理与对比

提供推理和前后对比功能。`generate_response()`加载基础模型，如有LoRA权重则叠加，使用`### Instruction: ... ### Response:`格式生成回答。`compare_before_after()`并排展示基础模型和微调模型对同一问题的回答。

- **关键函数**: `generate_response()` — 单次推理, `compare_before_after()` — 对比展示
- **核心模式**: LoRA权重加载(`PeftModel.from_pretrained`)、生成参数调优(top_p, temperature)

---

## 运行示例 (Run Examples)

```bash
# 安装依赖
cd model-finetune-demo
pip install -r requirements.txt

# Step 1: 准备数据
python prepare_data.py
# 预期输出:
# ✅ Created dataset with 10 examples at data/instruction_data.json
# 📝 Sample entry: {"instruction": "Explain what machine learning is...", ...}

# Step 2: 微调（CPU约10分钟）
python train.py --epochs 3 --batch-size 2 --lr 2e-4
# 预期输出:
# 📦 Loading base model: facebook/opt-350m
# 🔧 LoRA configured: 1,234,567 trainable / 350,000,000 total (0.35%)
# 🚀 Starting fine-tuning...
# ✅ Model saved to ./output

# Step 3: 评估
python evaluate.py
# 预期输出:
# 📊 Evaluation Results:
#    Keyword Match F1: 0.245
# 📝 Sample predictions: ...

# Step 4: 前后对比
python inference.py --compare
# 预期输出:
# ============================================================
# 📝 Prompt: What is machine learning?
# 🔵 BASE MODEL: (通用回答)
# 🟢 FINE-TUNED MODEL: (更精确的领域回答)

# 自定义参数微调
python train.py --lora-rank 16 --epochs 5 --model facebook/opt-1.3b

# 使用自定义数据
python train.py --data data/your_data.json
```

---

## 知识映射 (Knowledge Mapping)

**本项目演示的知识点：**
- LoRA(低秩适配)微调原理与实现
- 指令微调(Instruction Tuning)数据格式
- HuggingFace Transformers + PEFT生态
- 训练超参数调优（学习率、batch size、rank）
- 模型评估方法（困惑度、关键词匹配）

**前置知识：**
- Python基础、PyTorch基础
- 神经网络基本概念（前向传播、反向传播）
- Transformer架构基础

**进阶方向：**
- 完成本项目后 → 用微调后的模型替换 `rag-qa-bot` 中的生成器
- 深入 → QLoRA(量化LoRA)、全参数微调、RLHF
- 生产化 → 分布式训练、模型合并与导出(GGUF)

**相关知识库文件：**
- `knowledge-base/07-training/` — 模型训练与微调
- `knowledge-base/08-peft/` — 参数高效微调(LoRA/QLoRA)
- `knowledge-base/01-llm-basics/` — Transformer架构

---

## 商业价值扩展 (Commercial Value Extensions)

**目标客户：**
- 垂直领域AI公司（法律、医疗、金融）
- 企业AI团队（定制内部助手）
- AI研究机构（快速实验）

**定价模型：**
- 微调平台SaaS: $0.10/千token训练 + $0.002/千token推理
- 企业定制微调: $10,000-$50,000/项目
- 模型市场: 微调好的垂直模型按订阅出售

**竞品对比：**

| 特性 | 本项目 | OpenAI Fine-tuning | Together.ai | Lamini |
|------|--------|-------------------|-------------|--------|
| 开源 | ✅ | ❌ | ❌ | 部分 |
| CPU运行 | ✅ | ❌ | ❌ | ❌ |
| LoRA支持 | ✅ | ❌ | ✅ | ✅ |
| 本地隐私 | ✅ | ❌ | ❌ | ✅ |
| 自定义架构 | ✅ | ❌ | ✅ | 部分 |

**市场进入策略：**
1. 开源微调工具链 → 社区积累 → 托管微调平台
2. 垂直行业模型市场（法律助手、医疗问答）
3. 企业数据私有化微调咨询服务

---

## 进阶挑战 (Advanced Challenges)

### 🟢 挑战1 (初级): 添加更多评估指标
在evaluate.py中添加BLEU分数和ROUGE-L分数评估，使用`nltk`和`rouge-score`库。
- **学习目标**: NLP自动评估指标
- **提示**: `from nltk.translate.bleu_score import sentence_bleu`

### 🟡 挑战2 (中级): 实现早停(Early Stopping)机制
当验证集loss连续N个epoch不再下降时自动停止训练，避免过拟合。
- **学习目标**: 训练策略优化、过拟合防止
- **提示: 在TrainingArguments中添加`load_best_model_at_end=True`和`evaluation_strategy`

### 🔴 挑战3 (高级): 实现QLoRA(量化LoRA)微调
将基础模型量化为4bit后再应用LoRA，大幅减少显存占用，使得在消费级GPU上微调更大模型。
- **学习目标**: 量化技术、QLoRA原理、显存优化
- **提示**: 使用`bitsandbytes`库的`BitsAndBytesConfig(load_in_4bit=True)`
