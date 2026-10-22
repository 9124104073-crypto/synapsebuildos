import os
import re
import base64
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

class DiagramHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode('utf-8'))
        
        filename = data['filename']
        img_b64 = data['image'].split(',')[1]
        img_bytes = base64.b64decode(img_b64)
        
        target_path = os.path.join('report_assets', filename)
        with open(target_path, 'wb') as f:
            f.write(img_bytes)
        print(f"Saved clean diagram: {target_path} ({len(img_bytes)} bytes)")
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(b'{"status":"ok"}')
        
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

def run_server():
    server = HTTPServer(('127.0.0.1', 8089), DiagramHandler)
    print("Receiver listening on http://127.0.0.1:8089")
    server.serve_forever()

if __name__ == '__main__':
    run_server()
