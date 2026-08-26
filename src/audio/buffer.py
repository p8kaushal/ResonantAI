import threading
import numpy as np


class AudioRingBuffer:
    """
    Thread-safe circular ring buffer for real-time PCM audio streaming.
    Prevents overflow and falls back to zeros on underflow.
    """

    def __init__(self, capacity: int = 16000):
        self.capacity = capacity
        self.buffer = np.zeros(capacity, dtype=np.float32)
        self.head = 0
        self.tail = 0
        self.size = 0
        self.lock = threading.Lock()

    def write(self, data: np.ndarray) -> bool:
        with self.lock:
            num_samples = len(data)
            if num_samples > self.capacity - self.size:
                return False  # Buffer overflow prevention

            first_chunk = min(num_samples, self.capacity - self.head)
            self.buffer[self.head:self.head + first_chunk] = data[:first_chunk]

            second_chunk = num_samples - first_chunk
            if second_chunk > 0:
                self.buffer[0:second_chunk] = data[first_chunk:]

            self.head = (self.head + num_samples) % self.capacity
            self.size += num_samples
            return True

    def read(self, num_samples: int) -> np.ndarray:
        with self.lock:
            if num_samples > self.size:
                return np.zeros(num_samples, dtype=np.float32)  # Underflow fallback

            output = np.zeros(num_samples, dtype=np.float32)
            first_chunk = min(num_samples, self.capacity - self.tail)
            output[:first_chunk] = self.buffer[self.tail:self.tail + first_chunk]

            second_chunk = num_samples - first_chunk
            if second_chunk > 0:
                output[first_chunk:] = self.buffer[0:second_chunk]

            self.tail = (self.tail + num_samples) % self.capacity
            self.size -= num_samples
            return output
