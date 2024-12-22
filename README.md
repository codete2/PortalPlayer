# 🎮 Portal Player

[English](README_en.md) | [日本語](README_ja.md) | [한국어](README_ko.md) | [Français](README_fr.md) | [Deutsch](README_de.md) | [Español](README_es.md) | 简体中文 | [繁體中文](README_zh_tw.md)

一个带有 Portal 风格的音乐播放器，支持歌词显示、文本滚动和 ASCII 艺术展示。让你的终端化身为 Aperture Science 测试室！

## ✨ 功能特点

- 🖥️ Portal 科技风格的界面设计
- 🎵 支持 MP3/FLAC 音频播放
- 📝 LRC 格式歌词同步显示
- ⌨️ 右上方文本区域支持打字机效果显示
- 🖼️ 右下方区域支持图片/文本轮播展示
- 📦 支持歌曲包功能，方便分享完整的播放内容

## 🚀 快速开始

### 安装依赖

```bash
pip install pygame pydub pillow
```

### 基本使用

1. 直接播放模式：

```bash
python main.py -music "音乐文件路径" -lrc "歌词文件路径" [--rightxt "右侧文本路径"] [--img "图片1" "图片2" "文本1" ...]
```

2. 歌曲包模式：

```bash
python main.py -package "歌曲包路径.zip"
```

## 📦 歌曲包格式

歌曲包是一个 zip 文件，用于方便地打包和分享完整的播放内容。

### 文件结构

```
song_package.zip
├── config.json      # 配置文件（必需）
├── music.mp3        # 音乐文件（必需）
├── lyrics.lrc       # 歌词文件（必需）
├── rightbar.txt     # 右侧文本（可选）
└── images/          # 媒体文件（可选）
    ├── image1.jpg
    ├── image2.png
    └── text1.txt
```

### 配置文件示例

config.json:

```json
{
    "music": "music.mp3",
    "lyrics": "lyrics.lrc",
    "right_text": "rightbar.txt",
    "media": [
        "images/image1.jpg",
        "images/image2.png",
        "images/text1.txt"
    ]
}
```

## 🖥️ 界面布局

```
+------------------------+------------------------+
|                        |                       |
|      歌词显示区域      |    右上文本显示区域   |
|                        |                       |
|                        +---------------------- +
|                        |                       |
|                        |    右下媒体显示区域   |
|                        |                       |
+------------------------+------------------------+
```

### 显示区域说明

- 📝 左侧：歌词同步显示

  - 支持自动滚动
  - 当前行高亮显示
  - 自动分行处理长文本
- ⌨️ 右上：文本打字机效果显示

  - 自动换页继续显示
  - 支持中文和全角字符
  - 速度会根据音乐长度自动调整
- 🖼️ 右下：媒体轮播区

  - 支持图片和文本混合显示
  - 图片自动转换为彩色 ASCII 艺术
  - 每20秒自动切换下一个内容

## ⚠️ 注意事项

1. 🖥️ 确保终端窗口足够��（建议全屏）
2. 🈶 完整支持中文路径和文件名
3. 🎨 图片会自动转换为彩色 ASCII 艺术风格显示
4. ⌨️ 按 Ctrl+C 可以随时退出播放
5. 🎵 支持的音频格式：MP3, FLAC（会自动转换为MP3）
6. 📝 歌词文件必须是标准的 LRC 格式

## 💻 系统要求

- 🐍 Python 3.6+
- 💿 Windows/Linux/macOS
- 🖥️ 支持 ANSI 转义序列的终端
- 🎵 ffmpeg（用于音频转换，如果需要播放 FLAC）

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📜 许可证

本项目采用 MIT 许可证。

## 🎮 玩得开心！

"The cake is a lie, but the music is real!" - GLaDOS

## 📦 (不推荐)打包为可执行文件

### 方法一：使用批处理文件（推荐）

1. 运行 `build.bat`
2. 等待打包完成
3. 可执行文件将在 `dist` 目录中生成

### 方法二：手动打包

1. 安装依赖

```bash
pip install -r requirements.txt
pip install pyinstaller
```

2. 运行打包命令

```bash
pyinstaller portal_player.spec
```

### 使用打包后的程序

直接运行 exe 文件：

```bash
PortalPlayer.exe -music "音乐文件路径" -lrc "歌词文件路径" [--rightxt "右侧文本路径"] [--img "图片1" "图片2" ...]
```

或使用歌曲包：

```bash
PortalPlayer.exe -package "歌曲��路径.zip"
```

### 注意事项

1. 🎵 如果需要播放 FLAC 格式，请确保系统安装了 ffmpeg
2. 📦 打包后的程序体积较大（约 50MB），这是因为包含了所有必要的依赖
3. 🖥️ 运行时仍然需要命令行窗口
4. 💻 建议将程序添加到系统环境变量中，方便在任何位置使用
