#!/bin/bash

if [ -f ".venv-obv-study/bin/activate" ]; then
    # Activate the virtual environment
    source .venv-obv-study/bin/activate
    echo "Virtual environment activated!"
    exec bash
else
    echo "Virtual environment not found!"
    read -p "Press Enter to continue..."
fi