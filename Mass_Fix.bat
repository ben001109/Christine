@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================
echo  Christine  Mass_Fix  ^|  大量語法修復
echo ============================================
echo.
echo  1. 會先備份 christine_final.py -^> .bak.YYYYMMDD_HHMMSS
echo  2. 移除已知亂碼 (注音字 / 連續分號)
echo  3. 補齊所有空 block 的 pass
echo  4. 反覆 ast.parse 修復剩餘語法錯誤
echo  5. 輸出 _fix_report.txt
echo.
echo  執行中... (檔案 120k 行，約需 10~60 秒)
echo.
"C:\Users\josh1\AppData\Local\Programs\Python\Python313\python.exe" -X utf8 "%~dp0Mass_Fix.py"
echo.
echo ============================================
echo  完成。請把 _fix_report.txt 尾部的 RESULT 貼給我
echo ============================================
pause
