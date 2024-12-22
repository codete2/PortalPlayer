@echo off
echo 正在清理旧的构建文件...
rmdir /s /q build
rmdir /s /q dist
del /q *.spec

echo 正在安装依赖...
pip install -r requirements.txt
pip install pyinstaller

echo 正在打包...
pyinstaller --name=PortalPlayer ^
            --onefile ^
            --icon=assets/icon.ico ^
            --add-data "assets/*;assets" ^
            --hidden-import=pygame ^
            --hidden-import=pydub ^
            --hidden-import=PIL ^
            main.py

echo 打包完成！
echo 可执行文件位于 dist/PortalPlayer.exe
pause 