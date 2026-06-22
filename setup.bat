@echo off
echo ================================
echo    DevScan AI Setup
echo ================================
echo.
echo Step 1: Checking Ollama...
ollama list >nul 2>&1
if %errorlevel% neq 0 (
    echo Ollama not found. Please install from ollama.com
    pause
    exit
)
echo Ollama found.
echo.
echo Step 2: Pulling AI model (5GB - first time only)...
ollama pull qwen2.5-coder:7b
echo.
echo Step 3: Starting DevScan AI...
start /B ollama serve
timeout /t 3 /nobreak > nul
start http://localhost:8501
streamlit run app.py