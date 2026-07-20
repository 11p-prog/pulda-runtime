#!/bin/bash
set -e

# Reinstall Python dependencies (idempotent)
pip install -r requirements.txt
