#!/bin/zsh

# Get package requirements
pip3 install -r requirements.txt

# Generate app
pyinstaller ../scraper.py

# Delete old scraper.app
rm -r ./SearchifyX/scraper

# Copy newest scraper.app
cp -R ./dist/scraper ./SearchifyX/
