#!/usr/bin/env bash
# Nơi bình yên media pipeline (PRD NBY-09 AC02, §7.6). Runs on the admin's own machine with ffmpeg only;
# it never uploads anything. Turns owner-made assets into app-ready files:
#   -v  an externally generated AI video -> seamless loop (last xf seconds dissolve into the head),
#       1080x1920 portrait, 24 fps, soft film grade; H.264 + HEVC without an audio track; poster JPEG.
#       All source metadata (location, device, tool tags) is dropped; a plain AI-origin comment is written.
#   -a  ambient sound -> 60 s loop, EBU R128 -23 LUFS        (app mixes layers at runtime, NBY-06 AC02)
#   -m  licensed music -> 60 s loop, -32 LUFS (sits ~9 LU under the ambience)
# Every output gets a SHA-256 in <id>.manifest-entry.json. Signing, XMP/C2PA and upload are separate steps.
# Usage: nby-media.sh [-v video -g "AI tool"] [-a ambient] [-m music] [-o outdir] [-t 16] [-x 1]
set -euo pipefail

usage() { echo "usage: $0 [-v video -g tool] [-a ambient] [-m music] [-o outdir] [-t seconds] [-x crossfade]" >&2; exit 2; }
die() { echo "nby-media: $*" >&2; exit 2; }

video="" music="" ambient="" tool="" out="./out" target=16 xf=1
while getopts "v:m:a:g:o:t:x:" opt; do
  case "$opt" in
    v) video="$OPTARG" ;; m) music="$OPTARG" ;; a) ambient="$OPTARG" ;; g) tool="$OPTARG" ;;
    o) out="$OPTARG" ;; t) target="$OPTARG" ;; x) xf="$OPTARG" ;;
    *) usage ;;
  esac
done
[[ -n "$video$music$ambient" ]] || usage
[[ "$target" =~ ^[0-9]+([.][0-9]+)?$ && "$xf" =~ ^[0-9]+([.][0-9]+)?$ ]] || die "-t and -x must be numbers"
command -v ffmpeg >/dev/null || die "ffmpeg not found"
preset="${NBY_MEDIA_PRESET:-slow}" # tests use a faster preset; releases keep the default
max_video_bytes=$((200 * 1024 * 1024)) max_audio_bytes=$((50 * 1024 * 1024))
alen=60 axf=3

# ffmpeg -i always exits 1 without an output; its banner is what we parse (ffprobe is not required).
info() { { ffmpeg -hide_banner -i "$1" 2>&1 || true; }; }
duration() { info "$1" | sed -n 's/.*Duration: \([0-9:.]*\).*/\1/p' | head -1 \
  | awk -F: 'NF == 3 { printf "%.3f", $1*3600 + $2*60 + $3 }'; }
bytes() { wc -c < "$1" | tr -d ' '; }
sha() { if command -v sha256sum >/dev/null; then sha256sum "$1"; else shasum -a 256 "$1"; fi | cut -d' ' -f1; }
# Output names and JSON values only ever contain [A-Za-z0-9._-] (or spaces for the tool label).
safe_id() { local b; b="$(basename "${1%.*}")"; b="$(printf '%s' "$b" | LC_ALL=C tr -c 'A-Za-z0-9._-' '_')"; printf '%s' "${b:-asset}"; }
need_file() { [[ -f "$1" ]] || die "not a file: $1"; }

check_video() {
  local f="$1" d codec
  need_file "$f"
  (( $(bytes "$f") <= max_video_bytes )) || die "video over 200 MB: $f"
  codec="$(info "$f" | sed -n 's/.*Stream #[^:]*:[^:]*: Video: \([a-z0-9]*\).*/\1/p' | head -1)"
  case "$codec" in h264 | hevc | prores) ;; *) die "video codec must be h264, hevc or prores (got '${codec:-none}'): $f" ;; esac
  d="$(duration "$f")"
  [[ -n "$d" ]] || die "cannot read duration: $f"
  awk -v d="$d" 'BEGIN { exit !(d >= 8 && d <= 30) }' || die "video must be 8-30 s (got ${d}s): $f"
}

check_audio() {
  local f="$1"
  need_file "$f"
  (( $(bytes "$f") <= max_audio_bytes )) || die "audio over 50 MB: $f"
  info "$f" | grep -q 'Stream #.*: Audio:' || die "no audio stream: $f"
}

[[ -z "$video" ]] || { check_video "$video"; [[ -n "$tool" ]] || die "-g <AI tool name> is required with -v (AI label, PRD §8.5)"; }
[[ -z "$ambient" ]] || check_audio "$ambient"
[[ -z "$music" ]] || check_audio "$music"
tool="$(printf '%s' "$tool" | LC_ALL=C tr -c 'A-Za-z0-9 ._-' '_' | cut -c1-64)"
mkdir -p "$out"
entries=()

if [[ -n "$video" ]]; then
  id="$(safe_id "$video")"
  len="$(awk -v a="$(duration "$video")" -v b="$target" 'BEGIN { printf "%.3f", (a < b ? a : b) }')"
  offset="$(awk -v l="$len" -v x="$xf" 'BEGIN { printf "%.3f", l - 2*x }')"
  awk -v o="$offset" 'BEGIN { exit !(o > 0) }' || die "video too short for a ${xf}s crossfade"
  label="AI-generated (trainedAlgorithmicMedia); tool=${tool}; processed by la-lanh nby-media"
  grade="scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=24,\
eq=contrast=0.94:saturation=0.9:gamma=1.04,curves=all='0/0.05 0.5/0.52 1/0.97',\
colorbalance=rs=0.03:gs=0.01:bs=-0.03:rm=0.02:bm=-0.02,setsar=1,format=yuv420p"
  # Loop: body = source[xf, len); its last xf seconds dissolve into source[0, xf), so the output
  # ends on the frame just before source[xf], which is where it starts again.
  loop="[0:v]trim=0:${len},setpts=PTS-STARTPTS,${grade},split[a][b];\
[a]trim=start=${xf},setpts=PTS-STARTPTS,fps=24[body];[b]trim=0:${xf},setpts=PTS-STARTPTS,fps=24[head];\
[body][head]xfade=transition=fade:duration=${xf}:offset=${offset}[v]"
  ffmpeg -hide_banner -loglevel error -y -i "$video" -filter_complex "$loop" -map "[v]" -an -sn -dn \
    -map_metadata -1 -map_chapters -1 -metadata comment="$label" \
    -c:v libx264 -preset "$preset" -crf 23 -profile:v high -pix_fmt yuv420p -movflags +faststart "$out/$id.h264.mp4"
  ffmpeg -hide_banner -loglevel error -y -i "$out/$id.h264.mp4" -map 0:v -an -map_metadata -1 -metadata comment="$label" \
    -c:v libx265 -preset "$preset" -crf 27 -x265-params log-level=error -tag:v hvc1 -pix_fmt yuv420p \
    -movflags +faststart "$out/$id.hevc.mp4"
  ffmpeg -hide_banner -loglevel error -y -i "$out/$id.h264.mp4" -frames:v 1 -map_metadata -1 -q:v 3 "$out/$id.poster.jpg"
  entries+=("$(printf '"video": { "id": "%s", "loop_seconds": %s,\n    "ai_label": { "tool": "%s", "digital_source_type": "trainedAlgorithmicMedia" },\n    "src_h264": "%s", "sha256_h264": "%s",\n    "src_hevc": "%s", "sha256_hevc": "%s",\n    "poster": "%s", "sha256_poster": "%s" }' \
    "$id" "$(duration "$out/$id.h264.mp4")" "$tool" \
    "$id.h264.mp4" "$(sha "$out/$id.h264.mp4")" "$id.hevc.mp4" "$(sha "$out/$id.hevc.mp4")" \
    "$id.poster.jpg" "$(sha "$out/$id.poster.jpg")")")
fi

# One audio layer -> a seamless loop: a fixed-length, loudness-normalised WAV, then its tail crossfades
# into its head (two inputs of the same file; asplit + acrossfade on one input stalls).
audio_loop() {
  local in="$1" lufs="$2" kind="$3" id wav dst
  id="$(safe_id "$in")"; wav="$out/.$id.$kind.wav"; dst="$out/$id.$kind.m4a"
  ffmpeg -hide_banner -loglevel error -y -stream_loop -1 -i "$in" -vn -t $((alen + axf)) \
    -af "loudnorm=I=${lufs}:TP=-2:LRA=7,aresample=48000,aformat=channel_layouts=stereo" -c:a pcm_s16le "$wav"
  ffmpeg -hide_banner -loglevel error -y -i "$wav" -i "$wav" -filter_complex \
    "[0:a]atrim=start=${axf},asetpts=PTS-STARTPTS[body];[1:a]atrim=0:${axf},asetpts=PTS-STARTPTS[head];\
[body][head]acrossfade=d=${axf}:c1=tri:c2=tri[a]" -map "[a]" \
    -map_metadata -1 -c:a aac -b:a 128k -movflags +faststart "$dst"
  rm -f "$wav"
  entries+=("$(printf '"%s": { "id": "%s", "src": "%s", "sha256": "%s", "loudness_lufs": %s, "loop_seconds": %s }' \
    "$kind" "$id" "$(basename "$dst")" "$(sha "$dst")" "$lufs" "$(duration "$dst")")")
}
[[ -z "$ambient" ]] || audio_loop "$ambient" -23 ambient
[[ -z "$music" ]] || audio_loop "$music" -32 music

manifest_id="$(safe_id "${video:-${ambient:-$music}}")"
{
  printf '{\n'
  for i in "${!entries[@]}"; do
    printf '  %s%s\n' "${entries[$i]}" "$([[ $i -lt $((${#entries[@]} - 1)) ]] && echo , || true)"
  done
  printf '}\n'
} > "$out/$manifest_id.manifest-entry.json"
echo "done: $out/$manifest_id.manifest-entry.json"
