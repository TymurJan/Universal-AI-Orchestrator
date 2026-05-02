@echo off
:: Set UTF-8 encoding for Cyrillic support
chcp 65001 >nul

echo ===================================================
echo   UNIVERSAL AI ORCHESTRATOR - GITHUB UPLOADER
echo ===================================================
echo.
echo ПІДКАЗКА: Щоб вставити посилання, натисніть ПРАВУ КНОПКУ МИШІ або Ctrl+V.
echo Посилання: https://github.com/TymurJan/Universal-AI-Orchestrator.git
echo.

set /p repo_url="👉 Вставте посилання тут і натисніть ENTER: "

if "%repo_url%"=="" (
    echo [ПОМИЛКА] Ви не ввели посилання.
    pause
    exit /b
)

echo.
echo [1/4] Ініціалізація...
git init

echo [2/4] Додавання файлів...
git add .

echo [3/4] Створення запису (Commit)...
git commit -m "Initial release: Universal AI Orchestrator v1.0.0"

echo [4/4] Завантаження на GitHub...
echo (Можливо, відкриється вікно в браузері для входу в акаунт)
git remote remove origin >nul 2>&1
git remote add origin %repo_url%
git branch -M main
git push -u origin main

echo.
echo ===================================================
echo ✅ ГОТОВО! Перевірте свій GitHub.
echo Це вікно НЕ закриється саме. Закрийте його вручну (х).
echo ===================================================
cmd /k
