move "gallery-dl.conf" "%USERPROFILE%\gallery-dl.conf"
cd /d "C:\Windows\System32"
pip install --upgrade pip setuptools wheel
pip install -U gallery-dl
pip install -U -I --no-deps --no-cache-dir https://github.com/mikf/gallery-dl/archive/master.tar.gz
cd %USERPROFILE%
pause