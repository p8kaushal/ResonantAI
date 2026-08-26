"""
ResonantAI Acoustic Normalizer & ONNX Quantization Module
=========================================================

Defines the Conformer-based Mel-spectrogram normalizer architecture and handles
exporting to standard FP32 ONNX graph representations with dynamic time axes,
as well as dynamic INT8 quantization for low-latency on-device speech inference.
"""

import os
import time
import inspect
from pathlib import Path
from typing import Optional, Tuple

import torch
import torch.nn as nn
import numpy as np
import onnx
import onnxruntime as ort
from onnxruntime.quantization import quantize_dynamic, QuantType


class DummyConformerNormalizer(nn.Module):
    """
    Lightweight Conformer-style feature normalizer module for dysarthric acoustic features.

    Processes 80-channel log-mel filterbank energies across variable time steps,
    applying 1D temporal convolution, GRU temporal modeling, and linear projection
    back to normalized 80-channel feature space.
    """

    def __init__(self, in_features: int = 80, hidden_dim: int = 128, out_features: int = 80):
        super().__init__()
        self.conv = nn.Conv1d(in_features, hidden_dim, kernel_size=3, padding=1)
        self.gru = nn.GRU(hidden_dim, hidden_dim, batch_first=True)
        self.fc = nn.Linear(hidden_dim, out_features)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass for acoustic feature normalization.

        Args:
            x (torch.Tensor): Input mel-spectrogram of shape (batch_size, time_steps, 80).

        Returns:
            torch.Tensor: Normalized mel-spectrogram of shape (batch_size, time_steps, 80).
        """
        # x shape: (batch_size, time_steps, 80)
        x_t = x.transpose(1, 2)
        c = torch.relu(self.conv(x_t)).transpose(1, 2)
        g, _ = self.gru(c)
        out = self.fc(g)
        return out


def export_normalizer_fp32(
    output_fp32_path: str = "models/exported/normalizer_fp32.onnx",
    model: Optional[nn.Module] = None
) -> str:
    """
    Exports the DummyConformerNormalizer PyTorch model to ONNX FP32 format at the given path.

    Parameters:
      - opset_version: 17
      - Dynamic axes for time dimension (axis 1): {'input_mel': {1: 'time_steps'}, 'normalized_mel': {1: 'time_steps'}}
      - Input name: 'input_mel'
      - Output name: 'normalized_mel'

    Args:
        output_fp32_path (str): File destination path for the exported .onnx model.
        model (Optional[nn.Module]): Optional initialized model instance.

    Returns:
        str: Resolved string path to the exported ONNX FP32 model.
    """
    output_path = Path(output_fp32_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if model is None:
        model = DummyConformerNormalizer()

    model.eval()

    # Dummy tensor for tracing execution graph (batch=1, time_steps=20, n_mels=80)
    dummy_input = torch.randn(1, 20, 80, dtype=torch.float32)

    export_kwargs = {
        "export_params": True,
        "opset_version": 17,
        "do_constant_folding": True,
        "input_names": ["input_mel"],
        "output_names": ["normalized_mel"],
        "dynamic_axes": {
            "input_mel": {1: "time_steps"},
            "normalized_mel": {1: "time_steps"}
        }
    }

    # Ensure compatibility across PyTorch versions
    if "dynamo" in inspect.signature(torch.onnx.export).parameters:
        export_kwargs["dynamo"] = False

    torch.onnx.export(
        model,
        dummy_input,
        str(output_path),
        **export_kwargs
    )

    print(f"FP32 Model successfully exported to: {output_path}")
    return str(output_path)


def quantize_normalizer_to_int8(
    output_fp32_path: str = "models/exported/normalizer_fp32.onnx",
    output_int8_path: str = "models/exported/normalizer_int8.onnx"
) -> str:
    """
    Applies dynamic INT8 quantization to an existing FP32 ONNX model.

    Args:
        output_fp32_path (str): Source FP32 ONNX model path.
        output_int8_path (str): Destination INT8 ONNX model path.

    Returns:
        str: Resolved string path to the quantized INT8 ONNX model.
    """
    src_path = Path(output_fp32_path).resolve()
    dst_path = Path(output_int8_path).resolve()
    dst_path.parent.mkdir(parents=True, exist_ok=True)

    if not src_path.exists():
        raise FileNotFoundError(f"Source FP32 model not found at {src_path}")

    quantize_dynamic(
        model_input=str(src_path),
        model_output=str(dst_path),
        weight_type=QuantType.QUInt8
    )

    print(f"INT8 Quantized Model successfully generated at: {dst_path}")
    return str(dst_path)


def export_and_quantize_normalizer(
    output_fp32_path: str = "models/exported/normalizer_fp32.onnx",
    output_int8_path: str = "models/exported/normalizer_int8.onnx",
    model: Optional[nn.Module] = None
) -> Tuple[str, str]:
    """
    Executes full pipeline: exports the model to FP32 ONNX first, and then
    applies dynamic INT8 quantization to produce the quantized ONNX graph.

    Args:
        output_fp32_path (str): Output path for the FP32 ONNX model.
        output_int8_path (str): Output path for the INT8 ONNX model.
        model (Optional[nn.Module]): PyTorch model instance to export.

    Returns:
        Tuple[str, str]: (path_to_fp32_onnx, path_to_int8_onnx)
    """
    fp32_path = export_normalizer_fp32(output_fp32_path, model=model)
    int8_path = quantize_normalizer_to_int8(fp32_path, output_int8_path)
    return fp32_path, int8_path


if __name__ == "__main__":
    print("=" * 70)
    print("ResonantAI Conformer Normalizer - Step 6: INT8 Dynamic Quantization & Benchmark")
    print("=" * 70)

    # 1. Run full export and dynamic quantization pipeline
    fp32_path, int8_path = export_and_quantize_normalizer(
        output_fp32_path="models/exported/normalizer_fp32.onnx",
        output_int8_path="models/exported/normalizer_int8.onnx"
    )

    # 2. File size comparison and verification
    assert os.path.exists(int8_path), f"INT8 model not found at {int8_path}"
    assert os.path.exists(fp32_path), f"FP32 model not found at {fp32_path}"

    fp32_size_bytes = os.path.getsize(fp32_path)
    int8_size_bytes = os.path.getsize(int8_path)
    fp32_size_kb = fp32_size_bytes / 1024.0
    int8_size_kb = int8_size_bytes / 1024.0
    reduction_pct = ((fp32_size_bytes - int8_size_bytes) / fp32_size_bytes) * 100.0

    print("-" * 70)
    print("MODEL FILE SIZE COMPARISON:")
    print(f"  FP32 ONNX Model : {fp32_size_bytes:,} bytes ({fp32_size_kb:.2f} KB)")
    print(f"  INT8 ONNX Model : {int8_size_bytes:,} bytes ({int8_size_kb:.2f} KB)")
    print(f"  Size Reduction  : {reduction_pct:.2f}% reduction ({fp32_size_kb - int8_size_kb:.2f} KB saved)")
    print("-" * 70)

    assert int8_size_bytes < fp32_size_bytes, "Quantized INT8 model is not smaller than FP32 model!"

    # 3. Load INT8 model into ONNX Runtime InferenceSession
    session_options = ort.SessionOptions()
    session_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    session_int8 = ort.InferenceSession(int8_path, session_options, providers=["CPUExecutionProvider"])
    print(f"[PASS] Loaded INT8 model in ONNX Runtime with providers: {session_int8.get_providers()}")

    # 4. Generate dummy float32 NumPy array of shape (1, 20, 80) representing 20 frames of 80-mel bands
    dummy_input_np = np.random.randn(1, 20, 80).astype(np.float32)

    # Warmup runs (10 iterations)
    for _ in range(10):
        _ = session_int8.run(["normalized_mel"], {"input_mel": dummy_input_np})

    # 5. Measure inference latency over 100 benchmark runs
    num_runs = 100
    start_time = time.perf_counter()
    for _ in range(num_runs):
        outputs = session_int8.run(["normalized_mel"], {"input_mel": dummy_input_np})
    end_time = time.perf_counter()

    total_latency_ms = (end_time - start_time) * 1000.0
    avg_latency_ms = total_latency_ms / float(num_runs)
    output_tensor = outputs[0]

    print("-" * 70)
    print("INFERENCE LATENCY BENCHMARK (100 runs on CPU):")
    print(f"  Input Tensor Shape  : {dummy_input_np.shape} (20 frames x 80 mel bins)")
    print(f"  Output Tensor Shape : {output_tensor.shape} (dtype: {output_tensor.dtype})")
    print(f"  Total Duration      : {total_latency_ms:.2f} ms for {num_runs} inferences")
    print(f"  Average Latency     : {avg_latency_ms:.4f} ms / run")
    print("-" * 70)

    assert output_tensor.shape == (1, 20, 80), f"Expected shape (1, 20, 80), got {output_tensor.shape}"
    assert output_tensor.dtype == np.float32, f"Expected float32, got {output_tensor.dtype}"
    assert np.all(np.isfinite(output_tensor)), "Output contains NaN or Inf values"

    print("[SUCCESS] Dynamic INT8 Quantization and Performance Benchmark verified successfully!")
    print("=" * 70)
