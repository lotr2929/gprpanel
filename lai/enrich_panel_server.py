#!/usr/bin/env python
"""
enrich_panel_server.py
Local HTTP server for the GPR Enrichment Monitor panel.
Run: python enrich_panel_server.py
Then open: http://localhost:7749
"""
import os, json, glob, time, threading, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _credentials import SUPABASE_URL, SUPABASE_KEY, HEADERS as _HEADERS
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse, requests as req

BASE    = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE, "logs")
SB_URL  = SUPABASE_URL + "/rest/v1/gpr_plant_species"
SB_KEY  = SUPABASE_KEY
SB_HDR  = {"apikey": SB_KEY, "Authorization": "Bearer " + SB_KEY, "Prefer": "count=exact"}
PORT    = 7749

_db_cache = {}
_db_ts    = 0
_db_lock  = threading.Lock()

def get_db_coverage():
    global _db_cache, _db_ts
    now = time.time()
    with _db_lock:
        if now - _db_ts < 30:
            return _db_cache
    fields = [
        ("total",           {}),
        ("usda_zone",       {"usda_zone": "not.is.null"}),
        ("height_mature_m", {"height_mature_m": "not.is.null"}),
        ("growth_form",     {"growth_form": "not.is.null"}),
        ("leaf_phenology",  {"leaf_phenology": "not.is.null"}),
        ("sla",             {"sla": "not.is.null"}),
        ("fire_tolerance",  {"fire_tolerance": "not.is.null"}),
        ("image_url",       {"image_url": "not.is.null"}),
        ("carbon_seq_kg_yr",{"carbon_seq_kg_yr": "not.is.null"}),
        ("shade_factor",    {"shade_factor": "not.is.null"}),
        ("enrichment_sources",{"enrichment_sources": "not.is.null"}),
    ]
    result = {}
    for label, params in fields:
        try:
            p = dict(params)
            p["select"] = "id"
            p["limit"]  = "1"
            r = req.get(SB_URL, headers=SB_HDR, params=p, timeout=10)
            result[label] = int(r.headers.get("content-range","0/0").split("/")[-1])
        except:
            result[label] = -1
    with _db_lock:
        _db_cache = result
        _db_ts    = time.time()
    return result

def latest_log():
    logs = sorted(glob.glob(os.path.join(LOG_DIR, "enrich_*.log")), key=os.path.getmtime)
    if not logs: return None, ""
    path = logs[-1]
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return path, f.read()
    except:
        return path, ""

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        p = urllib.parse.urlparse(self.path)
        if p.path == "/log":
            path, content = latest_log()
            data = json.dumps({"path": path or "", "content": content}).encode()
            self.send_response(200)
            self.send_header("Content-Type","application/json")
            self.send_header("Access-Control-Allow-Origin","*")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers(); self.wfile.write(data)
        elif p.path == "/db":
            cov = get_db_coverage()
            data = json.dumps(cov).encode()
            self.send_response(200)
            self.send_header("Content-Type","application/json")
            self.send_header("Access-Control-Allow-Origin","*")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers(); self.wfile.write(data)
        elif p.path == "/" or p.path == "/panel":
            html_path = os.path.join(BASE, "enrich_panel.html")
            try:
                with open(html_path, encoding="utf-8") as f:
                    html = f.read().encode()
                self.send_response(200)
                self.send_header("Content-Type","text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(html)))
                self.end_headers(); self.wfile.write(html)
            except:
                self.send_response(404); self.end_headers()
        else:
            self.send_response(404); self.end_headers()

if __name__ == "__main__":
    print(f"GPR Enrichment Monitor  ->  http://localhost:{PORT}")
    print(f"Log dir: {LOG_DIR}")
    print("Ctrl-C to stop.")
    HTTPServer(("localhost", PORT), Handler).serve_forever()
