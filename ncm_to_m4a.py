import os
import subprocess
from pathlib import Path

# 2025.07.01 19:00:51
# mac 从 finder 获取文件，NCM 转换 M4A

def get_selected_finder_file():
	"""获取 Finder 当前选中的文件路径（适用于 macOS 系统）"""
	try:
		script = """
        tell application "Finder"
            set selectedFiles to selection as alias list
            if (count of selectedFiles) is 0 then
                return "NO_SELECTION"
            else
                return POSIX path of (item 1 of selectedFiles as text)
            end if
        end tell
        """
		result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, check=True)
		selected_path = result.stdout.strip()

		if selected_path == "NO_SELECTION":
			print("❌ 未在 Finder 中选中文件，请选择一个文件后重试！")
			return None

		print(f"🎯 Finder 当前选中的文件路径：{selected_path}")
		return selected_path

	except subprocess.CalledProcessError as e:
		print(f"❌ 获取 Finder 选中的文件失败：{e.stderr.strip()}")
		return None


def ncm_to_flac(ncm_path):
	"""NCM 文件转换为 FLAC 格式"""
	flac_path = ncm_path.replace('.ncm', '.flac')
	try:
		result = subprocess.run(['ncmdump', ncm_path], capture_output=True, text=True, check=True)
		print(f"NCM 转换 FLAC 成功 ✅: {result.stdout.strip()}")
		return flac_path
	except subprocess.CalledProcessError as e:
		print(f"NCM 转换 FLAC 失败 ❌: {e.stderr.strip()}")
		return None


def extract_cover(flac_path, output_dir):
	"""从 FLAC 文件提取专辑封面"""
	cover_path = Path(output_dir) / (Path(flac_path).stem + "_cover.jpg")
	try:
		# 检查是否有封面
		result = subprocess.run(['ffprobe', '-i', flac_path, '-show_streams', '-select_streams', 'v'],
		                        capture_output=True, text=True)
		if 'codec_type=video' not in result.stdout:
			print("未找到封面图片 ⚠️")
			return None

		# 提取封面
		subprocess.run([
			'ffmpeg', '-i', flac_path,
			'-map', '0:v:0',  # 映射第一个视频流（封面图）
			'-c:v', 'mjpeg',
			'-f', 'image2', str(cover_path),
			'-loglevel', 'quiet'
		], check=True)
		print(f"封面提取成功 ✅: {cover_path}")
		return str(cover_path)
	except subprocess.CalledProcessError as e:
		print(f"封面提取失败 ❌: {e.stderr.strip()}")
		return None


def flac_to_alac(flac_path):
	"""FLAC 转换为 ALAC (M4A) 格式"""
	m4a_path = flac_path.replace('.flac', '.m4a')
	try:
		subprocess.run([
			'ffmpeg', '-i', flac_path,
			'-map', '0:a',
			'-map', '0:v?',  # 映射封面图（如果存在）
			'-c:a', 'alac',
			'-c:v', 'copy',
			m4a_path,
			'-loglevel', 'quiet'
		], check=True)
		print(f"FLAC 转换 ALAC 成功 ✅")
		return m4a_path
	except subprocess.CalledProcessError as e:
		print(f"FLAC 转换 ALAC 失败 ❌: {e.stderr.strip()}")
		return None


def main():
	# 从 Finder 获取当前选中的文件路径
	ncm_path = get_selected_finder_file()
	if not ncm_path:
		return

	# 检查是否为 .ncm 文件
	if not ncm_path.endswith('.ncm'):
		print(f"❌ 选中的文件不是 NCM 文件：{ncm_path}")
		return

	# 确认文件是否存在
	if not os.path.isfile(ncm_path):
		print(f"❌ 文件不存在：{ncm_path}")
		return

	print("🎵 开始处理音频文件...")

	# 第一步：NCM -> FLAC
	print("\n1. NCM 转换为 FLAC:")
	flac_path = ncm_to_flac(ncm_path)
	if not flac_path:
		print("❌ 转换失败，终止处理！")
		return

	# 第二步：提取封面
	print("\n2. 提取封面:")
	output_dir = os.path.dirname(flac_path)
	cover_path = extract_cover(flac_path, output_dir)

	# 第三步：FLAC -> ALAC
	print("\n3. FLAC 转换为 ALAC:")
	m4a_path = flac_to_alac(flac_path)
	if not m4a_path:
		print("❌ 转换失败，终止处理！")
		return

	# 最终结果
	print("\n🎉 任务完成！输出文件如下：")
	print(f"FLAC 文件: {flac_path}")
	print(f"ALAC 文件: {m4a_path}")
	if cover_path:
		print(f"专辑封面: {cover_path}")


if __name__ == '__main__':
	main()