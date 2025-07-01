import os
import subprocess
from pathlib import Path
import pyperclip


# 2025.07.01 14:07:35
# 当前Finder选中的ncm歌曲文件，转换

def ncm_to_flac(ncm_path):
	"""NCM 文件转换为 FLAC 格式"""
	flac_path = ncm_path.replace('.ncm', '.flac')
	try:
		subprocess.run(['ncmdump', ncm_path], check=True)
		print(f"NCM 转换 FLAC 成功 ✅")
		return flac_path
	except subprocess.CalledProcessError as e:
		print(f"NCM 转换 FLAC 失败 ❌: {e}")
		return None


def extract_cover(flac_path, output_dir):
	"""从 FLAC 文件提取专辑封面"""
	cover_path = Path(output_dir) / (Path(flac_path).stem + "_cover.jpg")
	try:
		# 检查文件是否包含封面
		result = subprocess.run(['ffprobe', '-i', flac_path, '-show_streams', '-select_streams', 'v'],
		                        capture_output=True, text=True)
		if 'codec_type=video' not in result.stdout:
			print("未找到封面图片 ⚠️")
			return None

		subprocess.run([
			'ffmpeg', '-i', flac_path,
			'-map', '0:v:0',  # 映射第一个视频流（封面图）
			'-c:v', 'mjpeg',  # 确保以 JPEG 格式提取
			'-f', 'image2', str(cover_path),
			'-loglevel', 'quiet'
		], check=True)
		print(f"封面提取成功 ✅: {cover_path}")
		return str(cover_path)
	except subprocess.CalledProcessError as e:
		print(f"封面提取失败 ❌: {e}")
		return None


def extract_subtitles(flac_path, output_dir):
	"""从 FLAC 文件提取字幕"""
	subtitle_path = Path(output_dir) / (Path(flac_path).stem + "_subtitles.srt")
	try:
		# 检查文件是否包含字幕
		result = subprocess.run(['ffprobe', '-i', flac_path, '-show_streams', '-select_streams', 's'],
		                        capture_output=True, text=True)
		if 'codec_type=subtitle' not in result.stdout:
			print("未找到字幕 ⚠️")
			return None

		subprocess.run([
			'ffmpeg', '-i', flac_path,
			'-map', '0:s:0',  # 映射第一个字幕流
			str(subtitle_path),
			'-loglevel', 'quiet'
		], check=True)
		print(f"字幕提取成功 ✅: {subtitle_path}")
		return str(subtitle_path)
	except subprocess.CalledProcessError as e:
		print(f"字幕提取失败 ❌: {e}")
		return None


def flac_to_alac(flac_path):
	"""FLAC 转换为 ALAC (M4A) 格式"""
	m4a_path = flac_path.replace('.flac', '.m4a')
	try:
		subprocess.run([
			'ffmpeg', '-i', flac_path,
			'-map', '0:a',  # 映射音频流
			'-map', '0:v?',  # 映射封面图(如果存在)
			'-c:a', 'alac',
			'-c:v', 'copy',  # 复制封面图
			m4a_path,
			'-loglevel', 'quiet'
		], check=True)
		print(f"FLAC 转换 ALAC 成功 ✅")
		return m4a_path
	except subprocess.CalledProcessError as e:
		print(f"FLAC 转换 ALAC 失败 ❌: {e}")
		return None


def main():
	# 从剪贴板获取文件名
	filename = pyperclip.paste().strip()
	if not filename.endswith('.ncm'):
		filename += '.ncm'
	ncm_path = os.path.join('/Users/andy/Downloads/', filename)

	# 检查文件是否存在
	if not os.path.isfile(ncm_path):
		print(f"文件不存在 ❌: {ncm_path}")
		return

	print("开始处理音频文件 🎵")

	# 第一步: NCM 转换为 FLAC
	print("\n1. NCM 转换为 FLAC:")
	flac_path = ncm_to_flac(ncm_path)
	if not flac_path:
		print("转换终止 ❌")
		return

	# 提取并保存封面
	output_dir = os.path.dirname(flac_path)
	cover_path = extract_cover(flac_path, output_dir)

	# 第二步: FLAC 转换为 ALAC
	print("\n2. FLAC 转换为 ALAC:")
	m4a_path = flac_to_alac(flac_path)
	if not m4a_path:
		print("转换终止 ❌")
		return

	print(f"\n转换完成 🎉\nFLAC: {flac_path}\nM4A: {m4a_path}")
	if cover_path:
		print(f"封面: {cover_path}")


if __name__ == '__main__':
	main()
