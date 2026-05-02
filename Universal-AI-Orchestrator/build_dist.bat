@echo off
echo 🚀 Починаємо збірку Universal AI Orchestrator v1.1.0 (Protected)
echo -----------------------------------------------------------

:: 1. Перевірка залежностей
echo [1/4] Перевірка PyArmor та PyInstaller...
pip install pyarmor pyinstaller rich python-dotenv pydantic anthropic openai --quiet

:: 2. Обфускація (IP Protection)
echo [2/4] Захист вихідного коду (Obfuscating)...
pyarmor gen orchestrator.py
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Помилка при обфускації.
    exit /b %ERRORLEVEL%
)

:: 3. Збірка .EXE (Packaging)
echo [3/4] Створення автономного .EXE файлу...
pyinstaller --onefile --noconsole --name "Universal-AI-Orchestrator" dist/orchestrator.py
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Помилка при збірці EXE.
    exit /b %ERRORLEVEL%
)

:: 4. Фіналізація
echo [4/4] Створення фінального пакету...
mkdir "GM_Package_v1.1"
copy "dist\Universal-AI-Orchestrator.exe" "GM_Package_v1.1\"
copy "README.md" "GM_Package_v1.1\"
copy "TERMS_OF_USE.md" "GM_Package_v1.1\"

echo -----------------------------------------------------------
echo ✅ Збірка завершена! Файл у папці: GM_Package_v1.1
pause
