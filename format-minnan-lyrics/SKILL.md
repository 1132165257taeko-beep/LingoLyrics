---
name: format-minnan-lyrics
description: "Format Minnan/Hokkien song lyrics for Mandarin-speaking learners from a Minnan lyrics + Chinese translation file, optionally with a Minnan lyrics + romanization file. Use when Codex needs to align lyric lines, generate or align romanization using the Minnan Phonetic Scheme / Bbánlám pìngyīm rather than POJ or Tailo, and add concise Simplified Chinese notes only for words or expressions that are difficult for native Mandarin speakers to understand."
---

# Format Minnan Lyrics

## Goal

Create a study-ready Markdown lyric sheet from one or two source files:

- `lyrics + translation`: alternating Minnan lyric line and Simplified Chinese translation line, with optional title/credit header.
- Optional `lyrics + romanization`: alternating Minnan lyric line and Minnan Phonetic Scheme romanization line, with the same optional title/credit header.

The final output should match this block pattern:

```markdown
Title line(s)
Credit line(s)

---

Minnan lyric line
Minnan Phonetic Scheme line
Chinese translation line
①词或短语（闽拼）：简短解释；只解释普通话母语者可能难懂的点。
---
```

## Workflow

1. Read the translation input file, optional romanization input file, and desired output path from the user. If paths are omitted, infer common names such as `歌词翻译`, optional `歌词闽拼`, and `歌词_格式化.md` in the current song folder.
2. Preserve the header from the translation file: song title, artist/title variant, lyricist, composer, dialect/source notes, or other non-paired metadata.
3. Each output block must contain Minnan lyric, Minnan Phonetic Scheme romanization, Chinese translation, then optional notes.
4. If a romanization file exists, align body lines by the Minnan lyric line.
5. If no romanization file exists, generate romanization yourself using the Minnan Phonetic Scheme / Bbánlám pìngyīm. Do not use POJ or Tailo spelling unless the user explicitly asks.
6. Generate a best-effort romanization directly. Use `[读音待确认]` only for isolated words whose reading is genuinely uncertain; if uncertainty affects many lines, ask the user instead of marking every line.
7. If alignment is uncertain, use `scripts/build_lyrics_skeleton.py` to generate a skeleton and inspect warnings before adding notes.
8. Add annotations in Simplified Chinese using the guidance in `references/annotation-guidelines.md`.
9. Separate every lyric block with `---`. Keep repeated chorus blocks repeated; do not collapse them unless the user asks.
10. Save as Markdown. Prefer the user's requested filename; otherwise use `歌词_格式化.md` in the song folder.

## Non-Minnan Spoken Lines

For Mandarin narration or other non-Minnan spoken lyric lines that should not receive Minnan romanization, translation, or notes, still write a two-line block so downstream tools can align it with the timeline:

```markdown
---

鸟在飞行间鸣叫
（普通话）

---
```

Use `（普通话）` for Mandarin lines. Use a similarly short parenthesized label only when the source line is clearly another language or function, such as `（英语）` or `（音效）`.

## Romanization Rules

- Use Minnan Phonetic Scheme / Bbánlám pìngyīm as the default romanization system.
- Use tone numbers after syllables when confident. For a draft without reliable tone confidence, omit tone numbers consistently rather than marking every line uncertain.
- Preserve supplied romanization exactly when a trusted romanization file is provided, except for obvious spacing cleanup.
- Keep syllables separated by spaces. Keep multi-syllable words readable as spaced syllables, not fused strings.
- Preserve English, Mandarin, Japanese, or other non-Minnan words in their original script unless the source or user asks for a Minnan reading.
- For literary/vernacular reading choices, pick the sung or contextually likely reading. Mark only genuinely uncertain isolated cases.
- Do not mix systems in one file. Avoid POJ/Tailo markers such as `ch`, `ts`, `oo`, `nn`, or diacritics unless they appear in a source line that must be preserved.

## Formatting Rules

- Keep the original Minnan lyric text exactly as supplied unless the user explicitly asks to correct text or encoding.
- Put the Chinese translation immediately after the romanization line.
- Use numbered annotations `①`, `②`, `③` in order. Usually 0-3 notes per line is enough.
- Put each annotation on its own line. Do not join multiple numbered notes into one paragraph.
- For transparent lines that a Mandarin speaker can understand from the translation, output no forced annotation.
- For simple repeated interjections such as `啊`, `喔`, `Hey`, or `La`, output the line pair and separator without forced annotations unless the pronunciation or usage is notable.
- For Mandarin lines, use `（普通话）` as the second line and do not add a translation or notes unless the user requests them.
- Keep annotations concise and objective. Avoid long literary commentary unless the user requests interpretation.

## Annotation Priorities

Read `references/annotation-guidelines.md` when writing or revising notes. In short:

- Explain only words, expressions, particles, grammar, or cultural references that are likely difficult for native Mandarin speakers.
- Prefer Minnan-specific vocabulary, false friends with Mandarin, unusual character usage, colloquial particles, idioms, contractions, and dialect grammar.
- Mention Mandarin cognates only when the sound or meaning relationship helps learning.
- Avoid notes for words that are identical or very close to common Mandarin usage unless Minnan usage differs.
- Avoid line-by-line grammar commentary when the line is already transparent.

## Helper Script

Use the skeleton script when the input is long or alignment is easy to miss:

```powershell
python .\format-minnan-lyrics\scripts\build_lyrics_skeleton.py `
  --translation .\歌曲名\歌词翻译 `
  --romanization .\歌曲名\歌词闽拼 `
  --output .\歌曲名\歌词_骨架.md `
  --header-lines 4
```

If no romanization file exists, omit `--romanization`:

```powershell
python .\format-minnan-lyrics\scripts\build_lyrics_skeleton.py `
  --translation .\歌曲名\歌词翻译 `
  --output .\歌曲名\歌词_骨架.md `
  --header-lines 4
```

Then replace each `<!-- romanization -->` placeholder with generated Minnan Phonetic Scheme romanization, replace each `<!-- annotations -->` placeholder with concise numbered notes or remove it when no note is needed.

If the script reports mismatched lyric lines, inspect the nearby source lines manually. Do not silently discard or reorder lyrics.

## Quality Check

Before finishing, verify:

- Every non-header lyric block has Minnan lyric, romanization, and Chinese translation in that order.
- `---` separators are present between blocks.
- Notes use Simplified Chinese and numbered markers.
- Notes are sparse and focused on Mandarin-speaker difficulty.
- Romanization consistently uses the Minnan Phonetic Scheme / Bbánlám pìngyīm, or preserves the user-provided system only when explicitly requested.
- Uncertain isolated readings are marked sparingly or raised to the user; the output has no unfinished placeholders unless the user explicitly requested a skeleton only.
