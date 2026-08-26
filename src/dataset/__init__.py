"""
ResonantAI Dataset Utilities
Modules for data ingestion, downloading, preparation, and audio augmentation
for dysarthric speech datasets (TORGO, UA-Speech).
"""

from .augment import speed_scale, pitch_shift, inject_noise, random_augment
from .download_stubs import (
    download_torgo,
    prepare_torgo,
    download_ua_speech_instructions,
    prepare_ua_speech,
    build_dataset_manifest,
    augment_dataset,
)

__all__ = [
    "speed_scale",
    "pitch_shift",
    "inject_noise",
    "random_augment",
    "download_torgo",
    "prepare_torgo",
    "download_ua_speech_instructions",
    "prepare_ua_speech",
    "build_dataset_manifest",
    "augment_dataset",
]
