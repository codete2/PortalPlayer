import sys
import os
import time
import shutil
import pygame
import re
from datetime import datetime
import threading
from pydub import AudioSegment
from PIL import Image
import numpy as np
from io import StringIO
import zipfile
import tempfile
import json
from pathlib import Path

pygame.mixer.init()

def get_terminal_size():
    # 获取终端窗口大小
    terminal_size = shutil.get_terminal_size()
    return terminal_size.columns, terminal_size.lines

def check_terminal_size():
    width, height = get_terminal_size()
    
    if os.name == 'nt':  # Windows系统
        # 设置窗口最大化，使用较小的值以确保兼容性
        os.system('mode con cols=190 lines=50')
        os.system('powershell -command "&{$Host.UI.RawUI.WindowSize=New-Object System.Management.Automation.Host.Size(190,50)}"')
        # 全屏
        import ctypes
        kernel32 = ctypes.WinDLL('kernel32')
        user32 = ctypes.WinDLL('user32')
        SW_MAXIMIZE = 3
        hwnd = kernel32.GetConsoleWindow()
        user32.ShowWindow(hwnd, SW_MAXIMIZE)
    else:  # Unix系统
        os.system('resize -s 50 190')  # 设置终端大小
    
    # 再次检查大小是否满足要求
    width, height = get_terminal_size()
    required_width = 80
    required_height = 25
    
    if width < required_width or height < required_height:
        print(f"请确保窗口已最大化")
        print(f"当前窗口大小: {width}x{height}")
        print(f"需要的最小尺寸: {required_width}x{required_height}")
        return False
    return True

def set_window_title():
    if os.name == 'nt':
        os.system('title Portal Player')
    else:
        sys.stdout.write('\x1b]2;Portal Player\x07')

def clear_screen():
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')

def draw_rectangles():
    width, height = get_terminal_size()
    left_width = width // 2 - 4
    right_width = width // 2 - 4
    right_start = width // 2 + 2
    
    ORANGE = "\033[38;5;214m"
    RESET = "\033[0m"
    
    # 绘制左边框
    print(f"{ORANGE}+" + "-" * left_width + f"+{RESET}")
    for _ in range(height - 4):
        print(f"{ORANGE}|" + " " * left_width + f"|{RESET}")
    print(f"{ORANGE}+" + "-" * left_width + f"+{RESET}")
    
    # 绘制右边框（只占上半部分）
    print(f"\033[1;{right_start}H{ORANGE}+" + "-" * right_width + f"+{RESET}")
    for i in range(2, height // 2):
        print(f"\033[{i};{right_start}H{ORANGE}|" + " " * right_width + f"|{RESET}")
    print(f"\033[{height//2};{right_start}H{ORANGE}+" + "-" * right_width + f"+{RESET}")

def display_right_text(right_text_path, song_duration=None):
    try:
        with open(right_text_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        width, height = get_terminal_size()
        right_width = width // 2 - 6
        right_start_x = width // 2 + 4
        current_line = 2
        max_lines = height // 2 - 2
        ORANGE = "\033[38;5;214m"
        RESET = "\033[0m"
        
        # 计算延迟时间
        chars = list(text)
        total_chars = len(chars)
        if song_duration:
            CHAR_DELAY = (song_duration / (total_chars * 2.5))
            if CHAR_DELAY < 0.03:
                CHAR_DELAY = 0.03
        else:
            CHAR_DELAY = 0.03
        
        current_pos = right_start_x
        buffer = []  # 用于存储每个字符的位置信息
        
        # 先计算每个字符的位置
        for char in chars:
            if char == '\n' or current_pos >= (width - 4):
                current_line += 1
                current_pos = right_start_x
                if char == '\n':
                    continue
            
            if current_line >= max_lines:
                # 清除右上区域并等待一小段时间
                for i in range(2, max_lines):
                    print(f"\033[{i};{right_start_x}H{' ' * (right_width-2)}")
                time.sleep(0.1)  # 给用户一个短暂的时间看到前面的内容
                current_line = 2
                current_pos = right_start_x
            
            buffer.append((current_line, current_pos, char))
            current_pos += 2 if is_full_width(char) else 1
        
        # 显示文本，不循环
        last_line = 2  # 记录上一次显示的行号
        for line, pos, char in buffer:
            if not pygame.mixer.music.get_busy():
                return
            
            # 如果行号变小了，说明是换页，需要清屏
            if line < last_line:
                for i in range(2, max_lines):
                    print(f"\033[{i};{right_start_x}H{' ' * (right_width-2)}")
                time.sleep(0.1)  # 给用户一个短暂的时间看到前面的内容
            
            print(f"\033[{line};{pos}H{ORANGE}{char}{RESET}", end='', flush=True)
            time.sleep(CHAR_DELAY)
            last_line = line
            
    except Exception as e:
        print(f"\033[{height-1};1H读取右侧文本时出错：{str(e)}")

def display_portal_style(text):
    ORANGE = "\033[38;5;214m"
    RESET = "\033[0m"
    
    draw_rectangles()
    
    # 将光标移动到矩形框内部显示内容
    print(f"\033[5;2H{ORANGE}" + "=" * 46 + RESET)
    print(f"\033[6;2H{ORANGE}   APERTURE SCIENCE MUSIC PLAYER v1.0{RESET}")
    print(f"\033[7;2H{ORANGE}" + "=" * 46 + RESET)
    print(f"\033[9;2H{ORANGE}Now Playing:{RESET}")
    print(f"\033[10;2H{ORANGE}>> {text}{RESET}")
    print(f"\033[12;2H{ORANGE}[", end='', flush=True)
    for i in range(40):
        print("=", end='', flush=True)
        time.sleep(0.05)
    print(f"]{RESET}")
    print(f"\033[14;2H{ORANGE}Status: Playing...{RESET}")
    print(f"\033[16;2H{ORANGE}Press Ctrl+C to exit{RESET}")

def parse_lrc(file_path):
    lyrics = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
            # 析所有时间戳和歌词
            current_text = ""
            current_time = 0
            
            for line in lines:
                match = re.match(r'\[(\d{2}):(\d{2})[:.]([\d]{2,3})\](.*)', line)
                if match:
                    minutes, seconds, milliseconds, text = match.groups()
                    if len(milliseconds) == 3:
                        milliseconds = int(milliseconds) / 1000
                    else:
                        milliseconds = int(milliseconds) / 100
                    
                    time_in_seconds = int(minutes) * 60 + int(seconds) + milliseconds
                    
                    # 如果有新的文本，保存当前文本和时间
                    if text.strip():
                        if current_text:
                            lyrics.append((current_time, current_text.strip()))
                        current_text = text
                        current_time = time_in_seconds
            
            # 保存最后一句歌词
            if current_text:
                lyrics.append((current_time, current_text.strip()))
    
    except Exception as e:
        print(f"解析歌词文件时出错：{str(e)}")
    
    if not lyrics:
        print("警告：没有解析到任何歌词")
    
    return sorted(lyrics, key=lambda x: x[0])

def play_music(music_path):
    try:
        pygame.init()  # 初始化所有pygame模块
        pygame.mixer.init(frequency=44100)  # 初始化音频，设置采样率
        pygame.mixer.music.set_volume(1.0)  # 设置音���
        pygame.mixer.music.load(music_path)
        pygame.mixer.music.play()
    except Exception as e:
        print(f"播放音乐时出错：{str(e)}")

def is_full_width(char):
    """判断字符是否是全角字符"""
    return ord(char) > 0x1100 and any([
        ord(char) <= 0x115f,  # Hangul Jamo
        ord(char) >= 0x2e80 and ord(char) <= 0x9fff,  # CJK
        ord(char) >= 0xac00 and ord(char) <= 0xd7af,  # Hangul Syllables
        ord(char) >= 0xf900 and ord(char) <= 0xfaff,  # CJK Compatibility Ideographs
        ord(char) >= 0xfe30 and ord(char) <= 0xfe4f,  # CJK Compatibility Forms
        ord(char) >= 0xff00 and ord(char) <= 0xff60,  # Fullwidth Forms
        ord(char) >= 0xffe0 and ord(char) <= 0xffe6   # Fullwidth Forms
    ])

def display_lyrics_in_box(lyrics):
    if not lyrics:
        print("\033[2;2H\033[38;5;214m没有找到歌词\033[0m")
        return
        
    width, height = get_terminal_size()
    left_width = width // 2 - 6
    current_line = 2
    max_lines = height - 4
    ORANGE = "\033[38;5;214m"
    RESET = "\033[0m"
    MIN_CHAR_DELAY = 0.03
    MIN_TIME_INTERVAL = 0.5
    
    start_time = time.time()
    print(f"\033[2;2H{ORANGE}正在等待歌词...{RESET}")
    
    # 计算平均显示速度
    total_chars = 0
    total_time = 0
    for i in range(len(lyrics)-1):
        chars = sum(2 if is_full_width(c) else 1 for c in lyrics[i][1])
        time_diff = lyrics[i+1][0] - lyrics[i][0]
        if time_diff >= MIN_TIME_INTERVAL:
            total_chars += chars
            total_time += time_diff
    
    avg_char_delay = (total_time / total_chars) if total_chars > 0 else MIN_CHAR_DELAY
    
    for i, (timestamp, text) in enumerate(lyrics):
        next_timestamp = lyrics[i + 1][0] if i < len(lyrics) - 1 else timestamp + 5
        time_interval = next_timestamp - timestamp
        
        current_time = time.time() - start_time
        if current_time < timestamp:
            time.sleep(timestamp - current_time)
        
        if current_line >= max_lines:
            # 清除所有歌词显示区域
            for line in range(2, max_lines):
                print(f"\033[{line};2H{' ' * left_width}")
            current_line = 2
        
        # 清除当前行
        print(f"\033[{current_line};2H{' ' * left_width}")
        
        # 计算这句歌词的总字符宽度和字符延迟
        total_width = sum(2 if is_full_width(c) else 1 for c in text)
        total_chars = sum(2 if is_full_width(c) else 1 for c in text)
        char_delay = max(MIN_CHAR_DELAY, min(avg_char_delay, time_interval / (total_chars * 1.2)))
        
        # 如果一行��不下，需要分行显示
        if total_width > left_width - 2:
            current_width = 0
            line_text = ""
            display_pos = 2  # 当前行的显示位置
            
            for char in text:
                char_width = 2 if is_full_width(char) else 1
                if current_width + char_width > left_width - 2:
                    # 打印当前行
                    display_pos = 2
                    for c in line_text:
                        print(f"\033[{current_line};{display_pos}H{ORANGE}{c}{RESET}", end='', flush=True)
                        display_pos += 2 if is_full_width(c) else 1
                        time.sleep(char_delay)
                    
                    current_line += 1
                    if current_line >= max_lines:
                        # 如果到达底部，清屏并重置到顶部
                        for line in range(2, max_lines):
                            print(f"\033[{line};2H{' ' * left_width}")
                        current_line = 2
                    
                    line_text = char
                    current_width = char_width
                else:
                    line_text += char
                    current_width += char_width
            
            # 打印最后一行
            if line_text:
                display_pos = 2
                for c in line_text:
                    print(f"\033[{current_line};{display_pos}H{ORANGE}{c}{RESET}", end='', flush=True)
                    display_pos += 2 if is_full_width(c) else 1
                    time.sleep(char_delay)
                current_line += 1
        else:
            # 逐字打印整行
            display_pos = 2
            for char in text:
                print(f"\033[{current_line};{display_pos}H{ORANGE}{char}{RESET}", end='', flush=True)
                display_pos += 2 if is_full_width(char) else 1
                time.sleep(char_delay)
            current_line += 1
        
        # 等待到下一句歌词的时间
        remaining_time = next_timestamp - (time.time() - start_time)
        if remaining_time > 0:
            time.sleep(remaining_time)

def image_to_ascii(image_path, max_width, max_height):
    """将图片转换为彩色ASCII字符画"""
    # 扩充ASCII字符集，从密到稀疏
    ASCII_CHARS = "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\|()1{}[]?-_+~<>i!lI;:,\"^`'. "
    
    try:
        # 打开图片
        image = Image.open(image_path)
        
        # 强伸图片到指定大小
        new_width = max_width
        new_height = max_height
        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # 获取RGB数据
        pixels = list(image.getdata())
        ascii_str = StringIO()
        
        # 逐像素转换
        for i, pixel in enumerate(pixels):
            if i % new_width == 0 and i != 0:
                ascii_str.write('\n')
            
            if isinstance(pixel, int):  # 灰度图
                r = g = b = pixel
            else:  # RGB图
                r, g, b = pixel[:3]
            
            # 计算灰度值
            brightness = (r + g + b) / 3
            # 选择ASCII字符
            char_index = int((brightness / 255) * (len(ASCII_CHARS) - 1))
            char = ASCII_CHARS[char_index]
            
            # 直接使用原始颜色
            color = f"\033[38;2;{r};{g};{b}m"
            
            # 每个字符重复两次以填充空间
            ascii_str.write(f"{color}{char}{char}\033[0m")
        
        return ascii_str.getvalue()
        
    except Exception as e:
        print(f"转换图片时出错：{str(e)}")
        return None

def display_media_in_box(media_list, song_duration):
    """在右下方显示媒体内容"""
    try:
        width, height = get_terminal_size()
        right_width = width // 2 - 6
        right_start_x = width // 2 + 4
        start_line = height // 2 + 1
        max_lines = height - 4
        ORANGE = "\033[38;5;214m"
        RESET = "\033[0m"
        
        # 计算实际可用的显示区域（考虑到每个字符是两倍宽）
        display_width = right_width // 2  # 因为每个ASCII字符会重复两次
        display_height = max_lines - start_line
        
        while pygame.mixer.music.get_busy():
            for media_path in media_list:
                if not pygame.mixer.music.get_busy():
                    return
                
                # 清除显示区域
                for i in range(start_line, max_lines):
                    print(f"\033[{i};{right_start_x}H{' ' * (right_width-2)}")
                
                # 根据文件类型处理
                if media_path.lower().endswith(('.txt')):
                    try:
                        with open(media_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                    except Exception as e:
                        print(f"读取文件出错：{str(e)}")
                        continue
                elif media_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    # 转换图片为ASCII，确保完全填满显示区域
                    content = image_to_ascii(media_path, display_width, display_height)
                    if not content:
                        continue
                else:
                    continue
                
                # 显示内容
                current_line = start_line
                for line in content.split('\n'):
                    if current_line >= max_lines:
                        break
                    # 确保每行都填满整个宽度
                    padded_line = line.ljust(right_width-2)
                    print(f"\033[{current_line};{right_start_x}H{ORANGE}{padded_line}{RESET}")
                    current_line += 1
                
                # 等待指定时间
                display_end_time = time.time() + 20
                while time.time() < display_end_time and pygame.mixer.music.get_busy():
                    time.sleep(0.1)
                
    except Exception as e:
        print(f"\033[{height-1};1H显示媒体内容时出错：{str(e)}")

def extract_song_package(zip_path):
    """解压并解析歌曲包"""
    try:
        temp_dir = tempfile.mkdtemp()
        print(f"创建临时目录: {temp_dir}")
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # 打印所有文件列表
            print("压缩包中的文件:")
            namelist = zip_ref.namelist()
            for name in namelist:
                try:
                    # 尝试使用 gbk 解码
                    decoded_name = name.encode('cp437').decode('gbk')
                except:
                    # 如果失败，假设已经是 utf-8
                    decoded_name = name
                print(f"  - {decoded_name}")
            
            if 'config.json' not in namelist:
                raise Exception("歌曲包中缺少 config.json 文件")
            
            # 先解压有文件，保持原始文件名
            print("开始解压文件...")
            zip_ref.extractall(temp_dir)
            print("文件解压完成")
            
            # 读取配置文件
            config_path = os.path.join(temp_dir, 'config.json')
            print(f"读取配置文件: {config_path}")
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print("配置文件内容:", config)
            
            # 重命名文件
            print("\n重命名文件:")
            for name in namelist:
                if name == 'config.json':
                    continue
                    
                try:
                    # 获取原始文件路径和目标文件路径
                    old_path = os.path.join(temp_dir, name)
                    decoded_name = name.encode('cp437').decode('gbk')
                    new_path = os.path.join(temp_dir, decoded_name)
                    
                    if old_path != new_path and os.path.exists(old_path):
                        print(f"  {name} -> {decoded_name}")
                        # 如果目标文件已存在，先删除
                        if os.path.exists(new_path):
                            os.remove(new_path)
                        os.rename(old_path, new_path)
                except:
                    print(f"  保持原名: {name}")
            
            # 构建完整路径，确保路径存在
            music_path = os.path.join(temp_dir, config['music'])
            lyrics_path = os.path.join(temp_dir, config['lyrics'])
            
            print(f"\n检查文件是否存在:")
            print(f"音乐文件: {music_path} - {'存在' if os.path.exists(music_path) else '不存在'}")
            print(f"歌词文件: {lyrics_path} - {'存在' if os.path.exists(lyrics_path) else '不存在'}")
            
            if not os.path.exists(music_path):
                raise Exception(f"找不到音乐文件: {config['music']}")
            if not os.path.exists(lyrics_path):
                raise Exception(f"找不到歌词文件: {config['lyrics']}")
            
            right_text_path = None
            if config.get('right_text'):
                right_text_path = os.path.join(temp_dir, config['right_text'])
                if not os.path.exists(right_text_path):
                    print(f"警告: 找不到右侧文本文件: {config['right_text']}")
                    right_text_path = None
            
            # 处理媒体列表
            media_list = []
            if 'media' in config:
                for media_file in config['media']:
                    media_path = os.path.join(temp_dir, media_file)
                    if os.path.exists(media_path):
                        media_list.append(media_path)
                    else:
                        print(f"警告: 找不到媒体文件: {media_file}")
            
            return {
                'temp_dir': temp_dir,
                'music_path': music_path,
                'lyrics_path': lyrics_path,
                'right_text_path': right_text_path,
                'media_list': media_list
            }
            
    except Exception as e:
        print(f"解析歌曲包时出错：{str(e)}")
        if 'temp_dir' in locals():
            shutil.rmtree(temp_dir)
        return None

def parse_arguments():
    args = sys.argv[1:]
    music_path = None
    lrc_path = None
    right_text_path = None
    media_list = []
    song_package = None
    
    i = 0
    while i < len(args):
        if args[i] == "-package" and i + 1 < len(args):
            song_package = args[i + 1]
            i += 2
        elif args[i] == "-music" and i + 1 < len(args):
            music_path = args[i + 1]
            i += 2
        elif args[i] == "-lrc" and i + 1 < len(args):
            lrc_path = args[i + 1]
            i += 2
        elif args[i] == "--rightxt" and i + 1 < len(args):
            right_text_path = args[i + 1]
            i += 2
        elif args[i] == "--img" and i + 1 < len(args):
            i += 1
            while i < len(args) and not args[i].startswith('-'):
                media_list.append(args[i])
                i += 1
        else:
            i += 1
    
    return music_path, lrc_path, right_text_path, media_list, song_package

def convert_to_mp3(input_path):
    """将频文转换为mp3格式"""
    try:
        # 获取输入文件的目录和文件名
        directory = os.path.dirname(input_path)
        filename = os.path.basename(input_path)
        name_without_ext = os.path.splitext(filename)[0]
        
        # 创建输出文件路径
        output_path = os.path.join(directory, f"{name_without_ext}.mp3")
        
        # 如果输出文件已存在，直接返回路径
        if os.path.exists(output_path):
            return output_path
            
        # 音频文件
        audio = AudioSegment.from_file(input_path)
        
        # 导出为mp3
        audio.export(output_path, format="mp3")
        return output_path
        
    except Exception as e:
        print(f"转换音频文件时出错：{str(e)}")
        return None

def set_terminal_properties():
    if os.name == 'nt':  # Windows系统
        if 'POWERSHELL_DISTRIBUTION_CHANNEL' in os.environ:  # PowerShell
            # 使用 PowerShell 命令设置背景色
            os.system('powershell -command "$Host.UI.RawUI.BackgroundColor = \'Black\'; Clear-Host"')
        else:  # CMD
            os.system('color 0')  # 设置背景为黑色
        
        # 设置窗口最大化，使用较小的值以确保兼容性
        os.system('mode con cols=190 lines=50')
        os.system('powershell -command "&{$Host.UI.RawUI.WindowSize=New-Object System.Management.Automation.Host.Size(190,50)}"')
        # 全屏
        import ctypes
        kernel32 = ctypes.WinDLL('kernel32')
        user32 = ctypes.WinDLL('user32')
        SW_MAXIMIZE = 3
        hwnd = kernel32.GetConsoleWindow()
        user32.ShowWindow(hwnd, SW_MAXIMIZE)
    else:  # Unix系统
        os.system('tput setab 0')  # 设置背景为黑色
        os.system('resize -s 50 190')  # 设置终端大小

def main():
    if len(sys.argv) > 1:
        music_path, lrc_path, right_text_path, media_list, song_package = parse_arguments()
        
        # 如果提供了歌曲包，优先使用歌曲包
        temp_dir = None
        if song_package:
            package_info = extract_song_package(song_package)
            if package_info:
                temp_dir = package_info['temp_dir']
                music_path = package_info['music_path']
                lrc_path = package_info['lyrics_path']
                right_text_path = package_info['right_text_path']
                media_list = package_info['media_list']
            else:
                print("歌曲包解析失败")
                return
        
        if music_path or lrc_path:
            try:
                clear_screen()
                set_terminal_properties()
                set_window_title()
                
                if not check_terminal_size():
                    return
                
                if music_path.lower().endswith('.flac'):
                    print("正在转换音频文件...")
                    converted_path = convert_to_mp3(music_path)
                    if converted_path:
                        music_path = converted_path
                        clear_screen()  # 转换完成后清屏
                    else:
                        print("音频转换失败")
                        return
                
                # 获取音乐时长
                audio = AudioSegment.from_file(music_path)
                song_duration = len(audio) / 1000.0
                
                # 先绘制框架
                draw_rectangles()
                lyrics = parse_lrc(lrc_path)
                
                # 启动音乐播放
                music_thread = threading.Thread(target=play_music, args=(music_path,))
                music_thread.start()
                
                # 等待一小段时间确保音乐开始播放
                time.sleep(0.5)
                
                # 启动右侧文本显示
                if right_text_path:
                    right_text_thread = threading.Thread(target=display_right_text, args=(right_text_path, song_duration))
                    right_text_thread.start()
                
                # 启媒体显示
                if media_list:
                    media_thread = threading.Thread(target=display_media_in_box, args=(media_list, song_duration))
                    media_thread.start()
                
                # 显示歌词
                display_lyrics_in_box(lyrics)
                
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
                
                clear_screen()
                    
            except KeyboardInterrupt:
                pygame.mixer.music.stop()
                pygame.mixer.quit()
                pygame.quit()
                clear_screen()
                print("\nGoodbye!")
                time.sleep(1)
            finally:
                # 清理临时文
                if temp_dir:
                    shutil.rmtree(temp_dir)
                # 清理 pygame
                pygame.mixer.quit()
                pygame.quit()
        else:
            print("\n🎮 Portal Player - Aperture Science 音乐测试系统")
            print("\n使用方法:")
            print("\n1. 播放单个音乐文件:")
            print('   PortalPlayer.exe -music "音乐文件" -lrc "歌词文件" [--rightxt "右侧文本"] [--img "图片1" "图片2" ...]')
            print("\n2. 使用歌曲包:")
            print('   PortalPlayer.exe -package "歌曲包.zip"')
            print("\n参数说明:")
            print("   -music    音乐文件路径 (支持 MP3, FLAC)")
            print("   -lrc      歌词文件路径 (LRC 格式)")
            print("   --rightxt 右侧显示文本 (可选)")
            print("   --img     图片或文本文件列表 (可选)")
            print("   -package  歌曲包文件路径 (ZIP 格式)")
            print("\n示例:")
            print('   PortalPlayer.exe -music "test.mp3" -lrc "test.lrc"')
            print('   PortalPlayer.exe -package "song.zip"')
            print("\n注意:")
            print("   1. 建议在全屏终端中运行")
            print("   2. 按 Ctrl+C 可随时退出")
            print("   3. 支持中文路径")
            print("\nThe cake is a lie, but the music is real! - GLaDOS\n")
    else:
        print("\n🎮 Portal Player - Aperture Science 音乐测试系统")
        print("\n使用方法:")
        print("\n1. 播放单个音乐文件:")
        print('   PortalPlayer.exe -music "音乐文件" -lrc "歌词文件" [--rightxt "右侧文本"] [--img "图片1" "图片2" ...]')
        print("\n2. 使用歌曲包:")
        print('   PortalPlayer.exe -package "歌曲包.zip"')
        print("\n参数说明:")
        print("   -music    音乐文件路径 (支持 MP3, FLAC)")
        print("   -lrc      歌词文件路径 (LRC 格式)")
        print("   --rightxt 右侧显示文本 (可选)")
        print("   --img     图片或文本文件列表 (可选)")
        print("   -package  歌曲包文件路径 (ZIP 格式)")
        print("\n示例:")
        print('   PortalPlayer.exe -music "test.mp3" -lrc "test.lrc"')
        print('   PortalPlayer.exe -package "song.zip"')
        print("\n注意:")
        print("   1. 建议在全屏终端中运行")
        print("   2. 按 Ctrl+C 可随时退出")
        print("   3. 支持中文路径")
        print("\nThe cake is a lie, but the music is real! - GLaDOS\n")

if __name__ == "__main__":
    main()
