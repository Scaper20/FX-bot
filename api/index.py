"""Vercel entry point: the whole website is one Python (Flask) function."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from web.app import create_app  # noqa: E402

app = create_app()
