#!/usr/bin/env python3
"""
Hermes Memory Health Dashboard - Local Server
=============================================

A simple, clean local HTTP server for the Memory Health Dashboard.
This avoids file:// CORS issues and makes the live dashboard experience much better.

Usage:
    python memory_dashboard/run_dashboard_server.py

Then open: http://localhost:8765/memory_health_dashboard.html

You can also run the scheduled exporter in another terminal for live updates.
"""

import http.server
import socketserver
import os
from pathlib import Path

PORT = 8765
DIRECTORY = Path(__file__).parent  # Serve from the memory_dashboard folder

class DashboardHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIRECTORY), **kwargs)

    def end_headers(self):
        # Add headers to help with caching during development
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

    def log_message(self, format, *args):
        # Cleaner logging
        print(f"[Dashboard Server] {args[0]} {args[1]} {args[2]}")


if __name__ == "__main__":
    os.chdir(DIRECTORY)
    
    with socketserver.TCPServer(("", PORT), DashboardHTTPRequestHandler) as httpd:
        print(f"\n🚀 Hermes Memory Health Dashboard Server running!")
        print(f"   Open in your browser: http://localhost:{PORT}/memory_health_dashboard.html\n")
        print("   Press Ctrl+C to stop the server.\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")