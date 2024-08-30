..\venv\Scripts\pyinstaller.exe --noconfirm --clean --windowed -i "../resources/icon.ico" ^
--add-data "../resources;resources/" --add-data "../reportlab;reportlab/" --add-data "../ghostscript;ghostscript/" ^
--distpath "C:/Users/pasto/Desktop/output" --name="Weekly Giving" ../weekly_giving.py