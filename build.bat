@echo off
echo ��������ɵĹ����ļ�...
rmdir /s /q build
rmdir /s /q dist
del /q *.spec

echo ���ڰ�װ����...
pip install -r requirements.txt
pip install pyinstaller

echo ���ڴ��...
pyinstaller --name=PortalPlayer ^
            --onefile ^
            --icon=assets/icon.ico ^
            --add-data "assets/*;assets" ^
            --hidden-import=pygame ^
            --hidden-import=pydub ^
            --hidden-import=PIL ^
            main.py

echo �����ɣ�
echo ��ִ���ļ�λ�� dist/PortalPlayer.exe
pause 