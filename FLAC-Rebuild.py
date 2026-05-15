import os
import sys
import subprocess
from pathlib import Path
import ctypes
from ctypes import wintypes

try:
	from mutagen.flac import FLAC, Picture
except ImportError:
	print("错误: 缺少必要库 'mutagen'。请运行: pip install mutagen")
	sys.exit(1)

# 路径自适应
BASE_PATH = Path(sys._MEIPASS) if getattr(sys, "frozen", False) else Path(__file__).parent
LIBS_DIR = BASE_PATH / "libs"
FLAC_EXE = str(LIBS_DIR / "flac.exe")
PINGO_EXE = str(LIBS_DIR / "pingo.exe")


def set_file_times(path, ctime, atime, mtime):
	"""通过Windows API完美恢复文件的创建、访问和修改时间"""

	def to_ft(t):
		val = int(t * 10000000) + 116444736000000000
		return wintypes.FILETIME(val & 0xFFFFFFFF, val >> 32)

	ft_c, ft_a, ft_m = to_ft(ctime), to_ft(atime), to_ft(mtime)
	handle = ctypes.windll.kernel32.CreateFileW(str(path), 0x0100, 0x01 | 0x02, None, 3, 0x80, None)
	if handle != -1:
		ctypes.windll.kernel32.SetFileTime(handle, ctypes.byref(ft_c), ctypes.byref(ft_a), ctypes.byref(ft_m))
		ctypes.windll.kernel32.CloseHandle(handle)


def process_flac(file_path):
	f_path = Path(file_path)
	print(f"\n处理: {f_path.name}")

	# 备份原始时间戳 (创建时间, 访问时间, 修改时间)
	st = f_path.stat()
	orig_times = (st.st_ctime, st.st_atime, st.st_mtime)

	os.chdir(f_path.parent)
	temp_img = "temp_cover.jpg"
	orig_bak = f_path.with_name(f"{f_path.stem}_orig.flac")

	try:
		# 1. 提取并使用 Pingo 压缩封面
		audio = FLAC(f_path)
		if audio.pictures:
			with open(temp_img, "wb") as f:
				f.write(audio.pictures[0].data)

			subprocess.run([PINGO_EXE, "-lossless", "-s4", temp_img], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

			if os.path.exists(temp_img):
				with open(temp_img, "rb") as f:
					new_pic = Picture()
					new_pic.data = f.read()
					new_pic.type = 3
					new_pic.mime = "image/jpeg"

				audio.clear_pictures()
				audio.add_picture(new_pic)
				audio.save()
				os.remove(temp_img)
				print("成功：封面压缩完成")

		# 2. 重命名备份并使用 flac.exe 快速重构音频流
		if orig_bak.exists():
			orig_bak.unlink()
		f_path.rename(orig_bak)

		# -8 参数为最高压缩封装，无损压缩并重新编排流结构
		cmd_flac = [FLAC_EXE, "-8", "-f", str(orig_bak.name), "-o", str(f_path.name)]
		result = subprocess.run(cmd_flac, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

		if result.returncode == 0:
			orig_bak.unlink()  # 成功后清理备份
			set_file_times(f_path, *orig_times)  # 恢复原始时间戳
			print("成功：文件重建完成")
		else:
			print(f"错误：flac.exe: {result.returncode}")
			if orig_bak.exists() and not f_path.exists():
				orig_bak.rename(f_path)

	except Exception as e:
		print(f"错误：处理失败: {e}")
		if orig_bak.exists() and not f_path.exists():
			orig_bak.rename(f_path)


if __name__ == "__main__":
	for tool in [FLAC_EXE, PINGO_EXE]:
		if not os.path.exists(tool):
			print(f"错误: libs 目录下缺少工具: {os.path.basename(tool)}")
			sys.exit(1)

	files = sys.argv[1:]
	if not files:
		print("提示: 请将 FLAC 文件拖放到此程序上执行。")
	else:
		for f in files:
			if f.lower().endswith(".flac"):
				process_flac(f)
			else:
				print(f"非 FLAC 文件: {os.path.basename(f)}")

	input("\n所有任务处理完毕，按回车退出...")