..\.venv\Scripts\pyinstaller.exe --noconfirm --clean --windowed -i "../resources/icon.ico" ^
--add-data "../resources;resources/" ^
--add-data "../README.md;." --add-data "../README.html;." ^
--distpath "C:/Users/pasto/Desktop/output" ^
--workpath "C:\Users\pasto\Desktop\output\work" ^
--name="Weekly Giving" ../weekly_giving.py