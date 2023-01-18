#!/bin/zsh

# Get package requirements
pip3 install -r requirements.txt

# Generate app
mkdir ./SearchifyX/scraper
python3 -m PyInstaller --noconfirm ../scraper.py

# Delete old scraper.app
rm -r ./SearchifyX/scraper

# Copy newest scraper.app
cp -R ./dist/scraper ./SearchifyX/
