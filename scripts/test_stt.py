"""
Local manual test script for Speech-to-Text (STT) Sarvam integration.
Usage:
    python scripts/test_stt.py [path_to_audio_file.wav]
"""

import sys
import os
import asyncio
import wave
import struct
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


async def main():
    print("==================================================")
    print("         STT Integration Local Test               ")
    print("==================================================")

    if len(sys.argv) > 1:
        audio_path = Path(sys.argv[1])
    else:
        sample_path = Path(__file__).resolve().parent.parent / "data" / "sample_audio.wav"
        if not sample_path.exists():
            print(f"Creating sample audio file at: {sample_path}")
            create_sample_wav(sample_path)
        audio_path = sample_path

    print(f"Loading audio file: {audio_path}")

    try:
        engine = get_stt_engine("sarvam")
        result = await engine.transcribe(audio_path)

        print("\n--- Transcription Result ---")
        print(f"Status:      {result.status}")
        print(f"Provider:    {result.provider}")
        print(f"Latency:     {result.latency_ms:.2f} ms")
        print(f"Language:    {result.language}")
        print(f"Transcript:  {result.text if result.text else '(empty)'}")
        if result.error:
            print(f"Error:       {result.error}")
        print("----------------------------\n")

    except STTProcessingError as err:
        print(f"\n[STT ERROR]: {err}")
    except Exception as err:
        print(f"\n[UNEXPECTED ERROR]: {err}")


if __name__ == "__main__":
    asyncio.run(main())
