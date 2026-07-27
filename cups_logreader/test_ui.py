#!/usr/bin/env python3
import http.server, socketserver, subprocess, os, datetime, urllib.parse

MQTT_HOST = os.environ.get("MQTT_HOST", "")
MQTT_PORT = os.environ.get("MQTT_PORT", "1883")
MQTT_USER = os.environ.get("MQTT_USER", "")
MQTT_PASS = os.environ.get("MQTT_PASS", "")
QUEUES = os.environ.get("QUEUES", "").split(",")

PORT = 8099

FORM = """
<html>
<head>
<style>
  :root {{
    --bg: #f5f5f5;
    --card-bg: #ffffff;
    --text: #1a1a1a;
    --muted: #666666;
    --border: #dddddd;
    --accent: #0d6efd;
    --accent-text: #ffffff;
  }}
  html.dark {{
    --bg: #1a1a1a;
    --card-bg: #2a2a2a;
    --text: #e8e8e8;
    --muted: #a0a0a0;
    --border: #444444;
    --accent: #3b82f6;
    --accent-text: #ffffff;
  }}
  body {{
    font-family: sans-serif;
    max-width: 420px;
    margin: 40px auto;
    padding: 0 16px;
    background: var(--bg);
    color: var(--text);
    transition: background 0.15s, color 0.15s;
  }}
  .card {{
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 24px;
  }}
  h2 {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 1.2em;
    margin-top: 0;
  }}
  select, input {{
    width: 100%;
    box-sizing: border-box;
    padding: 8px;
    border-radius: 6px;
    border: 1px solid var(--border);
    background: var(--bg);
    color: var(--text);
    margin-top: 4px;
  }}
  button[type="submit"] {{
    background: var(--accent);
    color: var(--accent-text);
    border: none;
    padding: 10px 16px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 1em;
  }}
  .toggle-btn {{
    background: none;
    border: 1px solid var(--border);
    color: var(--text);
    border-radius: 6px;
    padding: 4px 10px;
    cursor: pointer;
    font-size: 0.85em;
  }}
  .meta {{
    color: var(--muted);
    font-size: 0.85em;
  }}
  code {{
    background: var(--bg);
    padding: 2px 5px;
    border-radius: 4px;
  }}
</style>
</head>
<body>
<div class="card">
<h2>Test Publish <button class="toggle-btn" onclick="toggleDark()">🌓 Toggle</button></h2>
<form method="POST">
<label>Queue:</label>
<select name="queue">{options}</select>
<label>Pages:</label>
<input type="number" name="pages" value="1" min="1" max="200">
<br><br>
<button type="submit">Send Test Print</button>
</form>
<p class="meta">IP: localhost &middot; User: TEST &middot; Time: now</p>
{message}
</div>
<script>
  function applyTheme(dark) {{
    document.documentElement.classList.toggle('dark', dark);
  }}
  function toggleDark() {{
    const isDark = !document.documentElement.classList.contains('dark');
    applyTheme(isDark);
    localStorage.setItem('cups_test_dark', isDark ? '1' : '0');
  }}
  (function() {{
    const stored = localStorage.getItem('cups_test_dark');
    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    applyTheme(stored === null ? prefersDark : stored === '1');
  }})();
</script>
</body></html>
"""

class Handler(http.server.BaseHTTPRequestHandler):
    def _options_html(self):
        return "".join(f'<option value="{q}">{q}</option>' for q in QUEUES if q)

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(FORM.format(options=self._options_html(), message="").encode())

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length).decode()
        params = urllib.parse.parse_qs(body)
        queue = params.get("queue", [QUEUES[0] if QUEUES else ""])[0]
        pages = params.get("pages", ["1"])[0]
        ts = datetime.datetime.now().strftime("%d/%b/%Y:%H:%M:%S %z")
        payload = f'{{"pages": {pages}, "last_printed": "{ts}", "last_user": "TEST", "last_ip": "localhost"}}'

        cmd = ["mosquitto_pub", "-h", MQTT_HOST, "-p", str(MQTT_PORT)]
        if MQTT_USER:
            cmd += ["-u", MQTT_USER]
        if MQTT_PASS:
            cmd += ["-P", MQTT_PASS]
        cmd += ["-t", f"cups/{queue}/status", "-m", payload]

        result = subprocess.run(cmd, capture_output=True, text=True)
        msg = f"<p>Published to <code>cups/{queue}/status</code>:<br>{payload}</p>"
        if result.returncode != 0:
            msg += f"<p style='color:red'>Error: {result.stderr}</p>"

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(FORM.format(options=self._options_html(), message=msg).encode())

with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
    httpd.serve_forever()
