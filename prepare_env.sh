#!/bin/bash

python3 -m venv .venv-obv-study
echo "Virtual environment created!"
source .venv-obv-study/bin/activate
echo "Virtual environment activated!"
pip install -r requirements.txt