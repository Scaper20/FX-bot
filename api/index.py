"""Vercel entry point: the whole website is one Python (Flask) function.

vercel.json rewrites every path to /api/index?__path=/<original path>. The small wrapper
below puts the original path back before Flask sees the request, so routing works the
same on Vercel as locally."""
import sys
from pathlib import Path
from urllib.parse import parse_qsl, urlencode

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from web.app import create_app  # noqa: E402

flask_app = create_app()


def app(environ, start_response):
    pairs = parse_qsl(environ.get("QUERY_STRING", ""), keep_blank_values=True)
    original = [v for k, v in pairs if k == "__path"]
    if original:
        path = original[0] or "/"
        environ["PATH_INFO"] = path if path.startswith("/") else "/" + path
        environ["QUERY_STRING"] = urlencode([(k, v) for k, v in pairs if k != "__path"])
    return flask_app(environ, start_response)
