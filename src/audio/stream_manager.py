from typing import Callable, Optional
import numpy as np
import sounddevice as sd

from src.audio.buffer import AudioRingBuffer


class AudioStreamManager:
    """
    Manages low-latency real-time audio streams bridging hardware inputs
    to virtual output audio devices using sounddevice and PortAudio.
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        chunk_size: int = 320,
        virtual_mic_keyword: str = "BlackHole",
    ):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.virtual_mic_keyword = virtual_mic_keyword
        self.in_buffer = AudioRingBuffer(capacity=16000)
        self.out_buffer = AudioRingBuffer(capacity=16000)
        self.input_stream: Optional[sd.InputStream] = None
        self.output_stream: Optional[sd.OutputStream] = None
        self.is_running = False
        self.processing_callback: Optional[Callable[[np.ndarray], np.ndarray]] = None

    def find_device_index(self, name_keyword: str, is_input: bool = False) -> int:
        devices = sd.query_devices()
        for idx, dev in enumerate(devices):
            max_channels = (
                dev["max_input_channels"] if is_input else dev["max_output_channels"]
            )
            if name_keyword.lower() in dev["name"].lower() and max_channels > 0:
                return idx
        raise ValueError(f"Target audio device matching '{name_keyword}' not found.")

    def _input_callback(self, indata, frames, time_info, status):
        if status:
            print(f"Input Stream Warning: {status}")
        audio_data = indata[:, 0].astype(np.float32)
        self.in_buffer.write(audio_data)

    def _output_callback(self, outdata, frames, time_info, status):
        if status:
            print(f"Output Stream Warning: {status}")
        data = self.out_buffer.read(frames)
        outdata[:, 0] = data

    def start_streams(
        self, process_fn: Optional[Callable[[np.ndarray], np.ndarray]] = None
    ):
        self.processing_callback = process_fn
        out_idx = self.find_device_index(self.virtual_mic_keyword, is_input=False)

        self.input_stream = sd.InputStream(
            samplerate=self.sample_rate,
            blocksize=self.chunk_size,
            channels=1,
            dtype="float32",
            callback=self._input_callback,
        )
        self.output_stream = sd.OutputStream(
            device=out_idx,
            samplerate=self.sample_rate,
            blocksize=self.chunk_size,
            channels=1,
            dtype="float32",
            callback=self._output_callback,
        )

        self.input_stream.start()
        self.output_stream.start()
        self.is_running = True

    def process_loop_tick(self):
        if self.is_running and self.in_buffer.size >= self.chunk_size:
            raw_chunk = self.in_buffer.read(self.chunk_size)
            if self.processing_callback:
                processed_chunk = self.processing_callback(raw_chunk)
            else:
                processed_chunk = raw_chunk
            self.out_buffer.write(processed_chunk)

    def stop_streams(self):
        self.is_running = False
        if self.input_stream:
            self.input_stream.stop()
            self.input_stream.close()
        if self.output_stream:
            self.output_stream.stop()
            self.output_stream.close()
