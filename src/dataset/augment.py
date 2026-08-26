"""
ResonantAI Audio Preprocessing & Data Augmentation Module

Provides synthetic speech perturbation routines (speed scaling, pitch shifting,
and noise injection) designed specifically for training robust acoustic models
and calibrating speech recognition pipelines for dysarthric speech patterns.
"""

from typing import Optional, Tuple
import numpy as np


def speed_scale(audio: np.ndarray, rate: float) -> np.ndarray:
    """
    Changes the playback speed / duration of the audio signal by a factor `rate`
    using linear interpolation (np.interp).

    A rate > 1.0 increases speed (shortens duration), while a rate < 1.0
    decreases speed (elongates duration). Typically used in the range [0.7, 1.3]
    to simulate variation in dysarthric speaking rate and syllable elongation.

    Args:
        audio (np.ndarray): 1D float32 or float64 audio time series, normalized to [-1.0, 1.0].
        rate (float): Speed scaling multiplier (e.g., 0.7 for 70% speed, 1.3 for 130% speed).

    Returns:
        np.ndarray: Speed-scaled 1D array of dtype float32 with values bounded in [-1.0, 1.0].

    Raises:
        ValueError: If rate is less than or equal to 0.
    """
    if rate <= 0:
        raise ValueError(f"Speed scaling rate must be strictly positive (>0), got {rate}")

    if audio is None or len(audio) == 0:
        return np.empty(0, dtype=np.float32)

    audio_flat = np.asarray(audio, dtype=np.float32).ravel()
    orig_len = len(audio_flat)

    if orig_len == 1 or rate == 1.0:
        return np.clip(audio_flat, -1.0, 1.0).astype(np.float32)

    # Compute target length based on speed rate
    new_len = max(1, int(round(orig_len / float(rate))))

    orig_indices = np.arange(orig_len, dtype=np.float64)
    new_indices = np.linspace(0.0, float(orig_len - 1), new_len, dtype=np.float64)

    scaled_audio = np.interp(new_indices, orig_indices, audio_flat)
    return np.clip(scaled_audio, -1.0, 1.0).astype(np.float32)


def pitch_shift(
    audio: np.ndarray,
    semitones: float,
    sample_rate: int = 16000
) -> np.ndarray:
    """
    Synthetically shifts the pitch of the audio signal by `semitones` while restoring
    the original sample length.

    Implements synthetic pitch adjustment by resampling the audio (using linear
    interpolation) by a frequency factor 2^(semitones/12), followed by duration
    restoration (padding with silence when pitch is shifted up, or truncating when
    pitch is shifted down) or windowing to preserve the fixed temporal length.

    Args:
        audio (np.ndarray): 1D audio time series, float32, normalized to [-1.0, 1.0].
        semitones (float): Number of semitones to shift (positive for higher pitch,
                           negative for lower pitch; typical range [-4.0, +4.0]).
        sample_rate (int): Sampling rate of the audio in Hz (default: 16000).

    Returns:
        np.ndarray: Pitch-shifted 1D array of dtype float32 of identical length to input,
                    with values bounded in [-1.0, 1.0].
    """
    if audio is None or len(audio) == 0:
        return np.empty(0, dtype=np.float32)

    audio_flat = np.asarray(audio, dtype=np.float32).ravel()
    orig_len = len(audio_flat)

    if semitones == 0.0 or orig_len <= 1:
        return np.clip(audio_flat, -1.0, 1.0).astype(np.float32)

    # Frequency shift factor: 2^(semitones / 12)
    factor = float(2.0 ** (semitones / 12.0))

    # Resample audio using interpolation:
    # Scaling speed by factor shifts frequencies by factor
    resampled = speed_scale(audio_flat, factor)
    resampled_len = len(resampled)

    # Restore original length
    if resampled_len == orig_len:
        out = resampled
    elif resampled_len < orig_len:
        # Pitch shifted up -> resampled is shorter; pad with zeros (silence)
        out = np.zeros(orig_len, dtype=np.float32)
        out[:resampled_len] = resampled
    else:
        # Pitch shifted down -> resampled is longer; truncate to original length
        out = resampled[:orig_len]

    return np.clip(out, -1.0, 1.0).astype(np.float32)


def inject_noise(
    audio: np.ndarray,
    snr_db: float = 20.0,
    noise: Optional[np.ndarray] = None
) -> np.ndarray:
    """
    Injects additive white Gaussian noise (or custom ambient background noise)
    into the audio signal at a specified Signal-to-Noise Ratio (SNR in dB).

    Args:
        audio (np.ndarray): 1D audio time series, float32, normalized to [-1.0, 1.0].
        snr_db (float): Target Signal-to-Noise Ratio in dB (e.g. 10.0 to 30.0 dB).
        noise (Optional[np.ndarray]): Optional custom noise waveform. If None,
                                     Gaussian noise is synthesized.

    Returns:
        np.ndarray: Noise-injected 1D array of dtype float32 clipped to [-1.0, 1.0].
    """
    if audio is None or len(audio) == 0:
        return np.empty(0, dtype=np.float32)

    audio_flat = np.asarray(audio, dtype=np.float32).ravel()
    sig_power = float(np.mean(audio_flat ** 2))

    if sig_power <= 1e-12:
        return audio_flat.astype(np.float32)

    target_noise_power = sig_power / (10.0 ** (snr_db / 10.0))

    if noise is None:
        noise_wave = np.random.normal(0.0, 1.0, size=audio_flat.shape).astype(np.float32)
    else:
        noise_flat = np.asarray(noise, dtype=np.float32).ravel()
        if len(noise_flat) < len(audio_flat):
            reps = int(np.ceil(len(audio_flat) / len(noise_flat)))
            noise_wave = np.tile(noise_flat, reps)[:len(audio_flat)]
        else:
            noise_wave = noise_flat[:len(audio_flat)]

    curr_noise_power = float(np.mean(noise_wave ** 2))
    if curr_noise_power > 1e-12:
        noise_wave = noise_wave * np.sqrt(target_noise_power / curr_noise_power)

    augmented = audio_flat + noise_wave
    return np.clip(augmented, -1.0, 1.0).astype(np.float32)


def random_augment(
    audio: np.ndarray,
    sample_rate: int = 16000,
    speed_range: Tuple[float, float] = (0.8, 1.2),
    pitch_range: Tuple[float, float] = (-2.0, 2.0),
    noise_snr_range: Optional[Tuple[float, float]] = (15.0, 30.0),
    seed: Optional[int] = None
) -> np.ndarray:
    """
    Applies a randomized pipeline of speed scaling, pitch shifting, and noise injection
    for training acoustic models on dysarthric speech variations.

    Args:
        audio (np.ndarray): 1D float32 audio waveform.
        sample_rate (int): Audio sample rate in Hz.
        speed_range (Tuple[float, float]): (min_rate, max_rate) for speed scaling.
        pitch_range (Tuple[float, float]): (min_semitones, max_semitones) for pitch shifting.
        noise_snr_range (Optional[Tuple[float, float]]): (min_snr, max_snr) in dB. None to disable.
        seed (Optional[int]): Random seed for reproducibility.

    Returns:
        np.ndarray: Randomly augmented float32 audio waveform.
    """
    rng = np.random.default_rng(seed)
    out = np.asarray(audio, dtype=np.float32).copy()

    # Random speed scaling
    if speed_range:
        rate = float(rng.uniform(speed_range[0], speed_range[1]))
        out = speed_scale(out, rate)

    # Random pitch shifting
    if pitch_range:
        semitones = float(rng.uniform(pitch_range[0], pitch_range[1]))
        out = pitch_shift(out, semitones, sample_rate)

    # Random noise injection
    if noise_snr_range:
        snr_db = float(rng.uniform(noise_snr_range[0], noise_snr_range[1]))
        out = inject_noise(out, snr_db)

    return out


if __name__ == "__main__":
    print("=" * 70)
    print("ResonantAI Audio Augmentation Module - Self-Verification Test")
    print("=" * 70)

    # Step 1: Generate 1-second synthetic 16kHz sine wave (float32, range [-1.0, 1.0])
    sample_rate = 16000
    duration_s = 1.0
    freq_hz = 440.0  # Concert A (440 Hz)

    t = np.linspace(0.0, duration_s, int(sample_rate * duration_s), endpoint=False, dtype=np.float32)
    orig_audio = np.sin(2.0 * np.pi * freq_hz * t).astype(np.float32)

    print(f"Original Signal:")
    print(f"  Sample Rate    : {sample_rate} Hz")
    print(f"  Duration       : {duration_s:.2f} s ({len(orig_audio)} samples)")
    print(f"  Data Type      : {orig_audio.dtype}")
    print(f"  Min / Max Value: [{orig_audio.min():.6f}, {orig_audio.max():.6f}]")
    print("-" * 70)

    # Test cases to execute and assert
    test_suite = [
        ("Speed Scale 0.7x (Slower/Stretched)", speed_scale(orig_audio, 0.7)),
        ("Speed Scale 1.3x (Faster/Compressed)", speed_scale(orig_audio, 1.3)),
        ("Pitch Shift -2 Semitones (Lower)", pitch_shift(orig_audio, -2.0, sample_rate)),
        ("Pitch Shift +2 Semitones (Higher)", pitch_shift(orig_audio, 2.0, sample_rate)),
        ("Noise Injection (20 dB SNR)", inject_noise(orig_audio, 20.0)),
    ]

    all_passed = True

    for name, transformed in test_suite:
        # Verification assertions
        assert transformed.dtype == np.float32, f"FAILED: {name} dtype is {transformed.dtype}, expected float32"
        assert transformed.min() >= -1.0, f"FAILED: {name} min value {transformed.min()} < -1.0"
        assert transformed.max() <= 1.0, f"FAILED: {name} max value {transformed.max()} > 1.0"
        assert np.all(np.isfinite(transformed)), f"FAILED: {name} contains NaN or infinite values"

        orig_samples = len(orig_audio)
        mod_samples = len(transformed)
        print(f"[PASS] {name}")
        print(f"       Samples: {orig_samples} -> {mod_samples} | Min: {transformed.min():.6f} | Max: {transformed.max():.6f} | Dtype: {transformed.dtype}")

    # Verify edge cases: empty array and 1-sample array
    empty_audio = np.empty(0, dtype=np.float32)
    assert len(speed_scale(empty_audio, 1.0)) == 0
    assert len(pitch_shift(empty_audio, 2.0)) == 0
    assert len(inject_noise(empty_audio, 20.0)) == 0

    print("-" * 70)
    print("Edge-case checks passed (empty arrays handled gracefully).")
    print("=" * 70)
    print("ALL DATA AUGMENTATION VERIFICATION GATES PASSED SUCCESSFULLY!")
    print("=" * 70)
