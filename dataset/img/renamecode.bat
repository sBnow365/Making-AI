@echo off
setlocal enabledelayedexpansion

:: Set starting number
set /a counter=301

:: Get list of image files sorted by creation time
for /f "delims=" %%F in ('dir /b /a:-d /o:d *.png') do (
    ren "%%F" "!counter!.png"
    set /a counter+=1
)

echo Done!
pause