"""
Local manual test script for Speech-to-Text (STT) Sarvam integration.
Usage:
    python scripts/test_stt.py --audio [path_to_audio_file.wav] --language [language_code] --provider [provider]
"""

import sys
import os
import asyncio
import wave
import struct
import argparse
from pathlib import Path

# Add project root directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.stt import get_stt_engine
from app.core.exceptions import STTProcessingError


def create_sample_wav(file_path: Path) -> Path:
    """Generate a 1-second 16kHz mono silent WAV file for local testing."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    sample_rate = 16000
    duration = 1.0  # seconds
    num_samples = int(sample_rate * duration)

    with wave.open(str(file_path), "wb") as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit PCM
        wav_file.setframerate(sample_rate)
        # Write silence (0s)
        for _ in range(num_samples):
            wav_file.writeframes(struct.pack("<h", 0))

    return file_path


def parse_arguments():
    """Parse CLI arguments for STT local test script."""
    parser = argparse.ArgumentParser(description="STT Integration Local Test CLI")
    parser.add_argument(
        "--audio",
        type=str,
        default=None,
        help="Path to the audio file to transcribe."
    )
    parser.add_argument(
        "--language",
        type=str,
        default=None,
        help="Language code for transcription (e.g. en-IN, hi-IN, mr-IN, kn-IN)."
    )
    parser.add_argument(
        "--provider",
        type=str,
        default="sarvam",
        help="STT provider to use (default: sarvam)."
    )
    return parser.parse_args()


async def main():
    args = parse_arguments()

    # Determine the audio path and check presence
    using_sample = False
    if args.audio is not None:
        audio_path = Path(args.audio)
    else:
        sample_path = Path(__file__).resolve().parent.parent / "data" / "sample_audio.wav"
        if not sample_path.exists():
            print(f"Creating sample audio file at: {sample_path}")
            create_sample_wav(sample_path)
        audio_path = sample_path
        using_sample = True

    # Resolve paths correctly and check existence
    resolved_path = audio_path.resolve()
    if not audio_path.exists() or audio_path.is_dir():
        print(f"Audio file does not exist: {resolved_path}")
        sys.exit(1)

    if using_sample:
        print(f"Using sample audio path: {audio_path.name}")
        print("Note: sample_audio.wav may contain no speech.")
        print()

    print("==================================================")
    print("         STT Integration Local Test               ")
    print("==================================================")
    print()
    print("Audio:")
    print(str(audio_path))
    print()
    print("Provider:")
    print(args.provider)
    print()
    print("Requested language:")
    print(args.language if args.language else "None")
    print()

    status = "error"
    latency_str = "0.00 ms"
    transcript = "(empty)"
    error_msg = None

    try:
        engine = get_stt_engine(args.provider)
        result = await engine.transcribe(audio_path, language_code=args.language)
        
        latency_str = f"{result.latency_ms:.2f} ms"
        
        if result.status == "error":
            status = "error"
            transcript = "(empty)"
            error_msg = result.error or "Transcription failed."
        elif not result.text or not result.text.strip():
            status = "error"
            transcript = "(empty)"
            error_msg = "Empty transcription received from provider."
        else:
            status = "success"
            transcript = result.text.strip()
            error_msg = None

    except STTProcessingError as err:
        status = "error"
        transcript = "(empty)"
        error_msg = str(err)
    except Exception as err:
        status = "error"
        transcript = "(empty)"
        error_msg = f"Unexpected error: {err}"

    print("Status:")
    print(status)
    print()
    print("Latency:")
    print(latency_str)
    print()
    print("Transcript:")
    print(transcript)
    print()
    if error_msg:
        print("Error:")
        print(error_msg)
        if error_msg == "Empty transcription received from provider.":
            print("Check that the audio contains audible speech.")
        print()


if __name__ == "__main__":
    asyncio.run(main())
