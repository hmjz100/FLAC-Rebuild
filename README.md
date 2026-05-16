# Audio Rebuilder

一个基于 Python 开发的 FLAC 文件重建工具，本用于解决 foobar2000 对 FLAC 文件提示 “文件末尾有垃圾(ID3 标签?)” 的问题。

现已支持重建 MP3 与 FLAC 两种格式的文件，一次拖放即可优化音频文件。

## 功能&亮点
- 重建 FLAC、MP3 文件
- FLAC 重建时使用最高压缩率进行无损压缩
- FLAC 标签使用 Vorbis Comments
- MP3 重建时会剔除除音频与封面以外的冗余数据
- MP3 标签使用 ID3v2.3
- 封面提取使用 Mutagen 操作标签
- 封面压缩使用 Pingo 引擎
- 使用 UTF-8 编码
- 使用最旧文件修改时间
- 成功后会删除备份文件，失败则保留备份文件。

## 使用&编译

环境要求：
* Windows 10/11 (x64)。
* `libs` 文件夹内包含 `ffmpeg.exe`, `flac.exe`, `libFLAC.dll`, `pingo.exe`。
* `pathlib` `mutagen` `pyinstaller` 库

打包：
```bash
pyinstaller --onefile --console --noupx --add-data "libs;libs" --name "Audio-Rebuilder" Audio-Rebuilder.py
```
*注意：必须添加 `--noupx` 参数，否则内置的 pingo.exe 会被压缩，导致运行时报 “16位程序不兼容” 错误。