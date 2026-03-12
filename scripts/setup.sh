#!/bin/bash
 # script to setup the development environment for the project, creates a virtual environment and installs dependencies
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt -r requirements-dev.txt
pip install -e .

echo "Setup complete."