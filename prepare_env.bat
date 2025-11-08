@echo off
python -m venv .venv-obv-study\
echo Virtual environment created!
call ".venv-obv-study\Scripts\activate.bat"
echo Virtual environment activated!
pip install -r requirements.txt
