# LingoLyrics

一个面向外语歌词学习的注释、时间轴与滚动歌词生成工具。目前支持日语、法语和闽南语歌词学习。

LingoLyrics 可以把歌词整理成带发音、中文翻译和语法/词汇注释的 Markdown 学习材料，并生成类似音乐播放器的滚动歌词 HTML 页面。日语使用罗马音，法语使用逐词法语音标，闽南语使用闽南话拼音方案。

## 功能特性

- 将日语 `歌词翻译` + `歌词罗马音` 整理为 `歌词_格式化.md`。
- 将法语 `歌词翻译` 整理为带逐词法语音标的 `歌词_格式化.md`。
- 将闽南语 `歌词翻译` 整理为带闽南话拼音方案注音的 `歌词_格式化.md`。
- 支持为每句歌词添加词汇、语法、读音和语感注释。
- 根据 `时间轴.json` 生成可滚动、可播放的歌词 HTML。
- 默认读取歌曲文件夹下的 `音频.mp3`，也可在页面中手动选择本地音频。
- 支持显示开关：罗马音/音标、中文翻译、行内注释、侧栏注释。
- 罗马音中的 `**...**` 和 `*...*` 会在 HTML 中渲染为粗体和斜体。
- 法语逐词音标会在 HTML 中与对应单词上下居中对齐。
- 可通过网易云歌曲 id 下载时间轴和音频。

## 环境要求

- Python 3.9+
- 无需额外安装第三方 Python 包。

## 目录结构

建议每首歌单独放一个文件夹：

```text
主目录/
  歌曲名/
    歌词翻译
    歌词罗马音（日语可选/需要）
    歌词闽拼（闽南语可选）
    时间轴.json
    音频.mp3
    歌词_格式化.md
    滚动歌词.html
```

## 需要准备的文件

### 1. 歌词翻译

可在网易云音乐进行复制

文件名建议为 `歌词翻译`。日语、法语和闽南语都使用“原文歌词 + 中文翻译”交替排列，格式为：

```text
歌名
中文歌名
作词: ...
作曲: ...
原文歌词第 1 行
中文翻译第 1 行
原文歌词第 2 行
中文翻译第 2 行
```


### 2. 歌词罗马音（日语）

可在网易云音乐进行复制

文件名建议为 `歌词罗马音`，格式为：

```text
歌名
中文歌名
作词: ...
作曲: ...
日文歌词第 1 行
罗马音第 1 行
日文歌词第 2 行
罗马音第 2 行
```

法语不需要单独准备罗马音文件。`format-french-lyrics` 会根据 `歌词翻译` 生成逐词法语音标。

闽南语可以准备 `歌词闽拼`，也可以让 `format-minnan-lyrics` 根据歌词生成闽南话拼音方案注音。


### 3. 时间轴.json

可通过 `download_netease_song.py` 获取，也可参考网易云歌词接口相关资料手动获取。

用于生成滚动歌词。支持网易云歌词接口常见格式，例如：

```json
{
  "lyric": "[00:00.000]第一句歌词\n[00:03.200]第二句歌词"
}
```

如果暂时没有时间轴，`lyrics_to_html.py` 也可以生成页面，但会按每行固定时长模拟滚动。

### 4. 音频.mp3（可选）

如果歌曲文件夹下存在 `音频.mp3`，生成的 `滚动歌词.html` 会默认使用它作为音频源。没有音频也可以使用时间轴模拟播放。

## 生成格式化歌词 Markdown（日语）

使用 Codex 的 `format-japanese-lyrics` skill，根据 `歌词翻译` 和 `歌词罗马音` 生成：

```text
歌曲名/歌词_格式化.md
```

输出格式大致为：

```markdown
日文歌词
ro ma ji
中文翻译
①词语（かな / romaji）：简短注释。
②语法结构：简短说明。

---
```

如果只想先生成对齐骨架，可运行：

```powershell
python .\format-japanese-lyrics\scripts\build_lyrics_skeleton.py `
  --translation .\歌曲名\歌词翻译 `
  --romaji .\歌曲名\歌词罗马音 `
  --output .\歌曲名\歌词_骨架.md `
  --header-lines 4
```

然后再把 `<!-- annotations -->` 替换为注释。

生成带注释的markdown后可自由进行注释修改和矫正

在罗马音一行可以用 `**...**` ， `*...*` 等方式为自己标记重音。

## 生成格式化歌词 Markdown（法语）

使用 Codex 的 `format-french-lyrics` skill，根据法语 `歌词翻译` 生成：

```text
歌曲名/歌词_格式化.md
```

输出格式大致为：

```markdown
法语歌词
[逐词] [法语] [音标]
中文翻译
①词语（[音标]）：词性和解释。
②动词（[音标]）：`原形` 的当前变位，含义和句中作用。

---
```

法语音标使用方括号逐词标注，例如：

```markdown
On veut croire à des choses éternelles
[ɔ̃] [vф] [krwar] [a] [de] [ʃoz] [etεrnεl]
```

动词注释的括号里只放音标，原形、时态、人称写在冒号后的说明里：

```markdown
③ sommes（[sɔm]）：`être` 的直陈式现在时第一人称复数，意为“我们是”。
```

如果只想先生成骨架，可运行：

```powershell
python .\format-french-lyrics\scripts\build_lyrics_skeleton.py `
  --input .\歌曲名\歌词翻译 `
  --output .\歌曲名\歌词_骨架.md `
  --header-lines 4
```

然后再把 `<!-- phonetics -->` 和 `<!-- annotations -->` 替换为音标和注释。

## 生成格式化歌词 Markdown（闽南语）

使用 Codex 的 `format-minnan-lyrics` skill，根据闽南语 `歌词翻译`，可选配合 `歌词闽拼` 生成：

```text
歌曲名/歌词_格式化.md
```

输出格式大致为：

```markdown
闽南语歌词
bbánlám pìngyīm
中文翻译
①词语（闽拼）：只解释普通话母语者较难理解的词或用法。

---
```

闽南语注音默认使用闽南话拼音方案 / Bbánlám pìngyīm。注释会尽量少写，只标普通话母语者容易卡住的方言词、语气词、特殊字词或用法。

如果歌词中有普通话唱词或旁白，不需要闽拼、翻译和注释时，写成两行块即可：

```markdown
鸟在飞行间鸣叫
（普通话）

---
```

如果只想先生成骨架，可运行：

```powershell
python .\format-minnan-lyrics\scripts\build_lyrics_skeleton.py `
  --translation .\歌曲名\歌词翻译 `
  --romanization .\歌曲名\歌词闽拼 `
  --output .\歌曲名\歌词_骨架.md `
  --header-lines 4
```

没有 `歌词闽拼` 时可以省略 `--romanization`，然后再补闽拼和注释。

## 生成滚动歌词 HTML

准备好 `歌词_格式化.md` 和 `时间轴.json` 后运行：

```powershell
python .\lyrics_to_html.py .\歌曲名
```

默认读取：

```text
歌曲名/歌词_格式化.md
歌曲名/时间轴.json
歌曲名/音频.mp3（如果存在）
```

默认输出：

```text
歌曲名/滚动歌词.html
```

也可以手动指定路径：

```powershell
python .\lyrics_to_html.py .\歌曲名 `
  --md .\歌曲名\歌词_格式化.md `
  --timeline .\歌曲名\时间轴.json `
  --audio .\歌曲名\音频.mp3 `
  --output .\歌曲名\滚动歌词.html
```

生成的 HTML 可以直接用浏览器打开。没有音频时会按时间轴模拟播放；有 `音频.mp3` 时会默认加载该音频；也可以打开页面后点击右上角“音频”选择其他本地音频文件。

## 滚动歌词页面功能

- 固定显示原文歌词。
- 可开关显示罗马音/音标、中文翻译、行内注释、侧栏注释。
- 支持播放、暂停、重置和拖动进度条。
- 当前歌词行自动居中、高亮。
- 罗马音中的 `**...**` 和 `*...*` 会渲染为粗体和斜体。
- 如果发音行是逐词方括号格式，并且数量与歌词单词数量一致，HTML 会自动将每个单词和对应音标上下居中显示；日语罗马音和闽南语闽拼仍按单行方式渲染。

## 示例命令

```powershell
python .\download_netease_song.py --id-file .\蜡烛\id --out .\蜡烛
python .\lyrics_to_html.py .\蜡烛
python .\lyrics_to_html.py .\蜉蝣 --output .\蜉蝣\滚动歌词_法语测试.html
```

## 下载时间轴和音频

如果已经知道网易云歌曲 id，可以用 `download_netease_song.py` 下载时间轴和音频：

```powershell
python .\download_netease_song.py 2074100424 --out .\蜡烛
```

如果不传歌曲 id，脚本会提示输入；可以粘贴纯 id，也可以粘贴包含 `id=...` 的网易云歌曲链接：

```powershell
python .\download_netease_song.py --out .\歌曲名
```

示例输入：

```text
https://music.163.com/song?id=1920623028&uct2=...
```

默认输出：

```text
歌曲目录/时间轴.json
歌曲目录/音频.mp3
```

也可以从歌曲目录里的 `id` 文件读取。`id` 文件中可以写纯 id，也可以写包含 `id=...` 的网址：

```powershell
python .\download_netease_song.py --id-file .\蜡烛\id --out .\蜡烛
```

只下载时间轴：

```powershell
python .\download_netease_song.py 2074100424 --out .\蜡烛 --skip-audio
```

只下载音频：

```powershell
python .\download_netease_song.py 2074100424 --out .\蜡烛 --skip-lyric
```

如果文件已经存在，默认不会覆盖；需要覆盖时加 `--overwrite`。

## 注意事项

- 本项目主要用于个人外语学习。
- 歌词和音频可能受版权保护，请尊重相关权利人的权益。
- 生成的 HTML 会内嵌歌词和注释数据，若包含受版权保护的歌词，不建议直接公开发布。
