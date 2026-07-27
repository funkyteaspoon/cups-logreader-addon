#!/usr/bin/env python3
import http.server, socketserver, subprocess, os, datetime, urllib.parse

MQTT_HOST = os.environ.get("MQTT_HOST", "")
MQTT_PORT = os.environ.get("MQTT_PORT", "1883")
MQTT_USER = os.environ.get("MQTT_USER", "")
MQTT_PASS = os.environ.get("MQTT_PASS", "")
QUEUES = os.environ.get("QUEUES", "").split(",")

PORT = 8099

FORM = """
<html><body style="font-family:sans-serif;max-width:420px;margin:40px auto;">
<h2>CUPS Log Reader — Test Publish</h2>
<form method="POST">
<label>Queue:</label><br>
<select name="queue">{options}</select><br><br>
<label>Pages:</label><br>
<input type="number" name="pages" value="1" min="1" max="200"><br><br>
<button type="submit">Send Test Print</button>
</form>
<p style="color:#666;font-size:0.9em">IP: localhost &middot; User: TEST &middot; Time: now</p>
{message}
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
