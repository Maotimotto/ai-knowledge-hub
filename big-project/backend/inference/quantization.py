"""
AI创作工坊 - Model Quantization Utilities

Tools for quantizing models (GGUF, GPTQ) and downloading from HuggingFace.
Reduces memory footprint and improves inference speed.
"""

import os
import subprocess
from pathlib import Path
from typing import Any, Optional

from observability.logger import get_logger

logger = get_logger(__name__)


def download_from_huggingface(
    repo_id: str,
    local_dir: str = "./models",
    filename: Optional[str] = None,
    revision: Optional[str] = None,
) -> str:
    """
    Download a model from HuggingFace Hub.

    Args:
        repo_id: HuggingFace repo ID (e.g., "meta-llama/Llama-3-8B")
        local_dir: Local directory to save to
        filename: Specific file to download (for GGUF files)
        revision: Git revision (branch/tag/commit)

    Returns:
        Path to downloaded model
    """
    from huggingface_hub import hf_hub_download, snapshot_download

    os.makedirs(local_dir, exist_ok=True)

    if filename:
        path = hf_hub_download(
            repo_id=repo_id, filename=filename,
            local_dir=local_dir, revision=revision,
        )
        logger.info(f"Downloaded {repo_id}/{filename} → {path}")
    else:
        path = snapshot_download(
            repo_id=repo_id, local_dir=os.path.join(local_dir, repo_id.split("/")[-1]),
            revision=revision,
        )
        logger.info(f"Downloaded {repo_id} → {path}")

    return path


def quantize_gguf(
    model_path: str,
    output_path: str,
    quant_method: str = "Q4_K_M",
) -> str:
    """
    Quantize a model to GGUF format using llama.cpp's convert script.

    Args:
        model_path: Path to HuggingFace model directory
        output_path: Output path for quantized model
        quant_method: Quantization level (Q4_0, Q4_K_M, Q5_K_M, Q8_0)

    Returns:
        Path to quantized GGUF file
    """
    llama_cpp_dir = os.environ.get("LLAMA_CPP_PATH", "./llama.cpp")

    # Step 1: Convert to GGUF F16
    f16_path = output_path.replace(".gguf", "-f16.gguf")
    convert_script = os.path.join(llama_cpp_dir, "convert_hf_to_gguf.py")

    cmd_convert = ["python3", convert_script, model_path, "--outfile", f16_path, "--outtype", "f16"]
    logger.info(f"Converting to GGUF F16: {' '.join(cmd_convert)}")
    subprocess.run(cmd_convert, check=True, capture_output=True, text=True)

    # Step 2: Quantize
    quantize_bin = os.path.join(llama_cpp_dir, "build", "bin", "llama-quantize")
    cmd_quant = [quantize_bin, f16_path, output_path, quant_method]
    logger.info(f"Quantizing to {quant_method}: {' '.join(cmd_quant)}")
    subprocess.run(cmd_quant, check=True, capture_output=True, text=True)

    # Cleanup intermediate file
    os.remove(f16_path)

    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    logger.info(f"Quantized model saved: {output_path} ({size_mb:.0f} MB, {quant_method})")
    return output_path


def quantize_gptq(
    model_path: str,
    output_path: str,
    bits: int = 4,
    dataset: str = "c4",
    group_size: int = 128,
) -> str:
    """
    Quantize a model using GPTQ (post-training quantization).

    Args:
        model_path: Path to HuggingFace model
        output_path: Output directory for quantized model
        bits: Quantization bits (2, 3, 4, 8)
        dataset: Calibration dataset name
        group_size: Group size for quantization

    Returns:
        Path to quantized model
    """
    from auto_gptq import AutoGPTQForCausalLM, BaseQuantizeConfig
    from transformers import AutoTokenizer

    quantize_config = BaseQuantizeConfig(
        bits=bits, group_size=group_size, damp_percent=0.01,
    )

    logger.info(f"Loading model for GPTQ quantization: {model_path}")
    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    model = AutoGPTQForCausalLM.from_pretrained(model_path, quantize_config)

    # Use a small calibration sample
    calibration_data = [
        tokenizer("This is a calibration sample for GPTQ quantization.", return_tensors="pt")
        for _ in range(4)
    ]

    logger.info(f"Quantizing to {bits}-bit GPTQ...")
    model.quantize(calibration_data)
    model.save_quantized(output_path)
    tokenizer.save_pretrained(output_path)

    logger.info(f"GPTQ model saved: {output_path} ({bits}-bit, group_size={group_size})")
    return output_path
