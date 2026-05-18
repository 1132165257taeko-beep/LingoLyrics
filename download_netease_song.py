import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Dict, List


LYRIC_URL = "https://music.163.com/api/song/lyric?id={song_id}&lv=1&kv=1&tv=-1"
SONG_DETAIL_URL = "https://music.163.com/api/song/detail/?id={song_id}&ids=%5B{song_id}%5D"
AUDIO_URL = "http://music.163.com/song/media/outer/url?id={song_id}.mp3"


def extract_song_id(value: str) -> str:
    match = re.search(r"id=(\d+)", value)
    if match:
        return match.group(1)

    match = re.search(r"\b(\d{5,})\b", value)
    if match:
        return match.group(1)

    raise ValueError("No NetEase song id found.")


def read_id_file(path: Path) -> str:
    text = path.read_text(encoding="utf-8-sig")
    return extract_song_id(text)


def prompt_song_id() -> str:
    while True:
        value = input("Enter NetEase song id or song URL: ").strip()
        if not value:
            print("Please enter a song id or a URL containing id=...")
            continue
        try:
            return extract_song_id(value)
        except ValueError as exc:
            print(f"{exc} Try again.")


def request_url(url: str, timeout: int = 30) -> bytes:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0 Safari/537.36"
            ),
            "Referer": "https://music.163.com/",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def load_json_url(url: str, timeout: int = 30) -> Dict:
    raw = request_url(url, timeout=timeout)
    try:
        data = json.loads(raw.decode("utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Response is not JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise RuntimeError("JSON response is not an object.")
    return data


def fetch_song_title(song_id: str) -> str:
    try:
        data = load_json_url(SONG_DETAIL_URL.format(song_id=song_id))
    except (urllib.error.URLError, urllib.error.HTTPError, RuntimeError, OSError):
        return ""

    songs = data.get("songs")
    if isinstance(songs, list) and songs and isinstance(songs[0], dict):
        name = songs[0].get("name")
        if isinstance(name, str):
            return name.strip()
    return ""


def sanitize_folder_name(value: str) -> str:
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", value).strip()
    name = name.rstrip(". ")
    return name or "歌曲"


def parse_lrc_pairs(text: str) -> Dict[str, str]:
    pairs: Dict[str, str] = {}
    for raw_line in text.splitlines():
        match = re.match(r"^\[(\d{2}:\d{2}\.\d{2,3})\](.*)$", raw_line.strip())
        if not match:
            continue
        timestamp, value = match.groups()
        value = value.strip()
        if not value or value.startswith("by:"):
            continue
        pairs[timestamp] = value
    return pairs


def extract_credit_lines(lrc_lines: Dict[str, str]) -> List[str]:
    credits: List[str] = []
    for value in lrc_lines.values():
        if value.startswith("作词") or value.startswith("作曲"):
            normalized = value.replace(" : ", ": ").replace("：", ": ")
            credits.append(normalized)
    return credits[:2]


def build_translation_lines(song_title: str, subtitle: str, lyric_data: Dict) -> List[str]:
    lrc = lyric_data.get("lrc")
    tlyric = lyric_data.get("tlyric")
    if not isinstance(lrc, dict) or not isinstance(lrc.get("lyric"), str):
        raise RuntimeError("Lyric JSON does not contain 'lrc.lyric'.")
    if not isinstance(tlyric, dict) or not isinstance(tlyric.get("lyric"), str) or not tlyric["lyric"].strip():
        raise RuntimeError("Lyric JSON does not contain translated lyrics in 'tlyric.lyric'.")

    lrc_lines = parse_lrc_pairs(lrc["lyric"])
    translation_lines = parse_lrc_pairs(tlyric["lyric"])
    if not lrc_lines:
        raise RuntimeError("No timed lyric lines found in 'lrc.lyric'.")
    if not translation_lines:
        raise RuntimeError("No timed translated lyric lines found in 'tlyric.lyric'.")

    title = song_title or "歌曲名"
    output: List[str] = [title, subtitle or title]
    credits = extract_credit_lines(lrc_lines)
    output.extend(credits)
    while len(output) < 4:
        output.append("")

    pair_count = 0
    for timestamp, lyric_line in lrc_lines.items():
        if lyric_line.startswith("作词") or lyric_line.startswith("作曲"):
            continue
        translated_line = translation_lines.get(timestamp)
        if translated_line is None:
            continue
        output.append(lyric_line)
        output.append(translated_line)
        pair_count += 1

    if pair_count == 0:
        raise RuntimeError("No matching timestamp pairs found between lyric and translation.")
    return output


def write_translation_file(
    song_id: str,
    lyric_data: Dict,
    output_path: Path,
    overwrite: bool,
    song_title: str = "",
) -> None:
    if output_path.exists() and not overwrite:
        print(f"Skip existing translation: {output_path}")
        return

    title = song_title or fetch_song_title(song_id)
    lines = build_translation_lines(title, title, lyric_data)
    output_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(f"Wrote translation: {output_path}")


def download_lyric(song_id: str, output_path: Path, overwrite: bool) -> Dict:
    if output_path.exists() and not overwrite:
        print(f"Skip existing lyric: {output_path}")
        return load_existing_lyric(output_path)

    data = load_json_url(LYRIC_URL.format(song_id=song_id))
    if not isinstance(data.get("lrc"), dict) and "lyric" not in data:
        raise RuntimeError("Lyric JSON does not contain lyric data.")

    output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote lyric: {output_path}")
    return data


def load_existing_lyric(path: Path) -> Dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Existing lyric file is not JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise RuntimeError("Existing lyric file is not a JSON object.")
    return data


def download_audio(song_id: str, output_path: Path, overwrite: bool) -> None:
    if output_path.exists() and not overwrite:
        print(f"Skip existing audio: {output_path}")
        return

    raw = request_url(AUDIO_URL.format(song_id=song_id), timeout=60)
    if len(raw) < 1024:
        preview = raw[:200].decode("utf-8", errors="replace")
        raise RuntimeError(f"Audio response is unexpectedly small. Preview: {preview!r}")

    output_path.write_bytes(raw)
    print(f"Wrote audio: {output_path}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Download NetEase lyric timeline JSON and audio by song id."
    )
    parser.add_argument(
        "song_id",
        nargs="?",
        help="NetEase song id, or a URL containing id=...",
    )
    parser.add_argument(
        "--id-file",
        type=Path,
        help="Read the song id from a text file such as 歌曲目录/id.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        help="Output folder. Defaults to a folder named after the song title.",
    )
    parser.add_argument(
        "--lyric-name",
        default="时间轴.json",
        help="Output lyric timeline filename. Defaults to 时间轴.json.",
    )
    parser.add_argument(
        "--audio-name",
        default="音频.mp3",
        help="Output audio filename. Defaults to 音频.mp3.",
    )
    parser.add_argument(
        "--translation-name",
        default="歌词翻译",
        help="Output paired lyric+translation filename. Defaults to 歌词翻译.",
    )
    parser.add_argument(
        "--skip-audio",
        action="store_true",
        help="Only download the lyric timeline JSON.",
    )
    parser.add_argument(
        "--skip-lyric",
        action="store_true",
        help="Only download the audio file.",
    )
    parser.add_argument(
        "--skip-translation",
        action="store_true",
        help="Do not write 歌词翻译 from NetEase translated lyrics.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing output files.",
    )
    args = parser.parse_args()

    try:
        if args.id_file:
            song_id = read_id_file(args.id_file)
        elif args.song_id:
            song_id = extract_song_id(args.song_id)
        else:
            song_id = prompt_song_id()
    except ValueError as exc:
        parser.error(str(exc))

    song_title = fetch_song_title(song_id)
    if args.out:
        output_dir = args.out.expanduser().resolve()
    else:
        output_dir = Path(sanitize_folder_name(song_title or song_id)).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Song id: {song_id}")
    print(f"Title: {song_title or '(unknown)'}")
    print(f"Output: {output_dir}")

    try:
        if not args.skip_lyric:
            lyric_data = download_lyric(song_id, output_dir / args.lyric_name, args.overwrite)
            if not args.skip_translation:
                try:
                    write_translation_file(
                        song_id,
                        lyric_data,
                        output_dir / args.translation_name,
                        args.overwrite,
                        song_title=song_title,
                    )
                except RuntimeError as exc:
                    print(f"Warning: could not write translation: {exc}", file=sys.stderr)
        if not args.skip_audio:
            download_audio(song_id, output_dir / args.audio_name, args.overwrite)
    except (urllib.error.URLError, urllib.error.HTTPError, RuntimeError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
