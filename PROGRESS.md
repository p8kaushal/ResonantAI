# 📈 Project Progress Roadmap

## Phase 1: Base Version (Eureka! 2026 Competition & POC Release)
- [x] Step 1: Environment & Security Setup (.gitignore, .env.example, directory structure) — verified 2026-08-26
- [x] Step 2: System audio dependencies installation (portaudio, sounddevice, BlackHole / VB-Cable) — verified 2026-08-26
- [x] Step 3: Supabase DDL migration (tables, indexes, RLS policies) — verified 2026-08-26
- [x] Step 4: Dataset download & Torgo/UA-Speech augmentation — verified 2026-08-26
- [x] Step 5: Train Conformer Acoustic Normalizer & export to ONNX — verified 2026-08-26
- [x] Step 6: Apply static INT8 quantization to Normalizer — verified 2026-08-26
- [x] Step 7: Build thread-safe AudioRingBuffer & AudioStreamManager — verified 2026-08-26
- [x] Step 8: Implement ONNX Runtime execution engine — verified 2026-08-26
- [x] Step 9: Integrate Vocos neural vocoder & SpeakerTimbreEncoder — verified 2026-08-26
- [x] Step 10: Build Electron + React system tray UI control center (100% complete — device routing & level metering verified) — verified 2026-08-26
- [x] Step 10.2: Backend PyAudio Device Enumeration & Direct Speaker Routing (`src/audio/stream_manager.py`) — verified 2026-08-26
- [x] Step 10.3: React UI Audio Device Dropdowns & Live Level Visualizer (`src/ui/App.tsx`, export mismatch fixed & bundle verified) — verified 2026-08-26
- [x] Step 10.4: End-to-End Live Audio Daemon & Virtual Call Driver Verification (automatic startup audio stream initialization & sys.path import resolution verified) — verified 2026-08-26
- [ ] Step 10.5: Real-Time ONNX Inference Integration & Ring Buffer Pipeline
  - [ ] 10.5a: Offline verification script (`scripts/test_onnx_offline.py`) and dysarthric audio restoration validation.
  - [ ] 10.5b: Polyphase sample-rate conversion ($44.1\text{ kHz} / 48\text{ kHz} \leftrightarrow 16\text{ kHz}$).
  - [ ] 10.5c: 160 ms sliding ring buffer implementation in `src/audio/audio_daemon.py`.
  - [ ] 10.5d: Overlap-add (OLA) Hanning window synthesis smoothing.
  - [ ] 10.5e: ONNX Conformer/Vocos CPU execution timeout fallback.
- [ ] Step 11: Launch GoDaddy Airo pitch landing page & comparison widget

## Phase 2: Enhancements & Enterprise Scaling
- [ ] Step 12: macOS native DriverKit and Windows WASAPI kernel loopback drivers
- [ ] Step 13: Non-invasive sEMG neck sensor interface
- [ ] Step 14: Federated Learning framework integration
- [ ] Step 15: File provisional patents
- [ ] Step 16: DPIIT Startup Recognition & FDA DME documentation
- [ ] Step 17: Enterprise B2B sales motion setup
