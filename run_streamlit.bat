@echo off
echo ========================================
echo  SINEMA RAG Chatbot - Streamlit UI
echo  Universitas Tadulako
echo ========================================
echo.

REM Activate virtual environment if exists
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
    echo [OK] Virtual environment activated
) else (
    echo [!] No virtual environment found, using system Python
)

echo.
echo Starting Streamlit server...
echo Open browser: http://localhost:8501
echo.

streamlit run streamlit_app.py --server.port 8501

pause
