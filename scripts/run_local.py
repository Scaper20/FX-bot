"""Run the website on your own computer with replayed history (no API key needed).

    python scripts/run_local.py                  # http://127.0.0.1:5000, password: local
    python scripts/run_local.py --now "2024-03-12 10:30"

Data is saved in scratch file local_store.json (git-ignored)."""
import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

ap = argparse.ArgumentParser()
ap.add_argument("--now", default="2024-03-12 10:30", help="replayed 'current time' (UTC)")
ap.add_argument("--port", type=int, default=5000)
ap.add_argument("--store", default=str(ROOT / "local_store.json"))
a = ap.parse_args()
os.environ.setdefault("LOCAL_DEV", "1")
os.environ.setdefault("FEED", "replay")
os.environ.setdefault("LOCAL_STORE_FILE", a.store)

import pandas as pd  # noqa: E402

from web.app import create_app  # noqa: E402
from web.store import MemoryStore  # noqa: E402

state = {"now": pd.Timestamp(a.now, tz="UTC")}
app = create_app(store=MemoryStore(a.store), now_fn=lambda: state["now"])
app.run(host="127.0.0.1", port=a.port, debug=False)
