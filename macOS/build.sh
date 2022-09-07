#!/bin/zsh

# Get package requirements
pip3 install -r requirements.txt

# Create setup.py file
py2applet --make-setup ../scraper.py

# Generate app
python3 setup.py py2app

# Delete old scraper.app
rm -r ./SearchifyX/scraper.app

# Copy newest scraper.app
cp -R ./dist/scraper.app ./SearchifyX/