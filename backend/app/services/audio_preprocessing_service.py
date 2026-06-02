import json
import logging
import subprocess
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

MAX_REFERENCE_DURATION = 15.0
MIN_CROP_DURATION = 3.0


class AudioPreprocessingError(ValueError):
    """Raised when audio validation or processing fails."""


def _ffprobe(path: Path, entries: str, section: str = "format") -> str:
    result = subprocess.run(
        [
            "ffprobe", "-v", "quiet",
            "-show_entries", f"{section}={entries}",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        capture_output=True,
        timeout=30,
    )
    if result.returncode != 0:
        raise AudioPreprocessingError(
            f"ffprobe failed on {path.name}: {result.stderr.decode(errors='replace')[-200:]}"
        )
    return result.stdout.decode().strip()


def _ffprobe_safe(path: Path, entries: str, section: str = "format") -> str:
    """Like _ffprobe but returns '' instead of raising on failure."""
    try:
        return _ffprobe(path, entries, section)
    except AudioPreprocessingError:
        return ""


def _parse_duration_str(raw: Optional[str]) -> Optional[float]:
    """Parse a duration string from ffprobe output; returns None if invalid or non-positive."""
    if not raw:
        return None
    first = raw.splitlines()[0].strip()
    if not first or first == "N/A":
        return None
    try:
        val = float(first)
        return val if val > 0 else None
    except (ValueError, TypeError):
        return None


def probe_duration(path: Path) -> float:
    """Return audio duration in seconds with multiple fallback strategies.

    Browser-recorded WebM (Chrome/Edge/Firefox via MediaRecorder) often lacks a
    Duration element in the container header. Four strategies are tried in order,
    guaranteeing a result even when metadata is absent.
    """
    size = path.stat().st_size if path.exists() else -1
    logger.debug("probe_duration: %s  size=%d bytes", path.name, size)

    # Strategy 1: format section — fast path for WAV, MP3, MP4, FLAC, OGG(some)
    raw = _ffprobe_safe(path, "duration", section="format")
    dur = _parse_duration_str(raw)
    if dur is not None:
        logger.debug("probe_duration[S1:format]: %s → %.3f s", path.name, dur)
        return dur

    # Strategy 2: stream section — needed for OGG and some MKV/WebM with stream-level info
    raw = _ffprobe_safe(path, "duration", section="stream")
    dur = _parse_duration_str(raw)
    if dur is not None:
        logger.debug("probe_duration[S2:stream]: %s → %.3f s", path.name, dur)
        return dur

    # Strategy 3: force full file scan.
    # Chrome/Edge MediaRecorder produces WebM without a Duration element in the
    # Segment Info block. ffprobe's default probesize stops reading early and
    # reports N/A. With probesize=100 MB we read the entire file, letting ffprobe
    # derive duration from the last packet timestamp.
    logger.debug(
        "probe_duration[S3:full-scan]: %s — format/stream headers lack duration, scanning full file",
        path.name,
    )
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "quiet",
                "-probesize", "104857600",       # 100 MB — covers any short reference clip
                "-analyzeduration", "100000000", # 100 s in microseconds
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(path),
            ],
            capture_output=True,
            timeout=60,
        )
        raw = result.stdout.decode().strip()
        dur = _parse_duration_str(raw)
        if dur is not None:
            logger.debug("probe_duration[S3:full-scan]: %s → %.3f s", path.name, dur)
            return dur
        logger.debug("probe_duration[S3:full-scan]: %s → still N/A", path.name)
    except (subprocess.TimeoutExpired, OSError) as exc:
        logger.debug("probe_duration[S3:full-scan]: %s — error: %s", path.name, exc)

    # Strategy 4: derive from last audio packet timestamp.
    # ffprobe reads every packet PTS; the last one equals the duration.
    logger.debug("probe_duration[S4:packets]: %s — reading packet timestamps", path.name)
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "quiet",
                "-select_streams", "a:0",
                "-show_entries", "packet=pts_time",
                "-of", "csv=print_section=0",
                str(path),
            ],
            capture_output=True,
            timeout=60,
        )
        lines = [l.strip() for l in result.stdout.decode().splitlines() if l.strip()]
        for line in reversed(lines):
            dur = _parse_duration_str(line)
            if dur is not None:
                logger.debug(
                    "probe_duration[S4:packets]: %s → %.3f s (last packet PTS)",
                    path.name, dur,
                )
                return dur
        logger.debug("probe_duration[S4:packets]: %s — no valid PTS found", path.name)
    except (subprocess.TimeoutExpired, OSError) as exc:
        logger.debug("probe_duration[S4:packets]: %s — error: %s", path.name, exc)

    logger.error(
        "probe_duration: all 4 strategies failed for %s (size=%d bytes)",
        path.name, size,
    )
    raise AudioPreprocessingError(
        f"Could not determine audio duration for '{path.name}'"
    )


def probe_format_name(path: Path) -> str:
    """Return the primary format name (e.g. 'mp3', 'ogg', 'wav')."""
    try:
        raw = _ffprobe(path, "format_name", section="format")
        return raw.split(",")[0].strip() if raw else "unknown"
    except AudioPreprocessingError:
        return "unknown"


def validate_crop(total_duration: float, crop_start: float, crop_end: float) -> None:
    """Raise AudioPreprocessingError if the crop parameters are invalid."""
    if crop_start < 0:
        raise AudioPreprocessingError("crop_start must be >= 0")
    if crop_end <= crop_start:
        raise AudioPreprocessingError("crop_end must be greater than crop_start")
    if crop_start > total_duration:
        raise AudioPreprocessingError(
            f"crop_start ({crop_start:.2f}s) exceeds audio duration ({total_duration:.2f}s)"
        )
    # Allow a small tolerance for floating-point imprecision from the frontend
    if crop_end > total_duration + 0.5:
        raise AudioPreprocessingError(
            f"crop_end ({crop_end:.2f}s) exceeds audio duration ({total_duration:.2f}s)"
        )
    crop_len = crop_end - crop_start
    if crop_len > MAX_REFERENCE_DURATION + 0.05:
        raise AudioPreprocessingError(
            f"Reference voice samples must be {int(MAX_REFERENCE_DURATION)} seconds or shorter "
            f"(selected region is {crop_len:.2f}s)"
        )
    if crop_len < MIN_CROP_DURATION - 0.05:
        raise AudioPreprocessingError(
            f"Reference sample must be at least {int(MIN_CROP_DURATION)} seconds "
            f"(selected region is {crop_len:.2f}s)"
        )


def process_audio(
    source_path: Path,
    output_path: Path,
    crop_start: float,
    crop_end: float,
    source_filename: str = "",
) -> dict:
    """
    Trim [crop_start, crop_end] from source_path and normalize to:
        WAV / mono / 16 kHz / PCM 16-bit

    Writes the result to output_path. Returns a metadata dict.
    Raises AudioPreprocessingError on any validation or conversion failure.
    """
    total_duration = probe_duration(source_path)
    source_format = probe_format_name(source_path)

    validate_crop(total_duration, crop_start, crop_end)

    result = subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", str(source_path),
            "-ss", f"{crop_start:.6f}",
            "-to", f"{crop_end:.6f}",
            "-ar", "16000",
            "-ac", "1",
            "-c:a", "pcm_s16le",
            "-vn",              # discard video streams (e.g. MP4 with video track)
            str(output_path),
        ],
        capture_output=True,
        timeout=120,
    )

    if result.returncode != 0:
        logger.error("ffmpeg stderr: %s", result.stderr.decode(errors="replace"))
        raise AudioPreprocessingError(
            "Audio conversion failed. Ensure the file is a valid audio file."
        )

    if not output_path.exists() or output_path.stat().st_size == 0:
        raise AudioPreprocessingError("Conversion produced no output file")

    # Final backend enforcement: reject if the normalized output still exceeds the limit
    output_duration = probe_duration(output_path)
    if output_duration > MAX_REFERENCE_DURATION + 0.5:
        output_path.unlink(missing_ok=True)
        raise AudioPreprocessingError(
            f"Processed audio is {output_duration:.2f}s — backend limit is "
            f"{int(MAX_REFERENCE_DURATION)}s"
        )

    return {
        "source_format": source_format,
        "source_filename": source_filename,
        "duration": round(output_duration, 3),
        "sample_rate": 16000,
        "channels": 1,
        "codec": "pcm_s16le",
        "crop_start": round(crop_start, 3),
        "crop_end": round(crop_end, 3),
    }


def write_metadata_json(path: Path, profile_id: str, name: str, meta: dict, **extra) -> None:
    """Write (or overwrite) the metadata.json file for a voice profile directory."""
    from datetime import datetime, timezone
    data = {
        "id": profile_id,
        "name": name,
        "language": extra.get("language"),
        "duration": meta["duration"],
        "sample_rate": meta["sample_rate"],
        "channels": meta["channels"],
        "codec": meta["codec"],
        "transcript": extra.get("transcript"),
        "source_format": meta["source_format"],
        "created_at": extra.get("created_at", datetime.now(timezone.utc).isoformat()),
    }
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
