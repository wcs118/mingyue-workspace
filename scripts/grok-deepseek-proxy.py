#!/usr/bin/env python3
"""Grok Build → DeepSeek 兼容代理
作用:grok 作为 agent 会发送 tool_choice=required/指定函数,DeepSeek thinking 模式不支持。
此代理在转发时注入 thinking:{"type":"disabled"},让工具调用完全可用。
用法:python3 grok-deepseek-proxy.py(监听 127.0.0.1:18800)
"""
import json
import urllib.request
import urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler

UPSTREAM = "https://api.deepseek.com"
PORT = 18800


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        try:
            req = json.loads(body)
        except Exception:
            req = None

        # 注入 thinking disabled(仅 chat/completions)
        if req and self.path.endswith("/chat/completions"):
            req.setdefault("thinking", {"type": "disabled"})
            body = json.dumps(req).encode()

        url = UPSTREAM + self.path
        headers = {k: v for k, v in self.headers.items() if k.lower() in (
            "authorization", "content-type", "user-agent", "accept")}
        r = urllib.request.Request(url, data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(r, timeout=300) as resp:
                data = resp.read()
                self.send_response(resp.status)
                for k, v in resp.headers.items():
                    if k.lower() in ("content-type",):
                        self.send_header(k, v)
                self.end_headers()
                self.wfile.write(data)
        except urllib.error.HTTPError as e:
            data = e.read()
            self.send_response(e.code)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(data)
        except Exception as e:
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": {"message": str(e)}}).encode())

    def do_GET(self):
        url = UPSTREAM + self.path
        r = urllib.request.Request(url, method="GET")
        try:
            with urllib.request.urlopen(r, timeout=60) as resp:
                data = resp.read()
                self.send_response(resp.status)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(data)
        except Exception as e:
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": {"message": str(e)}}).encode())

    def log_message(self, fmt, *args):
        pass


if __name__ == "__main__":
    print(f"Grok→DeepSeek 代理启动: http://127.0.0.1:{PORT} (注入 thinking disabled)")
    HTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
