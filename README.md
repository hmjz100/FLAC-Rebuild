# FLAC Rebuild

一个基于 Python 开发的 FLAC 文件重建工具，专用于解决 foobar2000 提示 “文件末尾有垃圾(ID3 标签?)” 的问题。

一次拖放即可解决问题。

## 功能
- 重建 FLAC 文件
- 重建时使用最高压缩率进行无损压缩
- 封面提取使用 Mutagen 操作标签
- 封面压缩使用 Pingo 引擎
- 支持 UTF-8 编码
- 标签使用 Vorbis Comments
- 可保留文件修改时间
- 成功后会删除备份文件，失败则保留备份文件。

## 编译

环境要求：
* Windows 10/11 (x64)。
* `libs` 文件夹内包含 `flac.exe`, `libFLAC.dll`, `pingo.exe`。
* `pathlib` `mutagen` `pyinstaller` 库

打包：
```bash
pyinstaller --onefile --console --noupx --add-data "libs;libs" --name "FLAC-Rebuild" FLAC-Rebuild.py
```
*注意：必须添加 `--noupx` 参数，否则内置的 pingo.exe 会被压缩，导致程序报 “16位程序不兼容” 错误。