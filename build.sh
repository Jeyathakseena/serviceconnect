#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Gather all CSS and Images
python manage.py collectstatic --no-input

# Update database
python manage.py migrate