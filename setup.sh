#!/bin/bash

echo "Creating a virtual environment..."
python3 -m venv tom_env/

echo "Activating the virtual environment..."
source tom_env/bin/activate

echo "Installing TOM Toolkit..."
pip install tomtoolkit

echo "Installing additional dependencies..."
pip install -r requirements.txt

echo "Setup of tomtoolit and virtual environment complete!"
echo "Now proceed to download the tidestom via git"