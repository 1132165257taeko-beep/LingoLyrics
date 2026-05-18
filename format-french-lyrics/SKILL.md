---
name: format-french-lyrics
description: "Format French song lyrics for study from a paired French lyrics + Chinese translation file. Use when Codex needs to add French phonetic transcription, translations, and detailed Simplified Chinese grammar/vocabulary notes into a structured Markdown lyric sheet for French learning."
---

# Format French Lyrics

## Goal

Create a study-ready Markdown lyric sheet from one source file:

- `lyrics + translation`: alternating French lyric line and Simplified Chinese translation line, with optional title/credit header.

The final output should match this block pattern:

```markdown
Title line(s)
Credit line(s)

---

French lyric line
[word-by-word French phonetics]
Chinese translation line
① 词或短语（法语音标）：词性，中文解释；必要时说明词源、搭配、语域或歌词中的省略。
② 动词（法语音标）：说明原形、当前变位、含义和句中作用。
③ 语法结构：说明结构如何影响理解。

---
```

## Workflow

1. Read the input file and desired output path from the user. If paths are omitted, infer common names such as `歌词翻译` and `歌词_格式化.md` in the current song folder.
2. Preserve the header from the input file: song title, artist/title variant, lyricist, composer, translator, or other non-paired metadata.
3. Align body lines as French lyric line + Chinese translation line pairs.
4. If the input is long or pairing is uncertain, use `scripts/build_lyrics_skeleton.py` to generate a skeleton and inspect warnings before filling French phonetics and notes.
5. Add French phonetic transcription under each French lyric line using the symbol inventory below. Use contemporary Standard French pronunciation, including common liaison/enchainement only when it would normally be pronounced in careful singing or connected speech.
6. Add detailed annotations in Simplified Chinese using `references/annotation-guidelines.md`.
7. Separate every lyric block with `---`. Keep repeated chorus blocks repeated; do not collapse them unless the user asks.
8. Save as Markdown. Prefer the user's requested filename; otherwise use `歌词_格式化.md` in the song folder.

## Formatting Rules

- Keep the original French lyric text exactly as supplied unless the user explicitly asks to correct text or encoding.
- Put the French phonetic transcription immediately after the French line. Use word-by-word square-bracket groups, for example `Je t'aime` -> `[Ʒə] [tεm]`.
- Keep the phonetic groups in the same order as the lyric words so learners can visually align them. Do not force exact column alignment with extra spaces; Markdown and HTML usually collapse spacing.
- Use the French phonetic symbol inventory below, not International Phonetic Alphabet output, English-style respelling, pinyin, or Chinese phonetic approximation.
- Mark elision and connected pronunciation naturally in French phonetics, for example `j'aime` as `[Ʒεm]`, `l'amour` as `[lamur]`, and `les amours` as `[lez] [amur]` when liaison is pronounced.
- Use these symbols for French vowels:
  - 口腔前元音: `[i] [e] [ε] [a]`
  - 口腔中元音: `[u] [o] [ɔ]`
  - 口腔后元音: `[y] [ф] [ə] [œ]`
  - 鼻化元音: `[ɛ̃] [œ̃] [ɑ̃] [ɔ̃]`
- Use these symbols for French consonants and semivowels:
  - 爆破辅音: `[p] [b] [t] [d] [k] [g]`
  - 摩擦辅音: `[f] [v] [s] [z] [ʃ] [Ʒ]`
  - 鼻辅音: `[l] [m] [n] [ɲ]`
  - 边辅音: `[r]`
  - 半元音: `[ɥ] [w] [j]`
- Preserve English or other non-French words in the lyric as originally styled; transcribe them only if pronunciation is reasonably clear from context.
- Put the Chinese translation immediately after the phonetic transcription line.
- Use numbered annotations `①`, `②`, `③` in order. Put each numbered annotation on its own line. For French, prefer 2-6 notes per lyric line when there is enough material; the user wants detailed notes.
- For every conjugated verb in the lyric line, try to note its infinitive and current form: tense, mood, person/number, and any agreement if relevant.
- In annotation headings, put only the French phonetics inside parentheses. Put the verb infinitive and conjugation details after the colon, for example `③ sommes（[sɔm]）：\`être\` 的直陈式现在时第一人称复数，意为“我们是”。`
- Annotate most lyric content: nouns, verbs, adjectives, adverbs, pronouns, negation, prepositions, contractions, idioms, fixed expressions, and notable pronunciation.
- For very short interjections such as `Oh`, `Ah`, `Yeah`, output the line, phonetics, translation, and separator without forced grammar notes unless context makes it useful.

## Annotation Priorities

Read `references/annotation-guidelines.md` when writing or revising notes. In short:

- Prefer notes that help with meaning, grammar, pronunciation, morphology, register, or translation differences.
- Explain vocabulary, verbs, adjectives, adverbs, pronouns, prepositions, contractions, idioms, set phrases, and common lyric inversions or omissions.
- Explain grammar when it changes interpretation: negation, tense/aspect, mood, reflexive verbs, pronominal verbs, compound tenses, relative clauses, object pronoun order, gender/number agreement, liaison, elision, and subjunctive/conditional nuance.
- Do not waste notes on extremely basic items if the line is already dense, but err on the side of detailed coverage for this skill.
- Avoid broad literary commentary unless the user requests interpretation; keep notes language-learning focused.

## Helper Script

Use the skeleton script when the input is long or line pairing is easy to miss:

```powershell
python .\format-french-lyrics\scripts\build_lyrics_skeleton.py `
  --input .\蜉蝣\歌词翻译 `
  --output .\蜉蝣\歌词_骨架.md `
  --header-lines 4
```

Then replace each `<!-- phonetics -->` placeholder with French phonetic transcription and each `<!-- annotations -->` placeholder with detailed numbered notes.

If the script reports an odd number of body lines, inspect the nearby source lines manually. Do not silently discard or reorder lyrics.

## Quality Check

Before finishing, verify:

- Every non-header lyric block has French, French phonetics, Chinese translation, then notes in that order.
- `---` separators are present between blocks.
- Phonetics use the specified French phonetic symbols and word-by-word square-bracket notation.
- Notes use Simplified Chinese and numbered markers.
- Conjugated verbs include infinitive and current form wherever practical.
- The output has no unfinished placeholders unless the user explicitly requested a skeleton only.
