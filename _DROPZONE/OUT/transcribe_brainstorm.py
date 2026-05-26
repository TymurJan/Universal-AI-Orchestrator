#!/usr/bin/env python3
"""Transcribe brainstorm m4a with faster-whisper (local)."""
import sys
from pathlib import Path

AUDIO = Path(__file__).resolve().parents[1] / "IN" / "пн 16.06 бреншторм по гранту IREX-3.m4a"
OUT = Path(__file__).resolve().parent / "пн_16.06_бреншторм_IREX-3_transcript.txt"

def main():
    if not AUDIO.exists():
        print(f"Missing: {AUDIO}", file=sys.stderr)
        sys.exit(1)

    from faster_whisper import WhisperModel

    print(f"Loading model (small, uk)...", flush=True)
    model = WhisperModel("small", device="cpu", compute_type="int8")

    print(f"Transcribing: {AUDIO.name} ({AUDIO.stat().st_size // 1024 // 1024} MB)", flush=True)
    segments, info = model.transcribe(
        str(AUDIO),
        language="uk",
        vad_filter=True,
        beam_size=5,
    )
    print(f"Duration: {info.duration:.0f}s, lang={info.language}", flush=True)

    lines = []
    for seg in segments:
        t0 = int(seg.start // 60)
        s0 = int(seg.start % 60)
        lines.append(f"[{t0:02d}:{s0:02d}] {seg.text.strip()}")

    text = "\n".join(lines)
    OUT.write_text(text, encoding="utf-8")
    print(f"Wrote {len(lines)} segments -> {OUT}", flush=True)

if __name__ == "__main__":
    main()
