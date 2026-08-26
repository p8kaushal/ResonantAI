"""
ResonantAI Acoustic Normalizer & ONNX Quantization Module
=========================================================

Defines the Conformer-based Mel-spectrogram normalizer architecture and handles
exporting to standard FP32 ONNX graph representations with dynamic time axes,
as well as dynamic INT8 quantization for low-latency on-device speech inference.
"""

import os
import inspect
from pathlib import Path
from typing import Optional

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
    output_fp32_path: str,
    output_int8_path: str
) -> str:
    """
    Dynamic quantization function stub to convert FP32 ONNX model to INT8 representation.

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


if __name__ == "__main__":
    print("=" * 70)
    print("ResonantAI Conformer Normalizer - Step 5 Verification")
    print("=" * 70)

    # 1. Export FP32 ONNX Model
    model_path = "models/exported/normalizer_fp32.onnx"
    exported_file = export_normalizer_fp32(model_path)

    # 2. Load the exported normalizer_fp32.onnx using onnxruntime.InferenceSession
    session = ort.InferenceSession(exported_file, providers=["CPUExecutionProvider"])

    # 3. Generate a dummy float32 NumPy array of shape (1, 20, 80)
    dummy_input_np = np.random.randn(1, 20, 80).astype(np.float32)

    # 4. Perform inference
    outputs = session.run(["normalized_mel"], {"input_mel": dummy_input_np})
    output_mel = outputs[0]

    # 5. Print output shape and validation confirmation
    print("-" * 70)
    print(f"Input Shape : {dummy_input_np.shape} (dtype: {dummy_input_np.dtype})")
    print(f"Output Shape: {output_mel.shape} (dtype: {output_mel.dtype})")
    print("-" * 70)

    assert output_mel.shape == (1, 20, 80), f"Expected (1, 20, 80), got {output_mel.shape}"
    assert output_mel.dtype == np.float32, f"Expected float32, got {output_mel.dtype}"
    assert np.all(np.isfinite(output_mel)), "Output contains non-finite values"

    print("[SUCCESS] Validation confirmed: Normalizer FP32 ONNX model successfully exported and verified via ONNX Runtime inference session.")
    print("=" * 70)
