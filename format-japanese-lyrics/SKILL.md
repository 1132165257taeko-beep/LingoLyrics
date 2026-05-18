---
name: format-japanese-lyrics
description: "Format Japanese song lyrics for study from a Japanese lyrics + Chinese translation file, optionally with a Japanese lyrics + romaji file. Use when Codex needs to merge lyric lines, generate or align romaji, translations, pronunciation emphasis, and concise Chinese grammar/vocabulary notes into a structured Markdown lyric sheet for Japanese learning."
---

# Format Japanese Lyrics

## Goal

Create a study-ready Markdown lyric sheet from one or two source files:

- `lyrics + translation`: alternating Japanese lyric line and Simplified Chinese translation line, with optional title/credit header.
- Optional `lyrics + romaji`: alternating Japanese lyric line and spaced romaji line, with the same optional title/credit header.

The final output should match this block pattern:

```markdown
Title line(s)
Credit line(s)

---

Japanese lyric line
romaji line
Chinese translation line
①词或短语（かな / romaji）：词性，简短解释；必要时补充词源或用法。
②语法结构（romaji）：结构说明，说明它如何影响理解。

---
```

## Workflow

1. Read the translation input file, optional romaji input file, and desired output path from the user. If paths are omitted, infer common names such as `歌词翻译`, optional `歌词罗马音`, and `歌词_格式化.md` in the current song folder.
2. Preserve the header from the translation file: song title, artist/title variant, lyricist, composer, or other non-paired metadata.
3. Each output block must contain Japanese, romaji, Chinese translation, then notes.
4. If a romaji file exists, align body lines by Japanese lyric line.
5. If no romaji file exists, generate romaji yourself from the Japanese lyric line. Do not omit the romaji line.
6. If alignment is uncertain, use `scripts/build_lyrics_skeleton.py` to generate a skeleton and inspect warnings before adding notes.
7. Add annotations in Simplified Chinese using the guidance in `references/annotation-guidelines.md`.
8. Separate every lyric block with `---`. Keep repeated chorus blocks repeated; do not collapse them unless the user asks.
9. Save as Markdown. Prefer the user's requested filename; otherwise use `歌词_格式化.md` in the song folder.

## Formatting Rules

- Keep the original Japanese lyric text exactly as supplied unless the user explicitly asks to correct text or encoding.
- Keep romaji spaced by kana/mora style, for example `na ma e`, `ko u su i`, `ta da`.
- When generating romaji without a romaji source file, infer standard readings from context and common song pronunciation. Use Hepburn-style consonants with the repo's mora spacing style, e.g. `shi`, `chi`, `tsu`, `fu`, `ja`, `jo`, `ryo`; split long vowels as `o u`, `e i`, etc.
- Preserve English words in the romaji line as English words, such as `Welcome Back`, `Red Red Check`, `Museum: Zero`.
- Preserve English words in the lyric as originally styled, such as `Harmony`, `Heart Beat`, `Moonlight`.
- Put the Chinese translation immediately after the romaji line.
- Use numbered annotations `①`, `②`, `③` in order. Usually 1-4 notes per line is enough; use more only when the line is dense.
- For simple repeated interjections such as `Yeah`, output the line pair and separator without forced annotations.
- Keep annotations concise and objective. Avoid long literary commentary unless the user requests interpretation.

## Annotation Priorities

Read `references/annotation-guidelines.md` when writing or revising notes. In short:

- Prefer notes that help with meaning, grammar, pronunciation, word origin, register, or translation differences.
- Explain vocabulary, verbs, adjectives, adverbs, mimetic words, loanwords, idioms, difficult kanji readings, and useful set phrases.
- Explain grammar when it changes interpretation: negation, contrast, connective patterns, potential/passive/causative forms, omissions, colloquial contractions, sentence-ending nuance.
- Avoid standalone notes for basic particles such as `の`, `が`, `は`, `を`, `に`, `で`, `と`, `も`, `から`, `まで`, `へ`, `や`, unless the use is special or part of a larger expression.
- Avoid explaining ordinary inflection unless it matters for understanding.

## Helper Script

Use the skeleton script when the input is long or alignment is easy to miss:

```powershell
python .\format-japanese-lyrics\scripts\build_lyrics_skeleton.py `
  --translation .\蜡烛\歌词翻译 `
  --romaji .\蜡烛\歌词罗马音 `
  --output .\蜡烛\歌词_骨架.md `
  --header-lines 4
```

If no romaji file exists, omit `--romaji`:

```powershell
python .\format-japanese-lyrics\scripts\build_lyrics_skeleton.py `
  --translation .\Museum_0\歌词翻译 `
  --output .\Museum_0\歌词_骨架.md `
  --header-lines 4
```

Then replace each `<!-- romaji -->` placeholder with generated romaji, replace each `<!-- annotations -->` placeholder with concise numbered notes, and add romaji emphasis if useful.

If the script reports mismatched Japanese lines, inspect the nearby source lines manually. Do not silently discard or reorder lyrics.

## Quality Check

Before finishing, verify:

- Every non-header lyric block has Japanese, romaji, and Chinese translation in that order.
- `---` separators are present between blocks.
- Notes use Simplified Chinese and numbered markers.
- Romaji style is consistent with the source file, or consistently generated in mora-spaced Hepburn style when no source file exists.
- The output has no unfinished placeholders unless the user explicitly requested a skeleton only.
