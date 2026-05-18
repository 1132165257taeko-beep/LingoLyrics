#!/usr/bin/env python3
"""Build a Markdown skeleton from lyric+translation and optional lyric+romanization files."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Optional, Tuple


def read_lines(path: Path) -> List[str]:
    text = path.read_text(encoding="utf-8-sig")
    return [line.rstrip() for line in text.splitlines() if line.strip()]


def pair_lines(lines: List[str], start: int) -> List[Tuple[str, str]]:
    body = lines[start:]
    pairs: List[Tuple[str, str]] = []
    for index in range(0, len(body), 2):
        first = body[index]
        second = body[index + 1] if index + 1 < len(body) else ""
        pairs.append((first, second))
    return pairs


def align_romanization(
    translation_pairs: List[Tuple[str, str]],
    romanization_lines: List[str],
    header_lines: int,
) -> Tuple[List[str], List[str]]:
    body = romanization_lines[header_lines:]
    romanization: List[str] = []
    warnings: List[str] = []
    cursor = 0

    for index, (lyric, _chinese) in enumerate(translation_pairs):
        next_lyric: Optional[str] = None
        if index + 1 < len(translation_pairs):
            next_lyric = translation_pairs[index + 1][0]

        if cursor >= len(body):
            warnings.append(f"line {index + 1}: missing romanization for {lyric!r}")
            romanization.append("")
            continue

        if body[cursor] != lyric:
            try:
                found_at = body.index(lyric, cursor + 1)
            except ValueError:
                warnings.append(
                    f"line {index + 1}: lyric text not found in romanization file: {lyric!r}"
                )
                romanization.append("")
                continue

            skipped = body[cursor:found_at]
            warnings.append(
                f"line {index + 1}: skipped {len(skipped)} unmatched romanization-file line(s) before {lyric!r}"
            )
            cursor = found_at

        candidate_index = cursor + 1
        if candidate_index >= len(body) or body[candidate_index] == next_lyric:
            romanization.append(lyric)
            cursor += 1
        else:
            romanization.append(body[candidate_index])
            cursor += 2

    if cursor < len(body):
        warnings.append(f"unused trailing romanization-file lines: {len(body) - cursor}")

    return romanization, warnings


def build_markdown(
    translation_lines: List[str],
    romanization_lines: Optional[List[str]],
    header_lines: int,
) -> Tuple[str, List[str]]:
    header = translation_lines[:header_lines]
    translation_pairs = pair_lines(translation_lines, header_lines)
    if romanization_lines is None:
        romanization_values = ["<!-- romanization -->"] * len(translation_pairs)
        warnings: List[str] = []
    else:
        romanization_values, warnings = align_romanization(
            translation_pairs, romanization_lines, header_lines
        )

    blocks: List[str] = []
    blocks.extend(header)
    blocks.append("")
    blocks.append("---")

    for translation_pair, romanization in zip(translation_pairs, romanization_values):
        lyric_from_translation, chinese = translation_pair

        blocks.extend(
            [
                "",
                lyric_from_translation,
                romanization,
                chinese,
                "<!-- annotations -->",
                "",
                "---",
            ]
        )

    return "\n".join(blocks).rstrip() + "\n", warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--translation", required=True, type=Path)
    parser.add_argument("--romanization", type=Path)
    parser.add_argument("--romaji", dest="romanization", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--header-lines", type=int, default=4)
    args = parser.parse_args()

    translation_lines = read_lines(args.translation)
    romanization_lines = read_lines(args.romanization) if args.romanization else None
    markdown, warnings = build_markdown(
        translation_lines, romanization_lines, args.header_lines
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(markdown, encoding="utf-8")

    for warning in warnings:
        print(f"WARNING: {warning}")
    print(f"Wrote {args.output}")
    return 0 if not warnings else 2


if __name__ == "__main__":
    raise SystemExit(main())
