..\venv\Scripts\pyinstaller.exe --noconfirm --clean --windowed -i "../resources/icon.ico" ^
--add-data "../resources;resources/" ^
--distpath "C:/Users/pasto/Desktop/output" ^
--workpath "C:\Users\pasto\Desktop\output\work" ^
--name="Weekly Giving" ../weekly_giving.py