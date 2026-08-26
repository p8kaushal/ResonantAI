"""
ResonantAI ONNX Runtime Inference Engine
========================================

Hardware-accelerated execution engine for low-latency acoustic normalization
and feature transformation using onnxruntime with automatic execution provider
fallback (CoreML on Apple Silicon/macOS, DirectML on Windows, CUDA on Linux/NVIDIA,
and fallback CPUExecutionProvider).
"""

import os
import sys
import time
from pathlib import Path
from typing import List, Optional, Union

import numpy as np
import onnxruntime as ort

# Ensure project root is on sys.path for standalone script execution
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


class ONNXInferenceEngine:
    """
    High-performance ONNX Runtime inference wrapper with dynamic platform provider negotiation.
    """

    def __init__(self, model_path: Union[str, Path], provider: str = "CoreML"):
        """
        Initializes an ONNX inference session with preferred hardware acceleration
        and CPU fallback.

        Args:
            model_path: Path to the .onnx model file (FP32 or INT8 quantized).
            provider: Preferred hardware acceleration provider ('CoreML', 'DirectML', 'CUDA', or 'CPU').

        Raises:
            FileNotFoundError: If model_path does not exist on disk.
        """
        self.model_path = Path(model_path).resolve()
        if not self.model_path.exists():
            raise FileNotFoundError(f"ONNX Model not found at {self.model_path}")

        available_providers = ort.get_available_providers()
        selected_providers: List[str] = []

        if provider == "CoreML" and "CoreMLExecutionProvider" in available_providers:
            selected_providers.append("CoreMLExecutionProvider")
        elif provider == "DirectML" and "DmlExecutionProvider" in available_providers:
            selected_providers.append("DmlExecutionProvider")
        elif provider == "CUDA" and "CUDAExecutionProvider" in available_providers:
            selected_providers.append("CUDAExecutionProvider")

        # Always include CPU execution provider as a universal fallback
        if "CPUExecutionProvider" not in selected_providers:
            selected_providers.append("CPUExecutionProvider")

        # Configure session options for optimal performance
        session_options = ort.SessionOptions()
        session_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

        self.session = ort.InferenceSession(
            str(self.model_path),
            sess_options=session_options,
            providers=selected_providers
        )

        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name
        self.active_providers = self.session.get_providers()

        print(f"ONNX Session Active with Providers: {self.active_providers}")

    def infer_spectrogram_frame(self, mel_frame: np.ndarray) -> np.ndarray:
        """
        Executes real-time inference on an incoming log-mel spectrogram frame or sequence.

        Args:
            mel_frame (np.ndarray): Mel-spectrogram array of shape:
                - 2D: (time_steps, 80)
                - 3D: (batch_size, time_steps, 80)
                - 1D: (80,) - representing a single frame of 80 mel bins.

        Returns:
            np.ndarray: Normalized mel-spectrogram tensor of shape (batch_size, time_steps, 80).
        """
        frame = np.asarray(mel_frame, dtype=np.float32)

        if frame.ndim == 1:
            # Shape (80,) -> (1, 1, 80)
            frame = np.expand_dims(np.expand_dims(frame, axis=0), axis=0)
        elif frame.ndim == 2:
            # Shape (time_steps, 80) -> (1, time_steps, 80)
            frame = np.expand_dims(frame, axis=0)

        inputs = {self.input_name: frame}
        outputs = self.session.run([self.output_name], inputs)
        return outputs[0]


if __name__ == "__main__":
    print("=" * 70)
    print("ResonantAI ONNX Runtime Inference Engine - Step 8 Verification")
    print("=" * 70)

    # 1. Resolve model path (prefer INT8 quantized model, fallback to FP32)
    int8_model_path = Path("models/exported/normalizer_int8.onnx")
    fp32_model_path = Path("models/exported/normalizer_fp32.onnx")

    if int8_model_path.exists():
        target_model = int8_model_path
        print(f"Loading INT8 model: {target_model.resolve()}")
    elif fp32_model_path.exists():
        target_model = fp32_model_path
        print(f"Loading FP32 fallback model: {target_model.resolve()}")
    else:
        # Generate model if missing
        from src.engine.quantizer import export_and_quantize_normalizer
        _, int8_p = export_and_quantize_normalizer()
        target_model = Path(int8_p)
        print(f"Generated model: {target_model.resolve()}")

    # 2. Instantiate ONNXInferenceEngine with CoreML provider
    engine = ONNXInferenceEngine(target_model, provider="CoreML")

    # 3. Create dummy test frame (1, 20, 80)
    dummy_frame_3d = np.random.randn(1, 20, 80).astype(np.float32)
    dummy_frame_2d = np.random.randn(20, 80).astype(np.float32)

    # 4. Perform inference and verify output shapes
    output_3d = engine.infer_spectrogram_frame(dummy_frame_3d)
    output_2d = engine.infer_spectrogram_frame(dummy_frame_2d)

    print("-" * 70)
    print("INFERENCE VERIFICATION:")
    print(f"  3D Input Shape  : {dummy_frame_3d.shape} -> Output Shape: {output_3d.shape} (dtype: {output_3d.dtype})")
    print(f"  2D Input Shape  : {dummy_frame_2d.shape} -> Output Shape: {output_2d.shape} (dtype: {output_2d.dtype})")

    assert output_3d.shape == (1, 20, 80), f"Expected (1, 20, 80), got {output_3d.shape}"
    assert output_2d.shape == (1, 20, 80), f"Expected (1, 20, 80), got {output_2d.shape}"
    assert np.all(np.isfinite(output_3d)), "Output 3D contains non-finite values"
    assert np.all(np.isfinite(output_2d)), "Output 2D contains non-finite values"

    # Latency benchmark (50 runs)
    start_t = time.perf_counter()
    for _ in range(50):
        _ = engine.infer_spectrogram_frame(dummy_frame_3d)
    elapsed_ms = (time.perf_counter() - start_t) * 1000.0 / 50.0

    print(f"  Avg Frame Latency: {elapsed_ms:.4f} ms / frame (over 50 iterations)")
    print("-" * 70)
    print("[SUCCESS] Validation confirmed: ONNX Runtime execution engine successfully initialized and verified.")
    print("=" * 70)
