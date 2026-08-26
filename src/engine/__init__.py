"""
ResonantAI Engine Module
Acoustic feature normalization, quantization, and ONNX Runtime inference engine.
"""

from .quantizer import (
    DummyConformerNormalizer,
    export_normalizer_fp32,
    quantize_normalizer_to_int8,
    export_and_quantize_normalizer,
)
from .onnx_runtime import ONNXInferenceEngine
from .timbre_encoder import SpeakerTimbreEncoder
from .vocoder import VocosNeuralVocoder

__all__ = [
    "DummyConformerNormalizer",
    "export_normalizer_fp32",
    "quantize_normalizer_to_int8",
    "export_and_quantize_normalizer",
    "ONNXInferenceEngine",
    "SpeakerTimbreEncoder",
    "VocosNeuralVocoder",
]
