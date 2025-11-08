@echo off
if exist ".venv-obv-study\Scripts\activate.bat" (
    call ".venv-obv-study\Scripts\activate.bat"
    echo Virtual environment activated!
    cmd /k
) else (
    echo Virtual environment not found!
    pause
)