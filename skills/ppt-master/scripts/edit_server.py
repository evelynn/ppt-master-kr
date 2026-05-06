#!/usr/bin/env python3
"""
PPT Master - local editor HTTP server.

Serves the static editor UI (skills/ppt-master/editor/) and a small JSON API
that wraps outline_manager + design_tokens + slide_regenerator.

Endpoints:
  GET    /                        → editor index.html
  GET    /editor/<asset>          → static asset
  GET    /api/outline             → outline.yaml as JSON
  PUT    /api/outline             → write outline.yaml from JSON body
  GET    /api/design-system       → DESIGN.md parsed (with theme_overrides applied)
  PATCH  /api/design-system       → merge color/typography overrides into outline.theme_overrides
  GET    /api/slides              → list slide ids + finalized status
  GET    /api/slides/<id>.svg     → svg_final/<id>.svg if present, else svg_output/<id>.svg
  GET    /api/components          → components_index.json + each component as inline svg
  POST   /api/regenerate          → body {mode: "slides"|"sections"|"theme"|"reorganize", ids?: [...]}
                                    runs slide_regenerator and returns combined log
  GET    /api/canvas-formats      → reference dimensions

Bind: 127.0.0.1 only. No auth — local single-user use.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

SCRIPTS = Path(__file__).parent
SKILL_ROOT = SCRIPTS.parent
EDITOR_DIR = SKILL_ROOT / "editor"

sys.path.insert(0, str(SCRIPTS))
import outline_manager  # type: ignore
from design_tokens import parse_design_md  # type: ignore


def _resolve_design_md(project_dir: Path) -> Path | None:
    local = project_dir / "design_system.md"
    if local.exists():
        return local
    pointer = project_dir / ".ppt-master" / "template.txt"
    if pointer.exists():
        slug = pointer.read_text(encoding="utf-8").strip()
        cand = SKILL_ROOT / "templates" / "layouts" / slug / "DESIGN.md"
        if cand.exists():
            return cand
    return None


def make_handler(project_dir: Path):
    class Handler(BaseHTTPRequestHandler):
        # ---- helpers ----
        def _send(self, status: int, body: bytes, ctype: str = "application/json") -> None:
            self.send_response(status)
            self.send_header("Content-Type", ctype + "; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, PUT, POST, PATCH, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()
            self.wfile.write(body)

        def _send_json(self, payload, status: int = 200) -> None:
            self._send(status, json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8"))

        def _send_text(self, body: str, ctype: str = "text/plain", status: int = 200) -> None:
            self._send(status, body.encode("utf-8"), ctype)

        def _read_json(self) -> dict | list | None:
            length = int(self.headers.get("Content-Length", "0"))
            if not length:
                return None
            raw = self.rfile.read(length)
            try:
                return json.loads(raw.decode("utf-8"))
            except Exception:
                return None

        def log_message(self, fmt, *args):  # silence default logger
            return

        # ---- dispatch ----
        def do_OPTIONS(self):
            self._send(204, b"")

        def do_GET(self):
            url = urlparse(self.path)
            path = url.path

            if path in ("/", "/index.html"):
                return self._serve_static(EDITOR_DIR / "index.html", "text/html")
            if path.startswith("/editor/"):
                rel = path[len("/editor/"):]
                target = (EDITOR_DIR / rel).resolve()
                if EDITOR_DIR.resolve() in target.parents and target.exists():
                    return self._serve_static(target)

            if path == "/api/outline":
                return self._send_json(outline_manager.load(project_dir))
            if path == "/api/design-system":
                return self._design_system_response()
            if path == "/api/slides":
                return self._send_json(self._slides_listing())
            if path.startswith("/api/slides/") and path.endswith(".svg"):
                slide_id = path[len("/api/slides/"):-len(".svg")]
                return self._serve_slide_svg(slide_id)
            if path == "/api/components":
                return self._send_json(self._components_payload())
            if path == "/api/canvas-formats":
                return self._send_json({
                    "ppt169": {"viewBox": "0 0 1280 720", "label": "PPT 16:9"},
                    "ppt43":  {"viewBox": "0 0 1024 768", "label": "PPT 4:3"},
                })
            return self._send_json({"error": "not found", "path": path}, status=404)

        def do_PUT(self):
            url = urlparse(self.path)
            if url.path == "/api/outline":
                body = self._read_json()
                if not isinstance(body, dict):
                    return self._send_json({"error": "expected JSON object"}, status=400)
                outline_manager.save(project_dir, body)
                return self._send_json({"ok": True})
            return self._send_json({"error": "not found"}, status=404)

        def do_PATCH(self):
            url = urlparse(self.path)
            if url.path == "/api/design-system":
                body = self._read_json()
                if not isinstance(body, dict):
                    return self._send_json({"error": "expected JSON object"}, status=400)
                outline = outline_manager.load(project_dir) or {"meta": {}, "slides": [], "sections": []}
                merged = outline.get("theme_overrides") or {}
                for ns in ("colors", "typography"):
                    if ns in body and isinstance(body[ns], dict):
                        merged.setdefault(ns, {}).update(body[ns])
                outline["theme_overrides"] = merged
                outline_manager.save(project_dir, outline)
                return self._send_json({"ok": True, "theme_overrides": merged})
            return self._send_json({"error": "not found"}, status=404)

        def do_POST(self):
            url = urlparse(self.path)
            if url.path == "/api/regenerate":
                body = self._read_json() or {}
                return self._handle_regenerate(body)
            return self._send_json({"error": "not found"}, status=404)

        # ---- handlers ----
        def _serve_static(self, target: Path, ctype: str | None = None):
            if not target.exists():
                return self._send_json({"error": "asset missing", "path": str(target)}, status=404)
            ext = target.suffix.lower()
            ctype = ctype or {
                ".html": "text/html",
                ".js": "application/javascript",
                ".css": "text/css",
                ".svg": "image/svg+xml",
                ".json": "application/json",
                ".png": "image/png",
            }.get(ext, "application/octet-stream")
            data = target.read_bytes()
            return self._send(200, data, ctype)

        def _design_system_response(self):
            ds_path = _resolve_design_md(project_dir)
            if not ds_path:
                return self._send_json({"error": "DESIGN.md not found"}, status=404)
            ds = parse_design_md(ds_path)
            outline = outline_manager.load(project_dir)
            overrides = (outline or {}).get("theme_overrides") or {}
            colors = dict(ds.colors)
            for k, v in (overrides.get("colors") or {}).items():
                colors[k] = v
            payload = ds.to_json()
            payload["colors"] = colors
            payload["theme_overrides"] = overrides
            return self._send_json(payload)

        def _slides_listing(self):
            outline = outline_manager.load(project_dir)
            svg_output = project_dir / "svg_output"
            svg_final = project_dir / "svg_final"
            slides = outline.get("slides", []) if outline else []
            for slide in slides:
                sid = slide["id"]
                slide["has_output"] = bool(list(svg_output.glob(f"{sid}*.svg")))
                slide["has_final"] = bool(list(svg_final.glob(f"{sid}*.svg")))
            return {"slides": slides, "sections": outline.get("sections", []) if outline else []}

        def _serve_slide_svg(self, slide_id: str):
            for sub in ("svg_final", "svg_output"):
                d = project_dir / sub
                for f in d.glob(f"{slide_id}*.svg"):
                    return self._send(200, f.read_bytes(), "image/svg+xml")
            return self._send_json({"error": "slide not found", "id": slide_id}, status=404)

        def _components_payload(self):
            comp_dir = SKILL_ROOT / "templates" / "components"
            index_path = comp_dir / "components_index.json"
            if not index_path.exists():
                return {"components": {}}
            index = json.loads(index_path.read_text(encoding="utf-8"))
            for name, meta in index.get("components", {}).items():
                file_path = comp_dir / f"{name}.svg"
                if file_path.exists():
                    meta["svg"] = file_path.read_text(encoding="utf-8")
            return index

        def _handle_regenerate(self, body: dict):
            mode = body.get("mode")
            ids = body.get("ids") or []
            cmd = ["python3", str(SCRIPTS / "slide_regenerator.py"), str(project_dir)]
            if mode == "slides":
                if not ids:
                    return self._send_json({"error": "ids required for slides mode"}, status=400)
                cmd += ["--slides", ",".join(ids)]
            elif mode == "sections":
                if not ids:
                    return self._send_json({"error": "ids required for sections mode"}, status=400)
                cmd += ["--sections", ",".join(ids)]
            elif mode == "theme":
                cmd += ["--theme"]
            elif mode == "reorganize":
                cmd += ["--reorganize"]
            else:
                return self._send_json({"error": f"unknown mode {mode!r}"}, status=400)
            import subprocess
            proc = subprocess.run(cmd, capture_output=True, text=True)
            return self._send_json({
                "ok": proc.returncode == 0,
                "returncode": proc.returncode,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
                "command": cmd,
            })

    return Handler


def main() -> int:
    p = argparse.ArgumentParser(description="PPT Master local editor server")
    p.add_argument("project", type=Path)
    p.add_argument("--port", type=int, default=5051)
    p.add_argument("--no-browser", action="store_true")
    args = p.parse_args()

    project_dir = args.project.resolve()
    if not project_dir.exists():
        print(f"✖ Project not found: {project_dir}")
        return 1

    handler = make_handler(project_dir)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler)
    url = f"http://127.0.0.1:{args.port}/"
    print(f"PPT Master editor → {url}")
    print(f"  Project: {project_dir}")
    print(f"  Editor:  {EDITOR_DIR}")
    if not args.no_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nshutting down")
    return 0


if __name__ == "__main__":
    sys.exit(main())
