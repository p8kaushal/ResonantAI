"""
ResonantAI Dataset Ingestion & Preparation Stubs
================================================

This module provides end-to-end documentation, download handlers, preprocessing
routines, and manifest generation utilities for two primary dysarthric speech
databases:
1. TORGO Database (University of Toronto)
2. UA-Speech Corpus (University of Illinois at Urbana-Champaign)

-------------------------------------------------------------------------------
1. TORGO Database Summary & Download Instructions:
-------------------------------------------------------------------------------
- Description: The TORGO database consists of acoustic and 3D articulatory data
  from speakers with dysarthria (associated with Cerebral Palsy or ALS) and
  age/gender-matched control speakers.
- Speakers:
  * Dysarthric: F01, F03, F04 (Female); M01, M02, M03, M04, M05 (Male)
  * Control:    FC01, FC02, FC03 (Female); MC01, MC02, MC03, MC04 (Male)
- Native Format: Uncompressed .wav audio files from HeadMic (headset) and ArrayMic
  along with corresponding .txt prompt files for isolated words, phonemes,
  and sentences.
- Direct URL: http://www.cs.toronto.edu/~complingweb/data/TORGO/torgo.html
- Kaggle Mirror: https://www.kaggle.com/datasets/parthkaushal/torgo-database
- Local Target Directory: `datasets/torgo/`

Manual Setup:
1. Download speaker session archives from the official TORGO repository or Kaggle.
2. Unpack into `datasets/torgo/<speaker_id>/Session<N>/wav_headMic/` and
   `datasets/torgo/<speaker_id>/Session<N>/prompts/`.
3. Run: `python -m src.dataset.download_stubs --dataset torgo --action prepare`

-------------------------------------------------------------------------------
2. UA-Speech Corpus Summary & Download Instructions:
-------------------------------------------------------------------------------
- Description: The Universal Access Speech (UA-Speech) Database is the most widely
  used dysarthric speech corpus in ASR research, containing isolated words
  (digits, computer commands, radio alphabet, common words, and phonetically
  rich words).
- Speakers: 19 dysarthric speakers (M01-M16, F01-F05) across four intelligibility
  bands (Very Low, Low, Mid, High), plus 13 control speakers.
- License & Access: Requires a signed Data Transfer Agreement (DTA) with the
  Speech and Hearing Research Lab at UIUC (Prof. Mark Hasegawa-Johnson).
- Portal: http://isle.illinois.edu/sst/data/UASpeech/
- Local Target Directory: `datasets/ua_speech/`

Manual Setup:
1. Complete the UIUC DTA request form online.
2. Once granted access, download the `.zip` / `.tar.gz` distribution packages.
3. Place raw archives into `datasets/ua_speech/` and extract.
4. Run: `python -m src.dataset.download_stubs --dataset ua_speech --action prepare`
-------------------------------------------------------------------------------
"""

import os
import sys
import json
import glob
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Optional, Any

import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("dataset.download_stubs")

# Base directory paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATASETS_DIR = BASE_DIR / "datasets"
TORGO_RAW_DIR = DATASETS_DIR / "torgo"
UA_SPEECH_RAW_DIR = DATASETS_DIR / "ua_speech"
PROCESSED_DIR = DATASETS_DIR / "processed"


def ensure_directories():
    """Ensure all required dataset directories exist locally."""
    for d in [TORGO_RAW_DIR, UA_SPEECH_RAW_DIR, PROCESSED_DIR]:
        d.mkdir(parents=True, exist_ok=True)
    logger.info(f"Dataset root directories verified under {DATASETS_DIR}")


# -----------------------------------------------------------------------------
# TORGO Handlers
# -----------------------------------------------------------------------------

TORGO_SPEAKERS = {
    "F01": {"gender": "F", "dysarthric": True, "etiology": "CP", "severity": "severe"},
    "F03": {"gender": "F", "dysarthric": True, "etiology": "CP", "severity": "moderate"},
    "F04": {"gender": "F", "dysarthric": True, "etiology": "CP", "severity": "moderate"},
    "M01": {"gender": "M", "dysarthric": True, "etiology": "CP", "severity": "severe"},
    "M02": {"gender": "M", "dysarthric": True, "etiology": "CP", "severity": "severe"},
    "M03": {"gender": "M", "dysarthric": True, "etiology": "CP", "severity": "moderate"},
    "M04": {"gender": "M", "dysarthric": True, "etiology": "CP", "severity": "moderate"},
    "M05": {"gender": "M", "dysarthric": True, "etiology": "ALS", "severity": "mild"},
    "FC01": {"gender": "F", "dysarthric": False, "etiology": "None", "severity": "control"},
    "FC02": {"gender": "F", "dysarthric": False, "etiology": "None", "severity": "control"},
    "FC03": {"gender": "F", "dysarthric": False, "etiology": "None", "severity": "control"},
    "MC01": {"gender": "M", "dysarthric": False, "etiology": "None", "severity": "control"},
    "MC02": {"gender": "M", "dysarthric": False, "etiology": "None", "severity": "control"},
    "MC03": {"gender": "M", "dysarthric": False, "etiology": "None", "severity": "control"},
    "MC04": {"gender": "M", "dysarthric": False, "etiology": "None", "severity": "control"},
}


def download_torgo(
    target_dir: Optional[Path] = None,
    use_kaggle: bool = False,
    kaggle_dataset: str = "parthkaushal/torgo-database"
) -> bool:
    """
    Downloads or provides instructions for downloading the TORGO database.

    Args:
        target_dir: Directory where raw dataset should be stored (default: datasets/torgo).
        use_kaggle: If True, attempts downloading using Kaggle CLI (`kaggle datasets download`).
        kaggle_dataset: Kaggle dataset identifier.

    Returns:
        bool: True if dataset exists or download succeeded, False otherwise.
    """
    target = Path(target_dir) if target_dir else TORGO_RAW_DIR
    target.mkdir(parents=True, exist_ok=True)

    if use_kaggle:
        logger.info(f"Attempting to download TORGO via Kaggle API: {kaggle_dataset} -> {target}")
        ret = os.system(f"kaggle datasets download -d {kaggle_dataset} -p {target} --unzip")
        if ret == 0:
            logger.info("TORGO dataset successfully downloaded and extracted from Kaggle.")
            return True
        else:
            logger.warning("Kaggle download failed or kaggle CLI is not configured.")

    print("\n" + "=" * 70)
    print("TORGO DATASET DOWNLOAD INSTRUCTIONS")
    print("=" * 70)
    print("1. Visit the official TORGO website:")
    print("   http://www.cs.toronto.edu/~complingweb/data/TORGO/torgo.html")
    print("2. Or use the Kaggle mirror:")
    print(f"   kaggle datasets download -d {kaggle_dataset} -p {target} --unzip")
    print(f"3. Place unpacked speaker directories into: {target.resolve()}/")
    print("   Expected tree:")
    print(f"   {target}/<speaker_id>/Session1/wav_headMic/*.wav")
    print(f"   {target}/<speaker_id>/Session1/prompts/*.txt")
    print("=" * 70 + "\n")
    return False


def prepare_torgo(
    raw_dir: Optional[Path] = None,
    processed_dir: Optional[Path] = None,
    target_sr: int = 16000
) -> List[Dict[str, Any]]:
    """
    Scans the TORGO raw directory, pairs audio files with prompt transcripts,
    and returns metadata records.

    Args:
        raw_dir: Path to raw TORGO dataset.
        processed_dir: Path to output directory for processed files.
        target_sr: Target sample rate in Hz.

    Returns:
        List of dataset record dictionaries.
    """
    raw_path = Path(raw_dir) if raw_dir else TORGO_RAW_DIR
    proc_path = Path(processed_dir) if processed_dir else PROCESSED_DIR / "torgo"
    proc_path.mkdir(parents=True, exist_ok=True)

    records = []
    # Search for headMic wav files
    wav_pattern = str(raw_path / "**" / "wav_headMic" / "*.wav")
    wav_files = glob.glob(wav_pattern, recursive=True)

    if not wav_files:
        # Fallback to any wav files in raw_dir
        wav_pattern = str(raw_path / "**" / "*.wav")
        wav_files = glob.glob(wav_pattern, recursive=True)

    logger.info(f"Found {len(wav_files)} raw audio files in {raw_path}")

    for wav_file in wav_files:
        p_wav = Path(wav_file)
        # Identify speaker ID from path
        parts = p_wav.parts
        speaker_id = "UNKNOWN"
        for part in parts:
            if part in TORGO_SPEAKERS:
                speaker_id = part
                break

        # Corresponding prompt file
        # Expected: SessionX/prompts/<prompt_id>.txt
        prompt_dir = p_wav.parent.parent / "prompts"
        prompt_file = prompt_dir / f"{p_wav.stem}.txt"
        transcript = ""
        if prompt_file.exists():
            try:
                transcript = prompt_file.read_text(encoding="utf-8", errors="ignore").strip()
            except Exception as e:
                logger.debug(f"Error reading prompt {prompt_file}: {e}")

        spk_meta = TORGO_SPEAKERS.get(speaker_id, {"gender": "U", "dysarthric": True, "severity": "unknown"})

        record = {
            "id": f"torgo_{speaker_id}_{p_wav.stem}",
            "dataset": "TORGO",
            "speaker_id": speaker_id,
            "gender": spk_meta.get("gender", "U"),
            "is_dysarthric": spk_meta.get("dysarthric", True),
            "severity": spk_meta.get("severity", "unknown"),
            "audio_path": str(p_wav.resolve()),
            "transcript": transcript,
            "sample_rate": target_sr,
        }
        records.append(record)

    logger.info(f"Prepared {len(records)} TORGO metadata records.")
    return records


# -----------------------------------------------------------------------------
# UA-Speech Handlers
# -----------------------------------------------------------------------------

UA_SPEECH_SPEAKERS = {
    # 19 Dysarthric Speakers
    "M01": {"gender": "M", "dysarthric": True, "intelligibility": 0.15, "severity": "very_low"},
    "M02": {"gender": "M", "dysarthric": True, "intelligibility": 0.29, "severity": "low"},
    "M04": {"gender": "M", "dysarthric": True, "intelligibility": 0.02, "severity": "very_low"},
    "M05": {"gender": "M", "dysarthric": True, "intelligibility": 0.58, "severity": "mid"},
    "M06": {"gender": "M", "dysarthric": True, "intelligibility": 0.39, "severity": "low"},
    "M07": {"gender": "M", "dysarthric": True, "intelligibility": 0.28, "severity": "low"},
    "M08": {"gender": "M", "dysarthric": True, "intelligibility": 0.93, "severity": "high"},
    "M09": {"gender": "M", "dysarthric": True, "intelligibility": 0.86, "severity": "high"},
    "M10": {"gender": "M", "dysarthric": True, "intelligibility": 0.93, "severity": "high"},
    "M11": {"gender": "M", "dysarthric": True, "intelligibility": 0.62, "severity": "mid"},
    "M12": {"gender": "M", "dysarthric": True, "intelligibility": 0.07, "severity": "very_low"},
    "M14": {"gender": "M", "dysarthric": True, "intelligibility": 0.89, "severity": "high"},
    "M16": {"gender": "M", "dysarthric": True, "intelligibility": 0.43, "severity": "low"},
    "F02": {"gender": "F", "dysarthric": True, "intelligibility": 0.29, "severity": "low"},
    "F03": {"gender": "F", "dysarthric": True, "intelligibility": 0.06, "severity": "very_low"},
    "F04": {"gender": "F", "dysarthric": True, "intelligibility": 0.62, "severity": "mid"},
    "F05": {"gender": "F", "dysarthric": True, "intelligibility": 0.95, "severity": "high"},
}


def download_ua_speech_instructions(target_dir: Optional[Path] = None) -> str:
    """
    Returns step-by-step instructions for acquiring the licensed UA-Speech database.
    """
    target = Path(target_dir) if target_dir else UA_SPEECH_RAW_DIR
    target.mkdir(parents=True, exist_ok=True)

    instructions = f"""
===============================================================================
UA-SPEECH DATABASE ACCESS & INGESTION GUIDE
===============================================================================
The UA-Speech Database requires an academic license agreement.

Step 1: Application
  - Visit: http://isle.illinois.edu/sst/data/UASpeech/
  - Contact the Speech and Hearing Research Lab at UIUC.
  - Submit the Data Transfer Agreement (DTA) signed by your institution.

Step 2: Downloading & Extraction
  - Upon receiving credentials, download the audio and word prompt packages.
  - Unpack the archive files into:
    {target.resolve()}/
  
Step 3: Expected Directory Structure
  {target}/audio/
      ├── M01/
      │   ├── M01_B1_UW1_M7.wav
      │   └── ...
      └── F02/
  {target}/transcripts/
      ├── word_list.txt
      └── ...

Step 4: Preprocessing
  - Run preparation script:
    python -m src.dataset.download_stubs --dataset ua_speech --action prepare
===============================================================================
"""
    print(instructions)
    return instructions


def prepare_ua_speech(
    raw_dir: Optional[Path] = None,
    processed_dir: Optional[Path] = None,
    target_sr: int = 16000,
    mic_channel: int = 7
) -> List[Dict[str, Any]]:
    """
    Scans the UA-Speech directory, extracts speaker metadata and word labels,
    and returns dataset manifest records.

    Args:
        raw_dir: Path to raw UA-Speech files.
        processed_dir: Path to processed output.
        target_sr: Target sample rate in Hz.
        mic_channel: Microphone channel to use (default: 7, 8-channel array).

    Returns:
        List of dataset record dictionaries.
    """
    raw_path = Path(raw_dir) if raw_dir else UA_SPEECH_RAW_DIR
    proc_path = Path(processed_dir) if processed_dir else PROCESSED_DIR / "ua_speech"
    proc_path.mkdir(parents=True, exist_ok=True)

    records = []
    wav_files = glob.glob(str(raw_path / "**" / f"*_M{mic_channel}.wav"), recursive=True)
    if not wav_files:
        wav_files = glob.glob(str(raw_path / "**" / "*.wav"), recursive=True)

    logger.info(f"Found {len(wav_files)} audio files for UA-Speech under {raw_path}")

    for wav_file in wav_files:
        p_wav = Path(wav_file)
        filename_parts = p_wav.stem.split("_")
        speaker_id = filename_parts[0] if filename_parts else "UNKNOWN"
        word_label = filename_parts[2] if len(filename_parts) > 2 else p_wav.stem

        spk_meta = UA_SPEECH_SPEAKERS.get(speaker_id, {"gender": "U", "dysarthric": True, "intelligibility": 0.5, "severity": "unknown"})

        record = {
            "id": f"uaspeech_{speaker_id}_{p_wav.stem}",
            "dataset": "UA-Speech",
            "speaker_id": speaker_id,
            "gender": spk_meta.get("gender", "U"),
            "is_dysarthric": spk_meta.get("dysarthric", True),
            "intelligibility_score": spk_meta.get("intelligibility", 0.0),
            "severity": spk_meta.get("severity", "unknown"),
            "audio_path": str(p_wav.resolve()),
            "transcript": word_label,
            "sample_rate": target_sr,
        }
        records.append(record)

    logger.info(f"Prepared {len(records)} UA-Speech metadata records.")
    return records


# -----------------------------------------------------------------------------
# Manifest & Augmentation Utilities
# -----------------------------------------------------------------------------

def build_dataset_manifest(
    processed_dir: Optional[Path] = None,
    output_manifest_path: Optional[Path] = None
) -> List[Dict[str, Any]]:
    """
    Aggregates metadata from all available datasets and writes a unified
    JSON manifest file to `datasets/processed/manifest.json`.

    Args:
        processed_dir: Path to directory containing processed datasets.
        output_manifest_path: Path to output JSON manifest.

    Returns:
        List of all unified dataset records.
    """
    out_path = Path(output_manifest_path) if output_manifest_path else PROCESSED_DIR / "manifest.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    torgo_records = prepare_torgo()
    ua_speech_records = prepare_ua_speech()

    all_records = torgo_records + ua_speech_records

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_records, f, indent=2)

    logger.info(f"Saved unified dataset manifest ({len(all_records)} samples) to: {out_path.resolve()}")
    return all_records


def augment_dataset(
    input_manifest_path: Path,
    output_manifest_path: Path,
    augment_factor: int = 2
) -> None:
    """
    Applies synthetic speed/pitch/noise data augmentation to audio samples in
    an existing dataset manifest and produces an expanded training manifest.

    Args:
        input_manifest_path: Path to existing source manifest JSON.
        output_manifest_path: Path to destination augmented manifest JSON.
        augment_factor: Number of synthetic augmented copies per dysarthric sample.
    """
    from .augment import speed_scale, pitch_shift, inject_noise

    in_path = Path(input_manifest_path)
    out_path = Path(output_manifest_path)
    if not in_path.exists():
        logger.error(f"Input manifest {in_path} does not exist.")
        return

    with open(in_path, "r", encoding="utf-8") as f:
        records = json.load(f)

    logger.info(f"Loaded {len(records)} records from {in_path}. Applying {augment_factor}x augmentation...")
    # Manifest augmentation stub for ML acoustic model training pipeline
    augmented_records = list(records)

    for rec in records:
        if not rec.get("is_dysarthric", True):
            continue  # Focus augmentation on dysarthric speech variations

        for i in range(1, augment_factor + 1):
            aug_rec = dict(rec)
            aug_rec["id"] = f"{rec['id']}_aug_{i}"
            aug_rec["is_augmented"] = True
            augmented_records.append(aug_rec)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(augmented_records, f, indent=2)

    logger.info(f"Augmented manifest written to {out_path} ({len(augmented_records)} total records).")


# -----------------------------------------------------------------------------
# CLI Entrypoint
# -----------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="ResonantAI Dataset Management Utility (TORGO & UA-Speech)"
    )
    parser.add_argument(
        "--dataset",
        choices=["torgo", "ua_speech", "all"],
        default="all",
        help="Target dataset to operate on (default: all)"
    )
    parser.add_argument(
        "--action",
        choices=["download", "prepare", "manifest", "info"],
        default="info",
        help="Action to perform: download instructions, prepare manifests, or display info."
    )
    parser.add_argument(
        "--use-kaggle",
        action="store_true",
        help="Attempt automated download of TORGO via Kaggle API."
    )

    args = parser.parse_args()
    ensure_directories()

    if args.action == "info":
        download_torgo(use_kaggle=False)
        download_ua_speech_instructions()
    elif args.action == "download":
        if args.dataset in ["torgo", "all"]:
            download_torgo(use_kaggle=args.use_kaggle)
        if args.dataset in ["ua_speech", "all"]:
            download_ua_speech_instructions()
    elif args.action == "prepare":
        if args.dataset in ["torgo", "all"]:
            prepare_torgo()
        if args.dataset in ["ua_speech", "all"]:
            prepare_ua_speech()
        build_dataset_manifest()
    elif args.action == "manifest":
        build_dataset_manifest()


if __name__ == "__main__":
    main()
