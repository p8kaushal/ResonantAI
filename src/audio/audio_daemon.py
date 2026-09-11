import sys
import os
import json
import time
import math
import threading

# Ensure project root is in sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Force line buffering for unbuffered stdout emission
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(line_buffering=True)

import numpy as np
from src.audio.stream_manager import AudioStreamManager


class AudioStreamingDaemon:
    def __init__(self):
        self.stream_mgr = AudioStreamManager()
        self.engine_active = True
        self.input_index = None
        self.output_index = None
        self.latency_ms = 28
        self.smoothed_level = 0.0
        self.noise_floor_db = -55.0
        self.speech_peak_db = -25.0
        self.is_running = True
        self.lock = threading.Lock()

    def process_audio(self, chunk: np.ndarray) -> np.ndarray:
        if not self.engine_active:
            return chunk

        # Apply 3.2x software gain boost with clipping protection
        boosted = chunk * 3.2
        return np.clip(boosted, -1.0, 1.0)

    def stdin_listener(self):
        while self.is_running:
            try:
                line = sys.stdin.readline()
                if not line:
                    break
                data = json.loads(line.strip())
                cmd = data.get("command")
                if cmd == "init_stream":
                    with self.lock:
                        self.input_index = data.get("input", 0)
                        self.output_index = data.get("output", 1)
                        ms = data.get("ms", 28)
                        self.latency_ms = ms
                        new_chunk = int(16000 * (ms / 1000.0))
                        self.stream_mgr.chunk_size = max(160, min(1600, new_chunk))
                        self._restart_streams()
                        print(json.dumps({"type": "latency_ack", "ms": ms}), flush=True)
                elif cmd == "set_devices":
                    with self.lock:
                        self.input_index = data.get("input")
                        self.output_index = data.get("output")
                        self.noise_floor_db = -55.0
                        self.speech_peak_db = -25.0
                        self._restart_streams()
                elif cmd == "toggle_engine":
                    with self.lock:
                        self.engine_active = data.get("active", True)
                elif cmd == "set_latency":
                    with self.lock:
                        ms = data.get("ms", 28)
                        self.latency_ms = ms
                        # Calculate dynamic chunk size based on latency budget
                        new_chunk = int(16000 * (ms / 1000.0))
                        self.stream_mgr.chunk_size = max(160, min(1600, new_chunk))
                        self._restart_streams()
                        print(json.dumps({"type": "latency_ack", "ms": ms}), flush=True)
            except Exception as e:
                pass

    def _restart_streams(self):
        try:
            self.stream_mgr.stop_streams()
        except Exception:
            pass
        try:
            self.stream_mgr.start_streams(
                process_fn=self.process_audio,
                input_device_index=self.input_index,
                output_device_index=self.output_index,
            )
        except Exception as e:
            sys.stderr.write(f"Stream restart error: {e}\n")

    def run(self):
        # Start stdin listener thread
        listener_thread = threading.Thread(target=self.stdin_listener, daemon=True)
        listener_thread.start()

        # Start audio streams
        self._restart_streams()

        last_level_time = time.time()
        while self.is_running:
            try:
                self.stream_mgr.process_loop_tick()
                now = time.time()
                if now - last_level_time >= 0.08:
                    last_level_time = now
                    
                    if self.stream_mgr.in_buffer.size > 0:
                        samples = self.stream_mgr.in_buffer.buffer[: self.stream_mgr.in_buffer.size]
                        rms = float(np.sqrt(np.mean(samples ** 2))) if len(samples) > 0 else 0

                        if rms > 0.001:
                            db = 20.0 * math.log10(rms / 32768.0) if np.issubdtype(samples.dtype, np.integer) or np.max(np.abs(samples)) > 1.0 else 20.0 * math.log10(rms)
                        else:
                            db = -100.0

                        # Fixed dB bounds tuned for macOS microphone inputs
                        min_db = -52.0  # Floor: Silence / ambient room noise maps to 0%
                        max_db = -8.0   # Ceiling: Loud speech maps to 100%

                        if db <= min_db:
                            pct = 0
                        else:
                            norm = min(1.0, (db - min_db) / (max_db - min_db))
                            # Power expansion (0.65) to expand speech dynamic range into 65-90%
                            pct = int((norm ** 0.65) * 100.0)
                    else:
                        pct = 0

                    self.smoothed_level = int(0.3 * self.smoothed_level + 0.7 * pct)
                    print(json.dumps({"type": "level", "val": self.smoothed_level}), flush=True)

                time.sleep(0.01)
            except KeyboardInterrupt:
                break
            except Exception:
                time.sleep(0.02)

        self.stream_mgr.stop_streams()


if __name__ == "__main__":
    daemon = AudioStreamingDaemon()
    daemon.run()
