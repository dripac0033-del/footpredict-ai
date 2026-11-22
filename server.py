#!/usr/bin/env python3
"""
FootPredict Server - High Performance Local Web Server & API
Serves interactive prediction dashboard and multi-league analysis endpoints.
"""

import os
import json
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
import engine

PORT = 5055
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "public")

class FootPredictHandler(BaseHTTPRequestHandler):
    def send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

    def do_HEAD(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # 1. API Endpoints
        if path == "/api/leagues":
            leagues_list = [{"slug": k, **v} for k, v in engine.LEAGUES.items()]
            self.send_json({"status": "success", "leagues": leagues_list})
            return

        elif path == "/api/matches":
            league = query.get("league", ["esp.1"])[0]
            date_val = query.get("date", [None])[0]
            try:
                matches = engine.get_matches_for_league(league, date_val)
                self.send_json({"status": "success", "league": league, "count": len(matches), "matches": matches})
            except Exception as e:
                self.send_json({"status": "error", "message": str(e)}, 500)
            return

        elif path == "/api/match-analysis":
            league = query.get("league", ["esp.1"])[0]
            event_id = query.get("eventId", [None])[0]
            if not event_id:
                self.send_json({"status": "error", "message": "Missing eventId"}, 400)
                return
            try:
                details = engine.get_match_full_details(league, event_id)
                if details:
                    self.send_json({"status": "success", "data": details})
                else:
                    self.send_json({"status": "error", "message": "Match details not found"}, 404)
            except Exception as e:
                self.send_json({"status": "error", "message": str(e)}, 500)
            return

        elif path == "/api/top-picks":
            date_val = query.get("date", [None])[0]
            all_matches = []
            # Scan top 5 leagues for highest confidence picks
            top_leagues = ["esp.1", "eng.1", "uefa.champions", "ita.1", "ger.1", "fra.1"]
            for l_slug in top_leagues:
                try:
                    m_list = engine.get_matches_for_league(l_slug, date_val)
                    all_matches.extend(m_list)
                except Exception:
                    pass

            # Sort by prediction confidence and corner expectancies
            safe_picks = sorted([m for m in all_matches if m.get("quick_prediction", {}).get("confidence", 0) >= 55],
                                key=lambda x: x["quick_prediction"]["confidence"], reverse=True)[:6]
            corner_picks = sorted(all_matches, key=lambda x: x.get("quick_prediction", {}).get("corners_exp", 0), reverse=True)[:6]

            self.send_json({
                "status": "success",
                "safe_picks": safe_picks,
                "corner_picks": corner_picks,
                "total_scanned": len(all_matches)
            })
            return

        elif path == "/api/search":
            q = query.get("q", [""])[0].lower().strip()
            date_val = query.get("date", [None])[0]
            if not q:
                self.send_json({"status": "success", "matches": []})
                return
            matched = []
            for l_slug in engine.LEAGUES.keys():
                try:
                    m_list = engine.get_matches_for_league(l_slug, date_val)
                    for m in m_list:
                        h_name = m["home"]["name"].lower()
                        a_name = m["away"]["name"].lower()
                        if q in h_name or q in a_name or q in m["name"].lower():
                            matched.append(m)
                except Exception:
                    pass
            self.send_json({"status": "success", "query": q, "matches": matched})
            return

        # 2. Static File Serving
        if path == "/" or path == "":
            path = "/index.html"
            
        rel_path = path.lstrip("/")
        file_path = os.path.join(STATIC_DIR, rel_path)
        
        # Security: prevent path traversal
        if not os.path.abspath(file_path).startswith(STATIC_DIR):
            self.send_error(403, "Forbidden")
            return

        if os.path.isfile(file_path):
            content_type = "text/plain"
            if file_path.endswith(".html"):
                content_type = "text/html; charset=utf-8"
            elif file_path.endswith(".css"):
                content_type = "text/css; charset=utf-8"
            elif file_path.endswith(".js"):
                content_type = "application/javascript; charset=utf-8"
            elif file_path.endswith(".json"):
                content_type = "application/json; charset=utf-8"
            elif file_path.endswith(".png"):
                content_type = "image/png"
            elif file_path.endswith(".svg"):
                content_type = "image/svg+xml"

            try:
                with open(file_path, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(content)))
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(content)
            except Exception as e:
                self.send_error(500, f"Error reading file: {e}")
        else:
            self.send_error(404, "File Not Found")

def run_server(port=PORT):
    os.makedirs(STATIC_DIR, exist_ok=True)
    server_address = ("0.0.0.0", port)
    httpd = HTTPServer(server_address, FootPredictHandler)
    print(f"=====================================================")
    print(f"🚀 FootPredict AI Server is running!")
    print(f"🔗 Local Dashboard:  http://localhost:{port}")
    print(f"🔗 Network Address:   http://127.0.0.1:{port}")
    print(f"=====================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        httpd.server_close()

if __name__ == "__main__":
    run_server()
