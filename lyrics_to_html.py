import argparse
import html
import json
import re
from pathlib import Path
from typing import Any, Dict, List


NOTE_MARKS = tuple(chr(code) for code in range(0x2460, 0x2469 + 1))
TIMELINE_METADATA_PREFIXES = (
    "by:",
    "作词",
    "作曲",
    "编曲",
    "編曲",
    "词:",
    "曲:",
    "詞:",
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def parse_markdown(md_text: str) -> Dict[str, Any]:
    blocks = [b.strip() for b in re.split(r"(?m)^---\s*$", md_text) if b.strip()]
    if not blocks:
        raise ValueError("Markdown file is empty or has no lyric blocks.")

    header_lines = [
        line.strip()
        for line in blocks[0].splitlines()
        if line.strip() and not line.strip().startswith("<!--")
    ]

    lyric_blocks: List[Dict[str, Any]] = []
    for block in blocks[1:]:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if len(lines) < 2:
            continue

        japanese = lines[0]
        romaji = lines[1]
        translation = ""
        note_start = 2
        if len(lines) > 2 and not lines[2].startswith(NOTE_MARKS):
            translation = lines[2]
            note_start = 3

        notes = [line for line in lines[note_start:] if line.startswith(NOTE_MARKS)]
        lyric_blocks.append(
            {
                "japanese": japanese,
                "romaji": romaji,
                "translation": translation,
                "notes": notes,
            }
        )

    title = header_lines[0] if header_lines else "滚动歌词"
    subtitle = " / ".join(header_lines[1:4]) if len(header_lines) > 1 else ""
    return {"title": title, "subtitle": subtitle, "blocks": lyric_blocks}


def parse_lrc_time(minutes: str, seconds: str, fraction: str) -> float:
    frac = fraction[:3].ljust(3, "0")
    return int(minutes) * 60 + int(seconds) + int(frac) / 1000


def extract_lrc_text(timeline_text: str) -> str:
    stripped = timeline_text.strip()
    if not stripped:
        return ""

    try:
        data = json.loads(stripped)
    except json.JSONDecodeError:
        return timeline_text

    if isinstance(data, dict):
        if isinstance(data.get("lyric"), str):
            return data["lyric"]
        if isinstance(data.get("lrc"), dict) and isinstance(data["lrc"].get("lyric"), str):
            return data["lrc"]["lyric"]
    if isinstance(data, list):
        lines = []
        for item in data:
            if isinstance(item, dict) and "time" in item and "text" in item:
                total = float(item["time"])
                minutes = int(total // 60)
                seconds = int(total % 60)
                millis = int(round((total - int(total)) * 1000))
                lines.append(f"[{minutes:02d}:{seconds:02d}.{millis:03d}]{item['text']}")
        return "\n".join(lines)

    return timeline_text


def parse_timeline(timeline_text: str) -> List[Dict[str, Any]]:
    lrc_text = extract_lrc_text(timeline_text)
    pattern = re.compile(r"^\[(\d{1,2}):(\d{2})[.:](\d{1,3})\](.*)$")
    timeline: List[Dict[str, Any]] = []

    for line in lrc_text.splitlines():
        match = pattern.match(line.strip())
        if not match:
            continue
        minutes, seconds, fraction, text = match.groups()
        text = text.strip()
        if not text or text.startswith(TIMELINE_METADATA_PREFIXES):
            continue
        timeline.append({"time": parse_lrc_time(minutes, seconds, fraction), "text": text})

    timeline.sort(key=lambda item: item["time"])
    return timeline


def build_items(
    blocks: List[Dict[str, Any]],
    timeline: List[Dict[str, Any]],
    fallback_line_duration: float,
) -> Dict[str, Any]:
    warnings: List[str] = []

    if not timeline:
        items = []
        for index, block in enumerate(blocks):
            start = index * fallback_line_duration
            items.append({**block, "time": start, "end": start + fallback_line_duration})
        return {"items": items, "warnings": ["No timeline found; generated fixed-duration timing."]}

    used = 0
    items: List[Dict[str, Any]] = []
    for index, point in enumerate(timeline):
        found = None
        for block_index in range(used, len(blocks)):
            if blocks[block_index]["japanese"] == point["text"]:
                found = block_index
                break

        if found is None:
            warnings.append(f"Timeline line not found in Markdown: {point['text']}")
            block = {"japanese": point["text"], "romaji": point["text"], "translation": "", "notes": []}
        else:
            if found > used:
                warnings.append(f"Skipped {found - used} Markdown block(s) before: {point['text']}")
            block = blocks[found]
            used = found + 1

        end = timeline[index + 1]["time"] if index + 1 < len(timeline) else point["time"] + fallback_line_duration
        items.append({**block, "time": point["time"], "end": end})

    return {"items": items, "warnings": warnings}


def render_html(data: Dict[str, Any], audio_src: str = "") -> str:
    json_data = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    title = html.escape(data.get("title") or "滚动歌词")
    audio_src_attr = html.escape(audio_src, quote=True)

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{title} - 滚动歌词</title>
<style>
:root {{
  --bg: #f6f3ee; --panel: #fffdfa; --ink: #252525; --muted: #6d6a64;
  --line: #ded8ce; --accent: #c83f3f; --accent-2: #19736b; --shadow: 0 18px 45px rgba(37,37,37,.10);
}}
* {{ box-sizing: border-box; }}
body {{ margin: 0; min-height: 100vh; font-family: "Microsoft YaHei", "Noto Sans SC", system-ui, sans-serif; color: var(--ink); background: var(--bg); }}
.app {{ min-height: 100vh; display: grid; grid-template-rows: auto 1fr auto; }}
header {{ padding: 22px clamp(18px, 4vw, 44px) 14px; border-bottom: 1px solid var(--line); background: rgba(255,253,250,.92); position: sticky; top: 0; z-index: 5; }}
.topbar {{ display: flex; align-items: center; justify-content: space-between; gap: 18px; max-width: 1180px; margin: 0 auto; }}
.title h1 {{ margin: 0; font-size: 24px; line-height: 1.2; letter-spacing: 0; }}
.title p {{ margin: 7px 0 0; color: var(--muted); font-size: 13px; }}
.controls {{ display: flex; align-items: center; gap: 10px; flex-wrap: wrap; justify-content: flex-end; }}
button, .file-label {{ appearance: none; border: 1px solid var(--line); background: var(--panel); color: var(--ink); height: 38px; padding: 0 13px; border-radius: 8px; font: inherit; font-size: 14px; cursor: pointer; display: inline-flex; align-items: center; gap: 7px; }}
button:hover, .file-label:hover {{ border-color: #c9bfb0; }}
button.primary {{ background: var(--accent); color: white; border-color: var(--accent); min-width: 84px; justify-content: center; }}
input[type="file"] {{ display: none; }}
main {{ max-width: 1180px; width: 100%; margin: 0 auto; padding: 22px clamp(14px, 4vw, 44px) 24px; display: grid; grid-template-columns: minmax(0, 1fr) 320px; gap: 20px; min-height: 0; }}
.stage {{ background: var(--panel); border: 1px solid var(--line); border-radius: 8px; box-shadow: var(--shadow); min-height: calc(100vh - 190px); max-height: calc(100vh - 190px); overflow: hidden; position: relative; }}
.lyrics {{ height: 100%; overflow-y: auto; scroll-behavior: smooth; padding: 34vh 34px 36vh; }}
.line {{ max-width: 760px; margin: 0 auto 28px; padding: 16px 18px; border-left: 3px solid transparent; border-radius: 8px; opacity: .48; transform: scale(.985); transition: opacity .22s ease, transform .22s ease, background .22s ease, border-color .22s ease; }}
.line.active {{ opacity: 1; transform: scale(1); background: #fff7f2; border-color: var(--accent); }}
.jp {{ font-size: 24px; line-height: 1.55; font-weight: 700; }}
.line.active .jp {{ font-size: 30px; }}
.aligned-lyrics {{ display: flex; flex-wrap: wrap; justify-content: center; align-items: flex-start; column-gap: 14px; row-gap: 10px; }}
.line.active .aligned-lyrics {{ column-gap: 16px; }}
.word-pair {{ display: inline-flex; flex-direction: column; align-items: center; min-width: max-content; text-align: center; }}
.word-text {{ font-size: 24px; line-height: 1.25; font-weight: 700; }}
.line.active .word-text {{ font-size: 30px; }}
.phonetic {{ margin-top: 3px; color: var(--accent-2); font-size: 15px; line-height: 1.25; font-weight: 500; white-space: nowrap; }}
.line.active .phonetic {{ font-size: 17px; }}
.romaji {{ margin-top: 8px; color: var(--accent-2); font-size: 16px; line-height: 1.55; }}
.romaji strong {{ color: #8b5e27; font-weight: 800; }}
.romaji em {{ color: #8b5e27; font-style: normal;}}
.translation {{ margin-top: 8px; color: #4c4840; font-size: 17px; line-height: 1.55; }}
.notes {{ margin-top: 12px; padding-top: 10px; border-top: 1px solid #eadfd4; color: #5c5147; font-size: 14px; line-height: 1.75; }}
.notes div {{ margin: 3px 0; }}
.side {{ display: flex; flex-direction: column; gap: 14px; }}
.panel {{ background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 16px; }}
.panel h2 {{ margin: 0 0 12px; font-size: 15px; }}
.toggles {{ display: grid; gap: 10px; }}
.toggle {{ display: flex; align-items: center; justify-content: space-between; gap: 12px; font-size: 14px; }}
.switch {{ width: 48px; height: 26px; border-radius: 999px; border: 1px solid #cfc5b7; background: #e8e0d6; position: relative; cursor: pointer; flex: 0 0 auto; }}
.switch::after {{ content: ""; position: absolute; width: 20px; height: 20px; left: 2px; top: 2px; border-radius: 50%; background: white; box-shadow: 0 1px 3px rgba(0,0,0,.20); transition: transform .18s ease; }}
.switch.on {{ background: var(--accent-2); border-color: var(--accent-2); }}
.switch.on::after {{ transform: translateX(22px); }}
.now {{ color: var(--muted); font-size: 13px; line-height: 1.6; }}
.now strong {{ display: block; color: var(--ink); font-size: 18px; margin-bottom: 8px; }}
.current-notes {{ margin-top: 10px; color: #574c43; font-size: 14px; line-height: 1.7; }}
footer {{ border-top: 1px solid var(--line); background: rgba(255,253,250,.96); padding: 13px clamp(18px, 4vw, 44px); }}
.transport {{ max-width: 1180px; margin: 0 auto; display: grid; grid-template-columns: auto auto 1fr auto; align-items: center; gap: 14px; }}
.speed-controls {{ display: inline-flex; align-items: center; gap: 4px; border: 1px solid var(--line); border-radius: 8px; padding: 3px; background: var(--panel); }}
.speed-btn {{ height: 30px; min-width: 44px; padding: 0 8px; border: 0; border-radius: 6px; background: transparent; font-size: 13px; justify-content: center; }}
.speed-btn.active {{ background: var(--accent-2); color: white; }}
.time {{ color: var(--muted); font-variant-numeric: tabular-nums; font-size: 13px; min-width: 102px; text-align: right; }}
.progress {{ width: 100%; accent-color: var(--accent); }}
body.hide-romaji .romaji, body.hide-translation .translation, body.hide-notes .notes {{ display: none; }}
body.hide-romaji .phonetic {{ display: none; }}
@media (max-width: 860px) {{ .topbar {{ align-items: flex-start; flex-direction: column; }} .controls {{ justify-content: flex-start; }} main {{ grid-template-columns: 1fr; }} .stage {{ min-height: 58vh; max-height: 58vh; }} .lyrics {{ padding-left: 16px; padding-right: 16px; }} .line {{ padding: 14px; margin-bottom: 20px; }} .jp, .word-text {{ font-size: 21px; }} .line.active .jp, .line.active .word-text {{ font-size: 24px; }} .transport {{ grid-template-columns: auto 1fr; }} .speed-controls {{ grid-column: 1 / -1; width: max-content; }} .time {{ grid-column: 1 / -1; text-align: left; }} }}
</style>
</head>
<body>
<div class="app">
<header><div class="topbar"><div class="title"><h1 id="songTitle"></h1><p id="songSubtitle"></p></div><div class="controls"><label class="file-label" title="选择本地音频文件">音频<input id="audioFile" type="file" accept="audio/*" /></label><button id="resetBtn" title="回到开头">重置</button></div></div></header>
<main><section class="stage" aria-label="滚动歌词"><div id="lyrics" class="lyrics"></div></section><aside class="side"><section class="panel"><h2>显示</h2><div class="toggles"><div class="toggle"><span>罗马音</span><span class="switch on" data-toggle="romaji" role="button" tabindex="0" title="显示或隐藏罗马音"></span></div><div class="toggle"><span>中文翻译</span><span class="switch on" data-toggle="translation" role="button" tabindex="0" title="显示或隐藏中文翻译"></span></div><div class="toggle"><span>行内注释</span><span class="switch on" data-toggle="notes" role="button" tabindex="0" title="显示或隐藏每行注释"></span></div><div class="toggle"><span>侧栏注释</span><span class="switch on" data-toggle="sideNotes" role="button" tabindex="0" title="显示或隐藏当前行注释"></span></div></div></section><section class="panel now"><strong>当前行</strong><div id="currentText"></div><div id="currentNotes" class="current-notes"></div></section></aside></main>
<footer><div class="transport"><button id="playBtn" class="primary" title="播放或暂停">播放</button><div class="speed-controls" aria-label="播放速度"><button class="speed-btn" data-speed="0.5" title="0.5 倍速">0.5x</button><button class="speed-btn" data-speed="0.75" title="0.75 倍速">0.75x</button><button class="speed-btn active" data-speed="1" title="正常速度">1x</button></div><input id="progress" class="progress" type="range" min="0" max="1000" value="0" title="拖动调整播放进度" /><div id="time" class="time">00:00 / 00:00</div></div></footer>
</div><audio id="audio" src="{audio_src_attr}"></audio><script id="lyric-data" type="application/json">{json_data}</script>
<script>
const DATA = JSON.parse(document.getElementById('lyric-data').textContent);
const lyricsEl = document.getElementById('lyrics'), audio = document.getElementById('audio'), playBtn = document.getElementById('playBtn'), progress = document.getElementById('progress'), timeEl = document.getElementById('time'), currentText = document.getElementById('currentText'), currentNotes = document.getElementById('currentNotes'), audioFile = document.getElementById('audioFile'), resetBtn = document.getElementById('resetBtn');
let simulatedTime = 0, lastTick = 0, playing = false, activeIndex = -1, useAudio = Boolean(audio.getAttribute('src')), showSideNotes = true, playbackRate = 1;
const duration = DATA.duration || 1;
document.getElementById('songTitle').textContent = DATA.title;
document.getElementById('songSubtitle').textContent = DATA.subtitle || '滚动歌词学习页';
function escapeHtml(value) {{ return String(value).replace(/[&<>"']/g, ch => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[ch])); }}
function renderInlineMarkdown(value) {{
  return escapeHtml(value)
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/(^|[^*])\*([^*]+)\*/g, '$1<em>$2</em>');
}}
function splitPhoneticGroups(value) {{
  const text = String(value || '').trim();
  if (!text) return [];
  const groups = text.match(/\[[^\]]+\]/g) || [];
  return groups.length && groups.join(' ') === text ? groups : [];
}}
function renderLyricMain(item) {{
  const words = String(item.japanese || '').trim().split(/\s+/).filter(Boolean);
  const phonetics = splitPhoneticGroups(item.romaji);
  if (words.length && words.length === phonetics.length) {{
    const pairs = words.map((word, wordIndex) => `<span class="word-pair"><span class="word-text">${{escapeHtml(word)}}</span><span class="phonetic">${{escapeHtml(phonetics[wordIndex])}}</span></span>`).join('');
    return `<div class="aligned-lyrics">${{pairs}}</div>`;
  }}
  return `<div class="jp">${{escapeHtml(item.japanese)}}</div><div class="romaji">${{renderInlineMarkdown(item.romaji || '')}}</div>`;
}}
function renderLyrics() {{ lyricsEl.innerHTML = DATA.items.map((item, index) => `<article class="line" data-index="${{index}}">${{renderLyricMain(item)}}<div class="translation">${{escapeHtml(item.translation || '')}}</div><div class="notes">${{(item.notes || []).map(note => `<div>${{escapeHtml(note)}}</div>`).join('')}}</div></article>`).join(''); }}
function formatTime(value) {{ const safe = Math.max(0, value || 0), minutes = Math.floor(safe / 60), seconds = Math.floor(safe % 60); return `${{String(minutes).padStart(2, '0')}}:${{String(seconds).padStart(2, '0')}}`; }}
function getCurrentTime() {{ return useAudio ? audio.currentTime : simulatedTime; }}
function getDuration() {{ return useAudio && Number.isFinite(audio.duration) && audio.duration > 0 ? audio.duration : duration; }}
function setCurrentTime(value) {{ const clamped = Math.max(0, Math.min(value, getDuration())); if (useAudio) audio.currentTime = clamped; simulatedTime = clamped; update(); }}
function findActiveIndex(time) {{ let lo = 0, hi = DATA.items.length - 1, result = 0; while (lo <= hi) {{ const mid = Math.floor((lo + hi) / 2); if (DATA.items[mid].time <= time) {{ result = mid; lo = mid + 1; }} else hi = mid - 1; }} return result; }}
function setActive(index) {{ if (index === activeIndex) return; const prev = lyricsEl.querySelector('.line.active'); if (prev) prev.classList.remove('active'); const next = lyricsEl.querySelector(`.line[data-index="${{index}}"]`); if (next) {{ next.classList.add('active'); next.scrollIntoView({{ behavior: 'smooth', block: 'center' }}); }} activeIndex = index; const item = DATA.items[index]; currentText.textContent = item ? item.japanese : ''; currentNotes.innerHTML = showSideNotes && item ? (item.notes || []).map(escapeHtml).join('<br>') : ''; }}
function update() {{ const now = getCurrentTime(), total = getDuration(); progress.value = total > 0 ? Math.round((now / total) * 1000) : 0; timeEl.textContent = `${{formatTime(now)}} / ${{formatTime(total)}}`; if (DATA.items.length) setActive(findActiveIndex(now)); }}
function tick(stamp) {{ if (!lastTick) lastTick = stamp; const delta = (stamp - lastTick) / 1000; lastTick = stamp; if (playing && !useAudio) {{ simulatedTime += delta * playbackRate; if (simulatedTime >= duration) {{ simulatedTime = duration; playing = false; playBtn.textContent = '播放'; }} update(); }} requestAnimationFrame(tick); }}
playBtn.addEventListener('click', async () => {{ if (useAudio) {{ if (audio.paused) await audio.play(); else audio.pause(); return; }} playing = !playing; playBtn.textContent = playing ? '暂停' : '播放'; }});
audio.addEventListener('play', () => {{ playing = true; playBtn.textContent = '暂停'; }}); audio.addEventListener('pause', () => {{ playing = false; playBtn.textContent = '播放'; }}); audio.addEventListener('timeupdate', update); audio.addEventListener('loadedmetadata', update);
audioFile.addEventListener('change', () => {{ const file = audioFile.files && audioFile.files[0]; if (!file) return; audio.src = URL.createObjectURL(file); audio.playbackRate = playbackRate; useAudio = true; simulatedTime = 0; activeIndex = -1; playBtn.textContent = '播放'; update(); }});
progress.addEventListener('input', () => setCurrentTime((Number(progress.value) / 1000) * getDuration()));
resetBtn.addEventListener('click', () => {{ if (useAudio) audio.pause(); playing = false; playBtn.textContent = '播放'; setCurrentTime(0); }});
document.querySelectorAll('.speed-btn').forEach(btn => {{ btn.addEventListener('click', () => {{ playbackRate = Number(btn.dataset.speed) || 1; audio.playbackRate = playbackRate; document.querySelectorAll('.speed-btn').forEach(item => item.classList.toggle('active', item === btn)); }}); }});
document.querySelectorAll('.switch').forEach(sw => {{ const toggle = () => {{ sw.classList.toggle('on'); const key = sw.dataset.toggle, visible = sw.classList.contains('on'); if (key === 'romaji') document.body.classList.toggle('hide-romaji', !visible); if (key === 'translation') document.body.classList.toggle('hide-translation', !visible); if (key === 'notes') document.body.classList.toggle('hide-notes', !visible); if (key === 'sideNotes') {{ showSideNotes = visible; activeIndex = -1; update(); }} }}; sw.addEventListener('click', toggle); sw.addEventListener('keydown', event => {{ if (event.key === 'Enter' || event.key === ' ') {{ event.preventDefault(); toggle(); }} }}); }});
renderLyrics(); update(); requestAnimationFrame(tick);
</script></body></html>"""


def default_path(folder: Path, filename: str) -> Path:
    return folder / filename


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a single-file scrolling lyrics HTML page.")
    parser.add_argument("folder", nargs="?", default=".", help="Song folder. Defaults to current directory.")
    parser.add_argument("--md", help="Formatted lyrics Markdown path. Defaults to <folder>/歌词_格式化.md.")
    parser.add_argument("--timeline", help="Timeline JSON/LRC path. Defaults to <folder>/时间轴.json.")
    parser.add_argument("--output", help="Output HTML path. Defaults to <folder>/滚动歌词.html.")
    parser.add_argument("--audio", help="Audio file path to embed. Defaults to <folder>/音频.mp3 if it exists.")
    parser.add_argument("--line-duration", type=float, default=4.0, help="Fallback seconds per line when timeline is missing.")
    args = parser.parse_args()

    folder = Path(args.folder).expanduser().resolve()
    md_path = Path(args.md).expanduser().resolve() if args.md else default_path(folder, "歌词_格式化.md")
    timeline_path = Path(args.timeline).expanduser().resolve() if args.timeline else default_path(folder, "时间轴.json")
    output_path = Path(args.output).expanduser().resolve() if args.output else default_path(folder, "滚动歌词.html")
    audio_path = Path(args.audio).expanduser().resolve() if args.audio else default_path(folder, "音频.mp3")

    markdown = parse_markdown(read_text(md_path))
    timeline_text = read_text(timeline_path) if timeline_path.exists() else ""
    timeline = parse_timeline(timeline_text)
    built = build_items(markdown["blocks"], timeline, args.line_duration)

    duration = built["items"][-1]["end"] if built["items"] else 0
    data = {
        "title": markdown["title"],
        "subtitle": markdown["subtitle"],
        "items": built["items"],
        "duration": duration,
        "warnings": built["warnings"],
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    audio_src = ""
    if audio_path.exists():
        try:
            audio_src = audio_path.relative_to(output_path.parent).as_posix()
        except ValueError:
            audio_src = audio_path.as_uri()

    output_path.write_text(render_html(data, audio_src=audio_src), encoding="utf-8")

    note_count = sum(len(item.get("notes", [])) for item in built["items"])
    print(f"Wrote: {output_path}")
    print(f"Lines: {len(built['items'])}")
    print(f"Notes: {note_count}")
    print(f"Warnings: {len(built['warnings'])}")
    print(f"Audio: {audio_src or '(none)'}")
    for warning in built["warnings"][:10]:
        print(f"WARNING: {warning}")
    return 0 if not built["warnings"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
