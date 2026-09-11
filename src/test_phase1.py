import unittest
import numpy as np
import os

from src.audio.buffer import AudioRingBuffer
from src.audio.stream_manager import AudioStreamManager
from src.engine.onnx_runtime import ONNXInferenceEngine
from src.engine.timbre_encoder import SpeakerTimbreEncoder
from src.engine.vocoder import VocosNeuralVocoder
import src.dataset.augment as aug


class TestResonantAIPhase1(unittest.TestCase):

    def test_audio_ring_buffer(self):
        buf = AudioRingBuffer(capacity=1000)
        data = np.ones(500, dtype=np.float32) * 0.5
        self.assertTrue(buf.write(data))
        self.assertEqual(buf.size, 500)
        read_data = buf.read(500)
        self.assertEqual(len(read_data), 500)
        self.assertAlmostEqual(float(read_data[0]), 0.5)
        self.assertEqual(buf.size, 0)

    def test_onnx_int8_inference(self):
        model_path = "models/exported/normalizer_int8.onnx"
        self.assertTrue(os.path.exists(model_path), "INT8 ONNX model missing")
        engine = ONNXInferenceEngine(model_path, provider="CPU")
        dummy_mel = np.random.randn(1, 20, 80).astype(np.float32)
        out = engine.infer_spectrogram_frame(dummy_mel)
        self.assertEqual(out.shape, (1, 20, 80))

    def test_timbre_encoder_and_vocoder(self):
        encoder = SpeakerTimbreEncoder(embedding_dim=256)
        dummy_pcm = np.random.randn(16000).astype(np.float32)
        embedding = encoder.extract_embedding_from_pcm(dummy_pcm)
        self.assertEqual(len(embedding), 256)
        self.assertAlmostEqual(float(np.linalg.norm(embedding)), 1.0, places=5)

        vocoder = VocosNeuralVocoder(sample_rate=16000)
        dummy_mel = np.random.randn(1, 20, 80).astype(np.float32)
        waveform = vocoder.decode_spectrogram_to_wave(dummy_mel, embedding)
        self.assertEqual(len(waveform), 3200)

    def test_dataset_augmentation(self):
        sample = np.sin(np.linspace(0, 10, 16000)).astype(np.float32)
        speed = aug.speed_scale(sample, 1.1)
        pitch = aug.pitch_shift(sample, 2.0)
        noise = aug.inject_noise(sample, 0.01)
        self.assertTrue(len(speed) > 0)
        self.assertEqual(len(pitch), 16000)
        self.assertEqual(len(noise), 16000)

    def test_stream_manager_device_discovery(self):
        mgr = AudioStreamManager(virtual_mic_keyword="MacBook")
        idx = mgr.find_device_index("MacBook", is_input=True)
        self.assertGreaterEqual(idx, 0)


if __name__ == "__main__":
    unittest.main()
