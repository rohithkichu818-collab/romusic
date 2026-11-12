@echo off
echo ========================================================
echo       ROMUSIC -- Auto GitHub Push Tool
echo ========================================================
echo.

git status --short
echo.
set /p commit_msg="Enter commit message (Press Enter for 'Update ROMUSIC platform'): "
if "%commit_msg%"=="" set commit_msg=Update ROMUSIC platform

echo.
echo [1/3] Staging changes...
git add .

echo [2/3] Committing changes...
git commit -m "%commit_msg%"

echo [3/3] Pushing to GitHub...
git push -u origin main

if %errorlevel% neq 0 (
    echo.
    echo ----------------------------------------------------
    echo If push failed, make sure your GitHub remote is set:
    echo   git remote add origin https://github.com/YOUR_USERNAME/romusic.git
    echo   git branch -M main
    echo   git push -u origin main
    echo ----------------------------------------------------
) else (
    echo.
    echo ========================================================
    echo SUCCESS! Changes pushed to GitHub!
    echo Render will now automatically redeploy your site.
    echo GitHub Actions will build a new ROMUSIC.apk!
    echo ========================================================
)

pause
