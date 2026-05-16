import os
import sys
import subprocess
from pathlib import Path
import ctypes
from ctypes import wintypes

try:
	from mutagen.flac import FLAC, Picture
	from mutagen.mp3 import MP3
	from mutagen.id3 import ID3, APIC
except ImportError:
	print("错误: 缺少必要库 'mutagen'。请运行: pip install mutagen")
	sys.exit(1)

# 路径自适应
BASE_PATH = Path(sys._MEIPASS) if getattr(sys, "frozen", False) else Path(__file__).parent
LIBS_DIR = BASE_PATH / "libs"
FLAC_EXE = str(LIBS_DIR / "flac.exe")
PINGO_EXE = str(LIBS_DIR / "pingo.exe")
FFMPEG_EXE = str(LIBS_DIR / "ffmpeg.exe")


def set_file_times(path, ctime, atime, mtime):
	"""通过Windows API恢复文件时间，选用传入参数中最古老的时间作为统一时间戳"""
	oldest_time = min(ctime, atime, mtime)

	def to_ft(t):
		val = int(t * 10000000) + 116444736000000000
		return wintypes.FILETIME(val & 0xFFFFFFFF, val >> 32)

	ft_c = ft_a = ft_m = to_ft(oldest_time)
	handle = ctypes.windll.kernel32.CreateFileW(str(path), 0x0100, 0x01 | 0x02, None, 3, 0x80, None)
	if handle != -1:
		ctypes.windll.kernel32.SetFileTime(handle, ctypes.byref(ft_c), ctypes.byref(ft_a), ctypes.byref(ft_m))
		ctypes.windll.kernel32.CloseHandle(handle)


def process_audio(file_path):
	f_path = Path(file_path)
	ext = f_path.suffix.lower()
	print(f"\n处理: {f_path.name}")

	# 备份原始时间戳 (创建时间, 访问时间, 修改时间)
	st = f_path.stat()
	orig_times = (st.st_ctime, st.st_atime, st.st_mtime)

	os.chdir(f_path.parent)
	temp_img = "temp_cover.jpg"
	orig_bak = f_path.with_name(f"{f_path.stem}_orig{ext}")

	try:
		# 1. 封面处理逻辑
		has_cover = False
		if ext == ".flac":
			audio = FLAC(f_path)
			if audio.pictures:
				with open(temp_img, "wb") as f:
					f.write(audio.pictures[0].data)
				has_cover = True
		elif ext == ".mp3":
			audio = MP3(f_path, ID3=ID3)
			apic_frames = audio.tags.getall("APIC")
			if apic_frames:
				with open(temp_img, "wb") as f:
					f.write(apic_frames[0].data)
				has_cover = True

		if has_cover:
			subprocess.run([PINGO_EXE, "-lossless", "-s4", temp_img], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
			if os.path.exists(temp_img):
				with open(temp_img, "rb") as f:
					img_data = f.read()
				
				if ext == ".flac":
					new_pic = Picture()
					new_pic.data = img_data
					new_pic.type = 3
					new_pic.mime = "image/jpeg"
					audio.clear_pictures()
					audio.add_picture(new_pic)
				elif ext == ".mp3":
					audio.tags.delall("APIC")
					audio.tags.add(APIC(encoding=3, mime='image/jpeg', type=3, desc='Front cover', data=img_data))
				
				audio.save()
				os.remove(temp_img)
				print("成功：封面压缩完成")

		# 2. 重命名备份并重构音频流
		if orig_bak.exists():
			orig_bak.unlink()
		f_path.rename(orig_bak)
		set_file_times(orig_bak, *orig_times)

		if ext == ".flac":
			# FLAC
			# -8: 最高压缩封装
			cmd = [FLAC_EXE, "-8", "-f", str(orig_bak.name), "-o", str(f_path.name)]
		else:
			# MP3
			# -y: 覆盖输出
			# -c copy: 仅拷贝流(无损)
			# -map 0:a -map 0:v? : 仅保留音频和封面，剔除可能存在的垃圾数据流
			# -map_metadata 0: 保留所有元数据
			# -id3v2_version 3 : 使用标准 ID3v2.3 标签，减少版本冲突开销
			# -write_id3v1 0 : 强制不写入旧版 ID3v1 标签，节省文件末尾空间
			cmd = [
				FFMPEG_EXE, "-y", "-i", str(orig_bak.name), 
				"-c", "copy", "-map", "0:a", "-map", "0:v?", 
				"-map_metadata", "0", "-id3v2_version", "3", "-write_id3v1", "0", 
				str(f_path.name)
			]

		result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

		if result.returncode == 0:
			orig_bak.unlink()  # 成功后清理备份
			set_file_times(f_path, *orig_times)  # 恢复原始时间戳
			print("成功：文件重建完成")
		else:
			print(f"错误：重构工具返回码: {result.returncode}")
			if orig_bak.exists() and not f_path.exists():
				orig_bak.rename(f_path)
				set_file_times(f_path, *orig_times)

	except Exception as e:
		import traceback
		print(f"错误：处理失败: {e}")
		# traceback.print_exc() # 调试用
		if orig_bak.exists() and not f_path.exists():
			orig_bak.rename(f_path)
			set_file_times(f_path, *orig_times)


if __name__ == "__main__":
	for tool in [FLAC_EXE, PINGO_EXE, FFMPEG_EXE]:
		if not os.path.exists(tool):
			print(f"错误: libs 目录下缺少工具: {os.path.basename(tool)}")
			sys.exit(1)

	files = sys.argv[1:]
	if not files:
		print("提示: 请将 FLAC 或 MP3 文件拖放到此程序上执行。")
	else:
		for f in files:
			if f.lower().endswith((".flac", ".mp3")):
				process_audio(f)
			else:
				print(f"不支持的文件格式: {os.path.basename(f)}")

	print("\n执行完毕，按任意键退出...")
	ctypes.windll.msvcrt._getch()