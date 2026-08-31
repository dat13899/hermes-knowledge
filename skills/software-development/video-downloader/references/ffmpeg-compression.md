# FFmpeg Compression Reference — Video Downloader Skill

## Environment

- Machine: Windows 10 (git-bash/MSYS2)
- `ffmpeg` 8.1.2-full_build (gyan.dev)
- Build config: `--enable-nvenc --enable-amf --enable-libx264 --enable-mediafoundation`

## HW encoder matrix

| Encoder | In binary | Works on this machine | Notes |
|---|---|---|---|
| `h264_mf` (MediaFoundation) | ✅ | ✅ | Bitrate-based only, no CQ/CRF. ~20x realtime speed |
| `h264_nvenc` (NVIDIA NVENC) | ✅ | ❌ | Fails: `-22 (Invalid argument)` even with `-rc vbr -cq 23` |
| `h264_amf` (AMD AMF) | ✅ | ❌ | `quality` param range is -1..2, not 0-51 |
| `libx264` (CPU) | ✅ | ✅ | CRF-based, `-preset veryfast` recommended (10-30x faster than `medium` for negligible quality loss) |

## libx264 preset speed vs quality tradeoff

For Telegram delivery (target < 48 MB, one watch on phone):

| Preset | Speed (relative) | Quality (relative) | Use case |
|---|---|---|---|
| `ultrafast` | 50x | Poor | Emergency compression only |
| `superfast` | 25x | Low | |
| **`veryfast`** | **15x** | **Good** | **Recommended — best balance** |
| `faster` | 10x | Very good | |
| `fast` | 5x | Great | |
| `medium` (default) | 1x | Excellent | Overkill for Telegram — 10-30x slower for barely visible difference |

**Rule**: always use `-preset veryfast` for post-download compression. `medium` is only for archival-quality encodes.

## Duration extraction (ffprobe)

```bash
ffprobe -v error -show_entries format=duration -of csv=p=0 input.mp4
# returns: 1265.32  (seconds, decimal)
```

Python:
```python
import subprocess
r = subprocess.run([
    "ffprobe", "-v", "error",
    "-show_entries", "format=duration",
    "-of", "csv=p=0", input_file
], capture_output=True, text=True, timeout=30)
duration = float(r.stdout.strip())
```

## Bitrate calculation

Target bitrate = (target_size_bytes × 8) / duration_seconds × 0.9 (10% headroom)

```python
TARGET_BYTES = 45 * 1024 * 1024  # 45 MB — under Telegram 50 MB limit
duration = 1265.32  # seconds
target_kbps = int(TARGET_BYTES * 8 / duration * 0.9 / 1000)
# = 45 * 1024 * 1024 * 8 / 1265.32 * 0.9 / 1000
# ≈ 263 kbps
```

## Compression command reference

### MediaFoundation (h264_mf) — bitrate target

`h264_mf` does NOT support CQ/CRF parameters — it uses target bitrate only.

```bash
ffmpeg -y -i input.mp4 ^
  -c:v h264_mf -b:v 2000k ^
  -c:a aac -b:a 96k ^
  -movflags +faststart -f mp4 output.mp4
```

Bitrate calculation with floor:
```python
target_kbps = max(200, int(TARGET_BYTES * 8 / duration * 0.9 / 1000))
```

**Minimum floor**: 200 kbps. Values below 100 produce unwatchable video at 720p+.

**2-pass escalation**: if first pass still > 48 MB, halve bitrate AND downscale to 720p:
```bash
ffmpeg -y -i input.mp4 ^
  -c:v h264_mf -b:v 1000k ^
  -vf "scale=-2:720" ^
  -c:a aac -b:a 64k ^
  -movflags +faststart -f mp4 output.mp4
```

**Boundary edge case**: h264_mf at very low bitrate (~177 kbps) + 720p can land exactly at 48 MB. The file may equal `48 * 1024 * 1024` bytes but still be rejected by `sz < MAX_TG`. Use `sz <= MAX_TG` to accept files at the boundary.

### libx264 — CRF escalation

Start at CRF 23 (visually lossless), increase CRF until target size met:

```bash
# CRF 28 — good balance (~50% of original)
ffmpeg -y -i input.mp4 ^
  -c:v libx264 -crf 28 -preset veryfast ^
  -c:a aac -b:a 96k ^
  -movflags +faststart -f mp4 output.mp4

# CRF 35 — aggressive compression (~25% of original)
ffmpeg -y -i input.mp4 ^
  -c:v libx264 -crf 35 -preset veryfast ^
  -c:a aac -b:a 64k ^
  -movflags +faststart -f mp4 output.mp4
```

### Resolution downscale

```bash
# 720p CRF 30
ffmpeg -y -i input.mp4 ^
  -c:v libx264 -crf 30 -preset veryfast ^
  -vf "scale=-2:720" ^
  -c:a aac -b:a 96k ^
  -movflags +faststart -f mp4 output.mp4

# 480p CRF 35
ffmpeg -y -i input.mp4 ^
  -c:v libx264 -crf 35 -preset veryfast ^
  -vf "scale=-2:480" ^
  -c:a aac -b:a 64k ^
  -movflags +faststart -f mp4 output.mp4
```

## Real-world compression scenarios

| Scenario | Expected size | Best approach |
|---|---|---|
| Short clip (< 5 min, 1080p) | ~50-150 MB | `h264_mf` bitrate target → 1 pass |
| Medium video (5-15 min, 1080p) | ~150-500 MB | `libx264 -crf 28` or `h264_mf` |
| Long video (> 15 min, 1080p) | > 500 MB | Skip compression (too slow) → save to disk |
| 2 GB file, 55 min | Massive | Do NOT attempt CPU compression. HW could do it but NVENC broken. |

## CompressO project context

The user explored [CompressO](https://github.com/codeforreal1/compressO) as a GUI alternative. It's a Tauri (Rust + React) desktop app that wraps FFmpeg, pngquant, jpegoptim, etc. Key features:
- Video/audio compression via FFmpeg
- Trim/split
- Batch compression
- Subtitle embedding
- Metadata editing

**Decision**: FFmpeg CLI was chosen for automation (integrated into dlv_tg.py). CompressO GUI is available for manual use but doesn't integrate with the download pipeline.

## Telegram size estimation by resolution & duration

Rough guide for H264 at CRF 28-30:

| Resolution | 5 min | 15 min | 30 min | 60 min |
|---|---|---|---|---|
| 1080p | ~80 MB | ~250 MB | ~500 MB | ~1 GB |
| 720p | ~40 MB | ~120 MB | ~250 MB | ~500 MB |
| 480p | ~20 MB | ~60 MB | ~120 MB | ~250 MB |
| 360p | ~10 MB | ~30 MB | ~60 MB | ~120 MB |

Any file > 48 MB needs compression or disk fallback. Videos over 30 min at 1080p are unlikely to fit under 48 MB even after aggressive compression — skip and recommend Telegram Desktop.

## Authoring note

This reference was created alongside the FFmpeg compression integration in `dlv_tg.py` (2026-07-11). The key discovery was that NVENC and AMF hardware encoders are present in the ffmpeg binary but do not work on this Windows machine, while `h264_mf` (MediaFoundation) works well at ~20x realtime speed.
