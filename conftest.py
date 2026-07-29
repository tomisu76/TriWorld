"""Pytest configuration: ensure project .venv packages take priority over hermes-agent venv."""

import sys
import os

# Remove hermes-agent venv from sys.path so project .venv packages are used
sys.path = [p for p in sys.path if 'hermes-agent' not in p]

# Ensure project packages are importable
project_root = os.path.dirname(os.path.abspath(__file__))
packages_dir = os.path.join(project_root, 'packages')
if packages_dir not in sys.path:
    sys.path.insert(0, packages_dir)
