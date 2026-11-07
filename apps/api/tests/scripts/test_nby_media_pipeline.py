"""Behavioural tests for ``scripts/media/nby-media.sh`` (Nơi bình yên PRD NBY-09 AC02, §7.6).

Runs the real script with the real ffmpeg on synthetic inputs (a drifting sine wave, a tone and
pink noise).
This proves format, loop, loudness, metadata and manifest behaviour; it says nothing about how a
real AI-generated scene looks, which stays a human review gate (NBY-09 AC03).
"""

from __future__ import annotations

import hashlib
import itertools
import json
import os
import re
import shutil
import statistics
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
SCRIPT = REPO_ROOT / "scripts" / "media" / "nby-media.sh"
FFMPEG = shutil.which("ffmpeg") or "ffmpeg"


def _has_encoders() -> bool:
    if shutil.which(FFMPEG) is None:
        return False
    listing = subprocess.run(  # noqa: S603
        [FFMPEG, "-hide_banner", "-encoders"], capture_output=True, text=True, check=False
    ).stdout
    return all(name in listing for name in ("libx264", "libx265", " aac "))


pytestmark = pytest.mark.skipif(
    not _has_encoders(), reason="ffmpeg with libx264, libx265 and aac is required"
)


def _ffmpeg(*args: str) -> None:
    subprocess.run(  # noqa: S603
        [FFMPEG, "-hide_banner", "-loglevel", "error", "-y", *args], check=True
    )


def _info(path: Path) -> str:
    return subprocess.run(  # noqa: S603
        [FFMPEG, "-hide_banner", "-i", str(path)], capture_output=True, text=True, check=False
    ).stderr


def _duration(path: Path) -> float:
    match = re.search(r"Duration: (\d+):(\d+):([\d.]+)", _info(path))
    assert match, f"no duration for {path}"
    hours, minutes, seconds = match.groups()
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def _loudness(path: Path) -> float:
    log = subprocess.run(  # noqa: S603
        [
            FFMPEG,
            "-hide_banner",
            "-nostats",
            "-i",
            str(path),
            "-af",
            "ebur128=framelog=quiet",
            "-f",
            "null",
            "-",
        ],
        capture_output=True,
        text=True,
        check=False,
    ).stderr
    values = re.findall(r"^\s+I:\s+(-?[\d.]+) LUFS", log, flags=re.MULTILINE)
    assert values, log
    return float(values[-1])


def _gray_frames(path: Path, width: int = 36, height: int = 64) -> list[bytes]:
    raw = subprocess.run(  # noqa: S603
        [
            FFMPEG,
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(path),
            "-vf",
            f"scale={width}:{height},format=gray",
            "-f",
            "rawvideo",
            "-",
        ],
        capture_output=True,
        check=True,
    ).stdout
    size = width * height
    return [raw[i : i + size] for i in range(0, len(raw), size)]


def _mean_abs_diff(a: bytes, b: bytes) -> float:
    return sum(abs(x - y) for x, y in zip(a, b, strict=True)) / len(a)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "NBY_MEDIA_PRESET": "ultrafast"}
    return subprocess.run(  # noqa: S603
        ["/bin/bash", str(SCRIPT), *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.fixture(scope="module")
def produced(tmp_path_factory: pytest.TempPathFactory) -> Path:
    work = tmp_path_factory.mktemp("nby-media")
    # A landscape sine wave drifting one period per 10 s: a hard cut at 15 s jumps half a period,
    # so the seam test can tell a real loop from a cut. The audio track and GPS tag must vanish.
    _ffmpeg(
        "-f",
        "lavfi",
        "-i",
        "color=c=black:s=960x540:r=30,geq=lum='128+90*sin(2*PI*(X/W-T/10))':cb=128:cr=128",
        "-f",
        "lavfi",
        "-i",
        "sine=f=220",
        "-t",
        "20",
        "-metadata",
        "location=+10.7769+106.7009/",
        "-c:v",
        "libx264",
        "-preset",
        "ultrafast",
        "-c:a",
        "aac",
        "-shortest",
        str(work / "scene one'.mp4"),
    )
    _ffmpeg(
        "-f", "lavfi", "-i", "sine=f=440:sample_rate=44100", "-t", "10", str(work / "music.m4a")
    )
    _ffmpeg(
        "-f",
        "lavfi",
        "-i",
        "anoisesrc=color=pink:amplitude=0.2",
        "-t",
        "10",
        str(work / "ambient.m4a"),
    )
    result = _run(
        "-v",
        "scene one'.mp4",
        "-g",
        'Tool "X" 3.1',
        "-a",
        "ambient.m4a",
        "-m",
        "music.m4a",
        "-o",
        "out",
        cwd=work,
    )
    assert result.returncode == 0, result.stderr
    return work / "out"


def test_outputs_have_safe_names(produced: Path) -> None:
    names = sorted(p.name for p in produced.iterdir())
    assert names == [
        "ambient.ambient.m4a",
        "music.music.m4a",
        "scene_one_.h264.mp4",
        "scene_one_.hevc.mp4",
        "scene_one_.manifest-entry.json",
        "scene_one_.poster.jpg",
    ]


@pytest.mark.parametrize(("name", "codec"), [("h264", "h264"), ("hevc", "hevc (Main) (hvc1")])
def test_video_is_portrait_24fps_loop_without_audio(produced: Path, name: str, codec: str) -> None:
    path = produced / f"scene_one_.{name}.mp4"
    info = _info(path)
    assert f"Video: {codec}" in info
    assert "1080x1920 [SAR 1:1 DAR 9:16]" in info
    assert "24 fps" in info
    assert "Audio:" not in info
    # 16 s used from the source, minus the 1 s that dissolves into the head.
    assert _duration(path) == pytest.approx(15.0, abs=0.05)


@pytest.mark.parametrize("name", ["h264", "hevc"])
def test_source_metadata_dropped_and_ai_label_written(produced: Path, name: str) -> None:
    info = _info(produced / f"scene_one_.{name}.mp4")
    assert "location" not in info
    assert "+10.7769" not in info
    assert "AI-generated (trainedAlgorithmicMedia); tool=Tool _X_ 3.1" in info


def test_loop_seam_is_no_bigger_than_a_normal_frame_step(produced: Path) -> None:
    frames = _gray_frames(produced / "scene_one_.h264.mp4")
    assert len(frames) == 360
    steps = [_mean_abs_diff(a, b) for a, b in itertools.pairwise(frames)]
    typical = statistics.median(steps)
    assert typical > 0.5  # the input really moves
    seam = _mean_abs_diff(frames[-1], frames[0])
    # Measured: ~1.5 here; a hard cut of the same input measures ~96.
    assert seam <= typical * 3, (seam, typical)


@pytest.mark.parametrize(
    ("name", "lufs"), [("ambient.ambient.m4a", -23.0), ("music.music.m4a", -32.0)]
)
def test_audio_layers_are_60s_loops_at_target_loudness(
    produced: Path, name: str, lufs: float
) -> None:
    path = produced / name
    info = _info(path)
    assert "Audio: aac" in info and "48000 Hz, stereo" in info
    assert "Video:" not in info
    assert _duration(path) == pytest.approx(60.0, abs=0.3)
    assert _loudness(path) == pytest.approx(lufs, abs=1.0)


def test_manifest_entry_hashes_match_files(produced: Path) -> None:
    entry = json.loads((produced / "scene_one_.manifest-entry.json").read_text())
    video = entry["video"]
    assert video["ai_label"] == {
        "tool": "Tool _X_ 3.1",
        "digital_source_type": "trainedAlgorithmicMedia",
    }
    for src, digest in (
        ("src_h264", "sha256_h264"),
        ("src_hevc", "sha256_hevc"),
        ("poster", "sha256_poster"),
    ):
        assert video[digest] == _sha256(produced / video[src])
    for kind, lufs in (("ambient", -23), ("music", -32)):
        assert entry[kind]["sha256"] == _sha256(produced / entry[kind]["src"])
        assert entry[kind]["loudness_lufs"] == lufs


@pytest.fixture(scope="module")
def rejects(tmp_path_factory: pytest.TempPathFactory) -> Path:
    work = tmp_path_factory.mktemp("nby-media-rejects")
    _ffmpeg(
        "-f",
        "lavfi",
        "-i",
        "testsrc2=size=640x360:rate=24",
        "-t",
        "5",
        "-c:v",
        "libx264",
        "-preset",
        "ultrafast",
        str(work / "short.mp4"),
    )
    _ffmpeg(
        "-f",
        "lavfi",
        "-i",
        "testsrc2=size=640x360:rate=24",
        "-t",
        "10",
        "-c:v",
        "mpeg4",
        str(work / "mpeg4.mp4"),
    )
    _ffmpeg(
        "-f",
        "lavfi",
        "-i",
        "testsrc2=size=640x360:rate=24",
        "-t",
        "10",
        "-c:v",
        "libx264",
        "-preset",
        "ultrafast",
        str(work / "ok.mp4"),
    )
    return work


@pytest.mark.parametrize(
    ("args", "message"),
    [
        ((), "usage"),
        (("-v", "short.mp4", "-g", "t"), "video must be 8-30 s"),
        (("-v", "mpeg4.mp4", "-g", "t"), "video codec must be h264, hevc or prores"),
        (("-v", "ok.mp4"), "-g <AI tool name> is required"),
        (("-m", "ok.mp4"), "no audio stream"),
        (("-a", "missing.m4a"), "not a file"),
        (("-v", "ok.mp4", "-g", "t", "-t", "1;rm"), "must be numbers"),
    ],
)
def test_rejects_bad_input_without_output(
    rejects: Path, args: tuple[str, ...], message: str
) -> None:
    result = _run(*args, "-o", "out", cwd=rejects) if args else _run(cwd=rejects)
    assert result.returncode == 2
    assert message in result.stderr
    assert not (rejects / "out").exists()
