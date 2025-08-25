99Proxys – Windows‑Centric Modular Refactor

A clean, Windows‑first split of your monolith into modules. It keeps your original features (SOCKS5 chain, locales, optional Tor hidden services, Flask WYSIWYG/Chat/Reviews, Tk GUI) but:

Uses Windows admin detection (ctypes.windll.shell32.IsUserAnAdmin).

Uses netsh for virtual IP assignment (no ip addr).

Defaults TOR_PATH to tor.exe and allows env override.

Avoids Linux‑only calls (os.geteuid, setcap, etc.).

Listener TLS is optional; hop‑to‑hop crypto is RSA+Fernet with a framed session key.


> Quick start (Windows, PowerShell)

`python -m venv .venv; .\.venv\Scripts\Activate.ps1`
`pip install -r requirements.txt`
``# Run elevated if you set ASSIGN_VIRTUAL_IP=true``
`python main.py`

To enable OS virtual IPs: run terminal as Administrator and set `ASSIGN_VIRTUAL_IP=true` (in .env or config).




---

Project layout

99proxys-win/
├─ main.py
├─ requirements.txt
├─ README.md
├─ .env                         # optional: overrides for config
├─ 99proxys/
│  ├─ __init__.py
│  ├─ config.py                 # Windows-centric defaults
│  ├─ logging_setup.py
│  ├─ locales.py
│  ├─ crypto.py                 # RSA+Fernet framing
│  ├─ ip_assign.py              # Windows admin + netsh
│  ├─ socks.py                  # SOCKS5 handler helpers
│  ├─ node.py                   # ProxyNode
│  ├─ chain.py                  # ProxyChain orchestration
│  ├─ tor.py                    # Hidden service (tor.exe)
│  ├─ utils.py
│  ├─ gui.py                    # Tkinter GUI (Windows)
│  └─ webapp/
│     ├─ __init__.py           # create_flask_app()
│     ├─ models.py             # SQLAlchemy models
│     ├─ routes.py             # editor/chat/reviews/status
│     └─ templates/            # html templates
│        ├─ chat.html
│        ├─ reviews.html
│        └─ editor.html
└─ assets/, certs/, config/, data/, hidden_services/, logs/, sites/, tor_data/, uploads/, docs/

> The assets/certs … folders are created at runtime if missing.




---

```requirements.txt

cryptography==42.0.5
Flask==2.3.3
Flask-SocketIO==5.3.6
Flask-SQLAlchemy==3.0.5
Flask-WTF==1.2.1
Werkzeug==3.0.1
WTForms==3.1.2
psutil==5.9.8
requests==2.31.0
rich==13.7.1
matplotlib==3.8.3
TimezoneFinder==6.1.9
pytz==2023.3
python-dotenv==1.0.1
```
---

```main.py

from 99proxys.logging_setup import init_logging
from 99proxys.config import CONFIG, ensure_dirs, load_env_overrides, generate_self_signed_cert
from 99proxys.webapp import create_flask_app
from 99proxys.chain import ProxyChain
from rich.console import Console
from rich.panel import Panel
import threading, os, time

console = Console()

ASCII_ART = r"""
┏━━━┓┏━━━┓━━━━┏━━━┓━━━━━━━━━━━━━━━━━━━━━
┃┏━┓┃┃┏━┓┃━━━━┃┏━┓┃━━━━━━━━━━━━━━━━━━━━━
┃┗━┛┃┃┗━┛┃━━━━┃┗━┛┃┏━┓┏━━┓┏┓┏┓┏┓━┏┓┏━━┓━
┗━━┓┃┗━━┓┃━━━━┃┏━━┛┃┏┛┃┏┓┃┗╋╋┛┃┃━┃┃┃━━┫━
┏━━┛┃┏━━┛┃━━━━┃┃━━━┃┃━┃┗┛┃┏╋╋┓┃┗━┛┃┣━━┃━
┗━━━┛┗━━━┛━━━━┗┛━━━┗┛━┗━━┛┗┛┗┛┗━┓┏┛┗━━┛━
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┏━┛┃━━━━━━
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┗━━┛━━BGGG━
             ~99Proxys v5.0.0~
      - Private Local VPN Network -
        - BG Gremlin Group ©2025 -
"""

def main():
    init_logging()
    load_env_overrides()
    ensure_dirs()
    generate_self_signed_cert()

    console.print(Panel(ASCII_ART, title="99Proxys Launch", style="cyan"))
    console.print("[cyan]Starting 99Proxys (Windows-centric)…[/cyan]")

    app = create_flask_app()

    chain = ProxyChain(app)

    # start Flask-SocketIO server on background thread
    from 99proxys.webapp import socketio
    threading.Thread(
        target=lambda: socketio.run(app, host="127.0.0.1", port=CONFIG["WEB_PORT"], debug=False, use_reloader=False, allow_unsafe_werkzeug=True),
        daemon=True
    ).start()

    console.print(f"[green]Flask server: http://127.0.0.1:{CONFIG['WEB_PORT']}[/green]")

    # Optional: start GUI (skip if headless or disabled)
    if CONFIG.get("ENABLE_GUI", True) and os.environ.get("WT_HEADLESS") != "1":
        from 99proxys.gui import ProxyGUI
        ProxyGUI(chain)
    else:
        console.print("[yellow]GUI disabled or headless detected. Running services only.[/yellow]")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            chain.stop()

if __name__ == "__main__":
    main()


---

99proxys/__init__.py

__all__ = []
```
---

```99proxys/config.py

import os
from pathlib import Path
from dotenv import load_dotenv
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from datetime import datetime, timedelta

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"
LOG_DIR = BASE_DIR / "logs"
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"
CERT_DIR = BASE_DIR / "certs"
TOR_DIR = BASE_DIR / "tor_data"
HIDDEN_SERVICE_DIR = BASE_DIR / "hidden_services"
UPLOAD_DIR = BASE_DIR / "uploads"
SITES_DIR = BASE_DIR / "sites"
DOCS_DIR = BASE_DIR / "docs"

CERT_FILE = CERT_DIR / "server.crt"
KEY_FILE  = CERT_DIR / "server.key"

CONFIG = {
    "WEB_PORT": 5000,
    "MIN_PORT": 1024,
    "MAX_PORT": 65535,
    "NODE_COUNT": 5,
    "RATE_LIMIT": 100,
    "MIN_SPEED_KBPS": 56,
    "MAX_BANDWIDTH_KBPS": 1000,
    "HEALTH_CHECK_INTERVAL": 30,
    "LISTENER_TLS": False,              # SOCKS listener TLS off by default
    "ASSIGN_VIRTUAL_IP": False,        # netsh IP add only if True
    "DEFAULT_IFACE": os.environ.get("PROXY_IFACE", "Ethernet"),
    "TOR_PATH": os.environ.get("TOR_PATH", "tor.exe"),
    "ENABLE_GUI": True,
}

DIRS = [CONFIG_DIR, LOG_DIR, DATA_DIR, ASSETS_DIR, CERT_DIR, TOR_DIR, HIDDEN_SERVICE_DIR, UPLOAD_DIR, SITES_DIR, DOCS_DIR]

def ensure_dirs():
    for d in DIRS:
        d.mkdir(parents=True, exist_ok=True)


def load_env_overrides():
    load_dotenv()
    for k in list(CONFIG.keys()):
        v = os.environ.get(k)
        if v is None:
            continue
        if v.lower() in {"true","false"}:
            CONFIG[k] = (v.lower() == "true")
        elif v.isdigit():
            CONFIG[k] = int(v)
        else:
            CONFIG[k] = v


def generate_self_signed_cert():
    if CERT_FILE.exists() and KEY_FILE.exists():
        return
    KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, "99Proxys Local VPN"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "BG Gremlin Group"),
        x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
    ])
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.utcnow())
        .not_valid_after(datetime.utcnow() + timedelta(days=365))
        .add_extension(x509.SubjectAlternativeName([x509.DNSName("localhost")]), critical=False)
        .sign(private_key, hashes.SHA256())
    )
    with open(CERT_FILE, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
    with open(KEY_FILE, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ))
```

---

```99proxys/logging_setup.py

import logging
from .config import LOG_DIR
from datetime import datetime

def init_logging():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logfile = LOG_DIR / f"99proxys_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logging.basicConfig(
        filename=str(logfile),
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        filemode="a",
    )
```

---

```99proxys/locales.py

# Truncated for brevity – include your full 99 LOCALES here
LOCALES = [
    {"country": "United States", "timezone": "America/New_York", "lat": 40.7128, "lon": -74.0060, "ip_prefix": "192.168.1.0/24"},
    {"country": "Canada", "timezone": "America/Toronto", "lat": 43.6532, "lon": -79.3832, "ip_prefix": "192.168.2.0/24"},
    # ... include all entries from your original LOCALES list ...
]

IOT_OUIS = [
    "00:0D:3F", "00:16:6C", "00:24:E4", "00:1E:C0", "00:26:66",
    "00:1A:22", "00:17:88", "00:21:CC", "00:24:81", "00:1D:0F"
]
```

---

```99proxys/crypto.py

import os, base64, logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes

FRAME_MAGIC = b"EK"

class HopCrypto:
    def __init__(self, fernet: Fernet, rsa_private_key, rsa_public_key):
        self.fernet = fernet
        self.rsa_private_key = rsa_private_key
        self.rsa_public_key = rsa_public_key

    def encrypt_for_next(self, data: bytes, next_pubkey=None) -> bytes:
        try:
            if next_pubkey is None:
                return self.fernet.encrypt(data)
            session_key = os.urandom(32)
            enc_key = next_pubkey.encrypt(
                session_key,
                padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
            )
            f = Fernet(base64.urlsafe_b64encode(session_key))
            payload = f.encrypt(data)
            return FRAME_MAGIC + len(enc_key).to_bytes(2, "big") + enc_key + payload
        except Exception as e:
            logging.error(f"encrypt_for_next error: {e}")
            return data

    def decrypt_from_prev(self, data: bytes) -> bytes:
        try:
            if data.startswith(FRAME_MAGIC) and len(data) > 4:
                klen = int.from_bytes(data[2:4], "big")
                if len(data) < 4 + klen:
                    return data
                enc_key = data[4:4+klen]
                payload = data[4+klen:]
                session_key = self.rsa_private_key.decrypt(
                    enc_key,
                    padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
                )
                f = Fernet(base64.urlsafe_b64encode(session_key))
                return f.decrypt(payload)
            return self.fernet.decrypt(data)
        except Exception as e:
            logging.error(f"decrypt_from_prev error: {e}")
            return data
```

---

```99proxys/ip_assign.py (Windows only)

import subprocess, logging
from .config import CONFIG

class AdminRequired(Exception):
    pass

def is_admin() -> bool:
    try:
        import ctypes
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def assign_virtual_ip(interface: str, ip: str, mask: str = "255.255.255.0"):
    if not CONFIG.get("ASSIGN_VIRTUAL_IP", False):
        logging.info(f"Skipping OS IP assignment for {ip}")
        return
    if not is_admin():
        raise AdminRequired("Run PowerShell/Terminal as Administrator to assign virtual IPs.")
    # netsh interface ip add address "Ethernet" 192.168.x.y 255.255.255.0
    subprocess.run(["netsh", "interface", "ip", "add", "address", interface, ip, mask], check=True)
```

---

```99proxys/socks.py

import socket

# Minimal helpers for SOCKS5 parsing
SOCKS_VERSION = 5

ATYP_IPV4 = 1
ATYP_DOMAIN = 3
ATYP_IPV6 = 4

REP_SUCCEEDED = 0x00
REP_GENERAL_FAIL = 0x01
REP_HOST_UNREACH = 0x04
REP_ADDR_NOT_SUP = 0x08


def recv_exact(sock, n):
    data = b""
    while len(data) < n:
        chunk = sock.recv(n - len(data))
        if not chunk:
            return None
        data += chunk
    return data


def parse_dest(request_sock):
    # after version/methods and the 4-byte header with CMD/RSV/ATYP has been read
    # this parses ATYP specific fields
    # returns (ip_bytes, ip_str, port) or raises
    atyp = None
    header = recv_exact(request_sock, 4)
    if not header:
        raise ValueError("short header")
    cmd, rsv, atyp = header[1], header[2], header[3]

    if atyp == ATYP_IPV4:
        addr = recv_exact(request_sock, 4)
        port = int.from_bytes(recv_exact(request_sock, 2), 'big')
        ip = socket.inet_ntoa(addr)
        return addr, ip, port, cmd, atyp
    elif atyp == ATYP_DOMAIN:
        ln = recv_exact(request_sock, 1)
        if not ln:
            raise ValueError("short domain len")
        dlen = ln[0]
        domain = recv_exact(request_sock, dlen)
        port = int.from_bytes(recv_exact(request_sock, 2), 'big')
        host = domain.decode('utf-8', 'ignore')
        try:
            ip = socket.gethostbyname(host)
            addr = socket.inet_aton(ip)
            return addr, ip, port, cmd, atyp
        except Exception:
            raise OSError("resolve fail")
    else:
        raise NotImplementedError("ATYP not supported")
```

---

```99proxys/node.py

import os, socket, socketserver, ssl, threading, time, logging, random, ipaddress
from datetime import datetime
from pathlib import Path
import pytz
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.asymmetric import rsa
from .config import CONFIG, CERT_FILE, KEY_FILE
from .crypto import HopCrypto
from .ip_assign import assign_virtual_ip
from .socks import SOCKS_VERSION, REP_SUCCEEDED, REP_GENERAL_FAIL, REP_HOST_UNREACH, REP_ADDR_NOT_SUP, parse_dest

class ProxyNode:
    def __init__(self, host: str, port: int, locale: dict, virtual_ip: str, virtual_mac: str, health_check_interval: int = 30):
        self.host = host
        self.port = port
        self.locale = locale
        self.virtual_ip = virtual_ip
        self.virtual_mac = virtual_mac
        self.server = None
        self.active = False
        self.stats = {"requests":0, "bytes_sent":0, "bytes_received":0, "latency":0.0, "errors":0, "connection_time":0.0, "bandwidth_kbps":0.0}
        # keys
        key_file = Path(CERT_FILE.parent) / f"fernet_{port}.key"
        if key_file.exists():
            self.fernet = Fernet(key_file.read_bytes())
        else:
            k = Fernet.generate_key(); key_file.write_bytes(k); self.fernet = Fernet(k)
        self.rsa_private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.rsa_public_key = self.rsa_private_key.public_key()
        self.crypto = HopCrypto(self.fernet, self.rsa_private_key, self.rsa_public_key)

        self.rate_limit = CONFIG["RATE_LIMIT"]
        self.request_timestamps = []
        self.bandwidth_limit_kbps = CONFIG["MAX_BANDWIDTH_KBPS"]
        self.bucket_tokens = self.bandwidth_limit_kbps * 1000 / 8
        self.bucket_capacity = self.bucket_tokens
        self.last_refill = time.time()
        self.lock = threading.Lock()
        self.health_check_thread = None
        self.running = threading.Event(); self.running.set()
        self.timezone = pytz.timezone(locale["timezone"])
        self.health_check_interval = health_check_interval

        # Optional OS IP assignment (Windows netsh)
        try:
            if CONFIG.get("ASSIGN_VIRTUAL_IP", False):
                assign_virtual_ip(CONFIG.get("DEFAULT_IFACE", "Ethernet"), self.virtual_ip)
        except Exception as e:
            logging.warning(f"Virtual IP assignment failed on {self.port}: {e}")

    def get_local_time(self) -> str:
        return datetime.now(self.timezone).strftime("%Y-%m-%d %H:%M:%S")

    def check_rate_limit(self) -> bool:
        with self.lock:
            now = time.time()
            self.request_timestamps = [t for t in self.request_timestamps if now - t < 60]
            self.request_timestamps.append(now)
            return len(self.request_timestamps) <= self.rate_limit

    def refill_bucket(self):
        now = time.time(); elapsed = now - self.last_refill
        self.bucket_tokens = min(self.bucket_capacity, self.bucket_tokens + elapsed * (self.bandwidth_limit_kbps * 1000 / 8))
        self.last_refill = now

    def throttle(self, size: int):
        with self.lock:
            self.refill_bucket()
            if size > self.bucket_tokens:
                time.sleep((size - self.bucket_tokens) / (self.bandwidth_limit_kbps * 1000 / 8))
                self.bucket_tokens = 0
            else:
                self.bucket_tokens -= size

    def health_check(self):
        while self.running.is_set():
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.settimeout(2)
                if CONFIG.get("LISTENER_TLS", False):
                    ctx = ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode = ssl.CERT_NONE
                    s = ctx.wrap_socket(s, server_hostname=self.host)
                s.connect((self.host, self.port))
                s.sendall(b"\x05\x01\x00")
                self.active = (s.recv(2) == b"\x05\x00")
            except Exception as e:
                self.active = False; logging.warning(f"Health check {self.port} failed: {e}")
            finally:
                try: s.close()
                except: pass
            time.sleep(self.health_check_interval)

    def start(self, next_node: 'ProxyNode' = None):
        node = self
        class Handler(socketserver.BaseRequestHandler):
            def handle(self):
                start = time.time()
                with node.lock:
                    node.stats["requests"] += 1
                # greeting
                data = self.request.recv(2)
                if data != b"\x05\x01\x00":
                    try: self.request.sendall(b"\x05\xff")
                    except: pass
                    return
                self.request.sendall(b"\x05\x00")
                # parse dest
                try:
                    addr_bytes, ip, port, cmd, atyp = parse_dest(self.request)
                except NotImplementedError:
                    self.request.sendall(b"\x05" + bytes([REP_ADDR_NOT_SUP]) + b"\x00\x01" + b"\x00"*6)
                    return
                except OSError:
                    self.request.sendall(b"\x05" + bytes([REP_HOST_UNREACH]) + b"\x00\x01" + b"\x00"*6)
                    return
                except Exception:
                    self.request.sendall(b"\x05" + bytes([REP_GENERAL_FAIL]) + b"\x00\x01" + b"\x00"*6)
                    return

                if cmd != 1:  # only CONNECT
                    self.request.sendall(b"\x05\x07\x00\x01" + b"\x00"*6)
                    return

                # connect out: if next_node provided, hop there; else raw to target
                try:
                    if next_node:
                        # hop to next node with TLS client if listener uses TLS
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        if CONFIG.get("LISTENER_TLS", False):
                            ctx = ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
                            sock = ctx.wrap_socket(sock, server_hostname=next_node.host)
                        sock.connect((next_node.host, next_node.port))
                        connect_req = b"\x05\x01\x00\x01" + addr_bytes + port.to_bytes(2,'big')
                        enc = node.crypto.encrypt_for_next(connect_req, next_node.rsa_public_key)
                        node.throttle(len(enc)); sock.sendall(enc)
                        reply = sock.recv(10)
                        dec = node.crypto.decrypt_from_prev(reply)
                        if dec.startswith(b"\x05\x00"):
                            self.request.sendall(b"\x05\x00\x00\x01" + addr_bytes + port.to_bytes(2,'big'))
                            self.tunnel(self.request, sock, next_node)
                        else:
                            self.request.sendall(b"\x05\x01\x00\x01" + b"\x00"*6)
                    else:
                        out = socket.create_connection((ip, port), timeout=5)
                        self.request.sendall(b"\x05\x00\x00\x01" + addr_bytes + port.to_bytes(2,'big'))
                        self.tunnel(self.request, out, None)
                except Exception as e:
                    logging.error(f"connect/tunnel error on {node.port}: {e}")
                    try: self.request.sendall(b"\x05\x01\x00\x01" + b"\x00"*6)
                    except: pass
                finally:
                    with node.lock:
                        node.stats["latency"] = time.time() - start

            def tunnel(self, client, target, next_node_obj):
                try:
                    while True:
                        data = client.recv(8192)
                        if not data: break
                        enc = node.crypto.encrypt_for_next(data, next_node_obj.rsa_public_key if next_node_obj else None)
                        node.throttle(len(enc)); target.sendall(enc)
                        resp = target.recv(8192)
                        if not resp: break
                        dec = node.crypto.decrypt_from_prev(resp)
                        client.sendall(dec)
                finally:
                    try: client.close()
                    except: pass
                    try: target.close()
                    except: pass

        self.server = socketserver.ThreadingTCPServer((self.host, self.port), Handler)
        self.server.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if CONFIG.get("LISTENER_TLS", False):
            ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            ctx.load_cert_chain(certfile=str(CERT_FILE), keyfile=str(KEY_FILE))
            self.server.socket = ctx.wrap_socket(self.server.socket, server_side=True)
        self.server.node = self
        self.active = True
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.health_check_thread = threading.Thread(target=self.health_check, daemon=True); self.health_check_thread.start()
        logging.info(f"Node started {self.host}:{self.port} ({self.locale['country']}, {self.virtual_mac})")

    def stop(self):
        self.running.clear()
        if self.server:
            try:
                self.server.shutdown(); self.server.server_close()
            except Exception as e:
                logging.error(f"stop server error {self.port}: {e}")
        self.active = False
```

---

```99proxys/chain.py

import os, random, ipaddress, socket, time, logging
from .config import CONFIG, SITES_DIR
from .locales import LOCALES, IOT_OUIS
from .node import ProxyNode
from .tor import create_hidden_service, stop_hidden_service
from .webapp.models import db, Website, Page
from flask import current_app
from werkzeug.utils import secure_filename

class ProxyChain:
    def __init__(self, flask_app):
        self.nodes = []
        self.websites = []
        self.used_ips = set()
        self.used_ports = set()
        self.flask_app = flask_app

    def _available_port(self):
        for _ in range(200):
            p = random.randint(CONFIG["MIN_PORT"], CONFIG["MAX_PORT"])
            if p in self.used_ports: continue
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind(("127.0.0.1", p)); self.used_ports.add(p); return p
                except OSError:
                    continue
        raise RuntimeError("No available ports found")

    def _v_ip(self, locale):
        nw = ipaddress.IPv4Network(locale["ip_prefix"], strict=False)
        for ip in nw.hosts():
            s = str(ip)
            if s not in self.used_ips:
                self.used_ips.add(s); return s
        raise RuntimeError("No IPs left in prefix")

    def _v_mac(self):
        import random
        oui = random.choice(IOT_OUIS)
        vb = ''.join(random.choices('0123456789ABCDEF', k=6))
        return f"{oui}:{vb[0:2]}:{vb[2:4]}:{vb[4:6]}".lower()

    def initialize_nodes(self):
        count = CONFIG["NODE_COUNT"]
        for i in range(count):
            loc = random.choice(LOCALES)
            port = self._available_port()
            vip = self._v_ip(loc)
            vmac = self._v_mac()
            node = ProxyNode("127.0.0.1", port, loc, vip, vmac, CONFIG["HEALTH_CHECK_INTERVAL"])
            self.nodes.append(node)
        for i in range(len(self.nodes) - 1):
            self.nodes[i].start(next_node=self.nodes[i+1])
        self.nodes[-1].start()
        logging.info(f"Initialized {len(self.nodes)} nodes")

    def create_website(self, name: str, pages: list):
        name = secure_filename(name)
        site_dir = SITES_DIR / name; site_dir.mkdir(parents=True, exist_ok=True)
        port = self._available_port()
        onion = create_hidden_service(name, port)
        with self.flask_app.app_context():
            w = Website(name=name, onion_address=onion, port=port, timestamp=time.strftime("%Y-%m-%d %H:%M:%S"))
            db.session.add(w); db.session.commit()
            for page in pages:
                p_name = secure_filename(page["name"]) or "index"
                p_dir = site_dir / p_name; p_dir.mkdir(parents=True, exist_ok=True)
                (p_dir/"index.html").write_text(page["html_content"], encoding="utf-8")
                if page.get("css_content"): (p_dir/"styles.css").write_text(page["css_content"], encoding="utf-8")
                if page.get("js_content"): (p_dir/"script.js").write_text(page["js_content"], encoding="utf-8")
                ent = Page(website_id=w.id, name=p_name, html_content=page.get("html_content",""), css_content=page.get("css_content",""), js_content=page.get("js_content",""), path=str(p_dir.relative_to(SITES_DIR)))
                db.session.add(ent)
            db.session.commit()
        self.websites.append({"name": name, "port": port, "onion_address": onion, "site_dir": site_dir})
        logging.info(f"Website '{name}' created on port {port} ({onion})")

    def stop(self):
        for n in self.nodes:
            try: n.stop()
            except Exception as e: logging.error(f"Stop node error: {e}")
        for w in list(self.websites):
            try: stop_hidden_service(w["name"])
            except Exception as e: logging.error(f"Stop HS error: {e}")
        self.nodes.clear(); self.websites.clear(); self.used_ports.clear(); self.used_ips.clear()
```

---

```99proxys/tor.py (Windows tor.exe)

import subprocess, time, logging
from pathlib import Path
from .config import CONFIG, TOR_DIR, HIDDEN_SERVICE_DIR

_processes = {}

def create_hidden_service(name: str, port: int) -> str:
    tor_bin = CONFIG.get("TOR_PATH", "tor.exe")
    hs_dir = HIDDEN_SERVICE_DIR / name
    hs_dir.mkdir(parents=True, exist_ok=True)
    (TOR_DIR / name).mkdir(parents=True, exist_ok=True)

    torrc = hs_dir / "torrc"
    torrc.write_text(f"""
HiddenServiceDir {hs_dir}
HiddenServicePort 80 127.0.0.1:{port}
Log notice stdout
""".strip(), encoding="utf-8")

    cmd = [tor_bin, "-f", str(torrc), "--DataDirectory", str(TOR_DIR / name), "--quiet"]
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(3)
        if proc.poll() is not None:
            out, err = proc.communicate(timeout=5)
            logging.error(f"tor.exe failed: {err.decode(errors='ignore')}")
            return ""
        _processes[name] = proc
        host_file = hs_dir / "hostname"
        for _ in range(50):
            if host_file.exists():
                onion = host_file.read_text(encoding="utf-8").strip()
                logging.info(f"Hidden service for {name}: {onion}")
                return onion
            time.sleep(0.2)
        logging.warning("hostname not found after tor start")
        return ""
    except Exception as e:
        logging.error(f"create_hidden_service error: {e}")
        return ""


def stop_hidden_service(name: str):
    p = _processes.pop(name, None)
    if p:
        try:
            p.terminate(); p.wait(timeout=5)
        except Exception:
            p.kill()
```

---

```99proxys/utils.py

import random

def choose_locale(locales):
    return random.choice(locales)
```

---

```99proxys/gui.py (Windows Tkinter)

import tkinter as tk
from tkinter import ttk, messagebox
from rich.console import Console

console = Console()

class ProxyGUI:
    def __init__(self, chain):
        self.chain = chain
        self.root = tk.Tk()
        self.root.title("99Proxys v5.0.0 – Windows")
        self.root.geometry("1100x750")
        self._build()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.mainloop()

    def _build(self):
        nb = ttk.Notebook(self.root); nb.pack(fill='both', expand=True)
        self.nodes_tab = ttk.Frame(nb); nb.add(self.nodes_tab, text="Proxy Nodes")
        self.web_tab = ttk.Frame(nb); nb.add(self.web_tab, text="Websites")

        # Nodes
        btns = ttk.Frame(self.nodes_tab); btns.pack(fill='x', pady=6)
        ttk.Button(btns, text="Start Chain", command=self.start_chain).pack(side='left', padx=4)
        ttk.Button(btns, text="Stop Chain", command=self.stop_chain).pack(side='left', padx=4)

        self.tree = ttk.Treeview(self.nodes_tab, columns=("Host","Port","Locale","VIP","MAC","Active","Req","Err"), show='headings')
        for c in ("Host","Port","Locale","VIP","MAC","Active","Req","Err"):
            self.tree.heading(c, text=c)
        self.tree.pack(fill='both', expand=True, padx=8, pady=8)

        # Websites
        wfrm = ttk.Frame(self.web_tab); wfrm.pack(fill='x', pady=6)
        ttk.Label(wfrm, text="Website Name:").pack(side='left', padx=4)
        self.site_name = ttk.Entry(wfrm, width=30); self.site_name.pack(side='left')
        ttk.Button(wfrm, text="Create Website", command=self.create_site).pack(side='left', padx=4)

        self.web_tree = ttk.Treeview(self.web_tab, columns=("Name","Port","Onion"), show='headings')
        for c in ("Name","Port","Onion"):
            self.web_tree.heading(c, text=c)
        self.web_tree.pack(fill='both', expand=True, padx=8, pady=8)

    def refresh(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        for n in self.chain.nodes:
            self.tree.insert('', 'end', values=(n.host, n.port, n.locale['country'], n.virtual_ip, n.virtual_mac, "Yes" if n.active else "No", n.stats['requests'], n.stats['errors']))
        for i in self.web_tree.get_children(): self.web_tree.delete(i)
        for w in self.chain.websites:
            self.web_tree.insert('', 'end', values=(w['name'], w['port'], w['onion_address']))

    def start_chain(self):
        try:
            self.chain.initialize_nodes(); self.refresh()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def stop_chain(self):
        self.chain.stop(); self.refresh()

    def create_site(self):
        name = self.site_name.get().strip() or "site"
        pages = [{"name":"index","html_content":f"<html><body><h1>Welcome to {name}</h1></body></html>","css_content":"","js_content":""}]
        try:
            self.chain.create_website(name, pages); self.refresh()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def on_close(self):
        self.chain.stop(); self.root.destroy()
```

---

```99proxys/webapp/__init__.py

from flask import Flask
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from ..config import CONFIG

socketio = SocketIO()
db = SQLAlchemy()
csrf = CSRFProtect()


def create_flask_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = __import__('uuid').uuid4().hex
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sites.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_size': 10, 'max_overflow': 20}

    csrf.init_app(app)
    db.init_app(app)
    socketio.init_app(app)

    from .models import init_db
    init_db(app)

    from .routes import register_routes
    register_routes(app)

    return app
```

---

```99proxys/webapp/models.py

from . import db
from datetime import datetime

class Website(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    onion_address = db.Column(db.String(100), nullable=True)
    port = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.String(50), nullable=False)
    pages = db.relationship('Page', backref='website', lazy=True, cascade="all, delete-orphan")
    reviews = db.relationship('Review', backref='website', lazy=True, cascade="all, delete-orphan")
    chat_messages = db.relationship('ChatMessage', backref='website', lazy=True, cascade="all, delete-orphan")

class Page(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    website_id = db.Column(db.Integer, db.ForeignKey('website.id'), nullable=False)
    name = db.Column(db.String(80), nullable=False)
    html_content = db.Column(db.Text, nullable=False)
    css_content = db.Column(db.Text, nullable=True)
    js_content = db.Column(db.Text, nullable=True)
    path = db.Column(db.String(100), nullable=False)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    website_id = db.Column(db.Integer, db.ForeignKey('website.id'), nullable=False)
    name = db.Column(db.String(80), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.String(50), nullable=False)

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    website_id = db.Column(db.Integer, db.ForeignKey('website.id'), nullable=False)
    username = db.Column(db.String(80), nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.String(50), nullable=False)

    def as_dict(self):
        return {
            "id": self.id,
            "website_id": self.website_id,
            "username": self.username,
            "message": self.message,
            "timestamp": self.timestamp,
        }


def init_db(app):
    with app.app_context():
        db.create_all()
```

---

```99proxys/webapp/routes.py

from flask import request, jsonify, render_template, send_from_directory, redirect, flash
from . import db, socketio, csrf
from .models import Website, Page, Review, ChatMessage
from ..config import SITES_DIR
from werkzeug.utils import secure_filename
from datetime import datetime
from pathlib import Path


def register_routes(app):

    @app.route('/')
    def home():
        return "99Proxys Web API"

    @app.route('/editor/<website_name>')
    def editor(website_name):
        website = Website.query.filter_by(name=secure_filename(website_name)).first()
        if not website:
            return "Website not found", 404
        pages = Page.query.filter_by(website_id=website.id).all()
        return render_template('editor.html', website_name=website_name, pages=pages)

    @app.route('/get_page/<website_name>/<page_name>')
    def get_page(website_name, page_name):
        website = Website.query.filter_by(name=secure_filename(website_name)).first()
        if not website:
            return jsonify({"error":"Website not found"}), 404
        page = Page.query.filter_by(website_id=website.id, name=secure_filename(page_name)).first()
        if not page:
            return jsonify({"error":"Page not found"}), 404
        return jsonify({"html_content": page.html_content, "css_content": page.css_content, "js_content": page.js_content})

    @app.route('/update_page', methods=['POST'])
    @csrf.exempt
    def update_page():
        try:
            data = request.get_json()
            website_name = secure_filename(data['website_name'])
            page_name = secure_filename(data['page_name'])
            html_content = data['html_content']
            css_content = data.get('css_content','')
            js_content = data.get('js_content','')
            website = Website.query.filter_by(name=website_name).first()
            if not website:
                return jsonify({"error":"Website not found"}), 404
            page = Page.query.filter_by(website_id=website.id, name=page_name).first()
            if not page:
                return jsonify({"error":"Page not found"}), 404
            page.html_content, page.css_content, page.js_content = html_content, css_content, js_content
            pdir = SITES_DIR / website_name / page_name
            pdir.mkdir(parents=True, exist_ok=True)
            (pdir/"index.html").write_text(html_content, encoding='utf-8')
            if css_content: (pdir/"styles.css").write_text(css_content, encoding='utf-8')
            if js_content: (pdir/"script.js").write_text(js_content, encoding='utf-8')
            db.session.commit()
            return jsonify({"message":"Page updated successfully"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/add_page', methods=['POST'])
    @csrf.exempt
    def add_page():
        data = request.get_json()
        website_name = secure_filename(data['website_name'])
        page_name = secure_filename(data['page_name'])
        website = Website.query.filter_by(name=website_name).first()
        if not website:
            return jsonify({"error":"Website not found"}), 404
        html_content = data.get('html_content','<html><body><h1>New Page</h1></body></html>')
        css_content = data.get('css_content','')
        js_content = data.get('js_content','')
        pdir = SITES_DIR / website_name / page_name
        pdir.mkdir(parents=True, exist_ok=True)
        (pdir/"index.html").write_text(html_content, encoding='utf-8')
        if css_content: (pdir/"styles.css").write_text(css_content, encoding='utf-8')
        if js_content: (pdir/"script.js").write_text(js_content, encoding='utf-8')
        page = Page(website_id=website.id, name=page_name, html_content=html_content, css_content=css_content, js_content=js_content, path=str(pdir.relative_to(SITES_DIR)))
        db.session.add(page); db.session.commit()
        return jsonify({"message":"Page added successfully"})

    @app.route('/chat')
    def chat():
        return render_template('chat.html')

    @socketio.on('message')
    def handle_message(data):
        website = Website.query.first()
        if not website: return
        msg = ChatMessage(website_id=website.id, username=secure_filename(data.get('username','anon')), message=data.get('message',''), timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        db.session.add(msg); db.session.commit()
        socketio.emit('message', msg.as_dict(), broadcast=True)

    @app.route('/reviews', methods=['GET','POST'])
    def reviews():
        from flask_wtf import FlaskForm
        from wtforms import StringField, IntegerField, TextAreaField, SubmitField
        from wtforms.validators import DataRequired, NumberRange
        class ReviewForm(FlaskForm):
            name = StringField('Name', validators=[DataRequired()])
            rating = IntegerField('Rating', validators=[DataRequired(), NumberRange(min=1, max=5)])
            comment = TextAreaField('Comment', validators=[DataRequired()])
            submit = SubmitField('Submit Review')
        form = ReviewForm()
        website = Website.query.first()
        if request.method == 'POST' and form.validate_on_submit():
            rv = Review(website_id=website.id if website else None, name=form.name.data, rating=form.rating.data, comment=form.comment.data, timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            db.session.add(rv); db.session.commit(); flash('Review submitted!', 'success'); return redirect('/reviews')
        rvws = Review.query.filter_by(website_id=website.id if website else None).all() if website else []
        return render_template('reviews.html', reviews=rvws, website_name=website.name if website else "")

    @app.route('/sites/<path:path>')
    def serve_site(path):
        return send_from_directory(str(SITES_DIR), path)

    @app.route('/status')
    def status():
        websites = [{"name": w.name, "port": w.port, "onion_address": w.onion_address} for w in Website.query.all()]
        return jsonify({"websites": websites, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
```

---

```99proxys/webapp/templates/chat.html

<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Chatroom</title>
<script src="https://cdn.socket.io/4.7.5/socket.io.min.js"></script>
</head>
<body>
  <h2>Chat</h2>
  <div id="msgs" style="height:300px;overflow:auto;border:1px solid #ccc;padding:8px"></div>
  <input id="user" placeholder="name"> <input id="text" placeholder="message">
  <button onclick="send()">Send</button>
<script>
const s = io();
s.on('message',m=>{ const d=document.getElementById('msgs'); const p=document.createElement('div'); p.textContent=`${m.timestamp} ${m.username}: ${m.message}`; d.appendChild(p); d.scrollTop=d.scrollHeight; });
function send(){ const u=document.getElementById('user').value||'anon'; const t=document.getElementById('text').value||''; s.emit('message',{username:u,message:t}); document.getElementById('text').value=''; }
</script>
</body>
</html>
```

---

```99proxys/webapp/templates/reviews.html

<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{ website_name }} Reviews</title>
</head>
<body>
  <h2>{{ website_name }} Reviews</h2>
  <form method="POST">{{ form.hidden_tag() }}
    <div>{{ form.name.label }} {{ form.name() }}</div>
    <div>{{ form.rating.label }} {{ form.rating(min=1,max=5) }}</div>
    <div>{{ form.comment.label }} {{ form.comment() }}</div>
    {{ form.submit() }}
  </form>
  {% with messages = get_flashed_messages(with_categories=true) %}
    {% if messages %}
      {% for category, message in messages %}
        <p style="color: {{ 'green' if category == 'success' else 'red' }}">{{ message }}</p>
      {% endfor %}
    {% endif %}
  {% endwith %}
  <hr/>
  {% for r in reviews %}
    <div><strong>{{ r.name }}</strong> – Rating: {{ r.rating }}<br/>{{ r.comment }}<br/><small>{{ r.timestamp }}</small></div>
  {% endfor %}
</body>
</html>
```

---

```99proxys/webapp/templates/editor.html

<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{ website_name }} – Editor</title>
<script src="https://cdn.ckeditor.com/4.22.1/standard/ckeditor.js"></script>
</head>
<body>
  <h2>{{ website_name }} Editor</h2>
  <label>Page:</label>
  <select id="pageSel" onchange="loadPage()">
    {% for p in pages %}<option value="{{ p.name }}">{{ p.name }}</option>{% endfor %}
  </select>
  <h3>HTML</h3><textarea id="html"></textarea>
  <h3>CSS</h3><textarea id="css"></textarea>
  <h3>JS</h3><textarea id="js"></textarea>
  <button onclick="save()">Save</button>
  <script>
  CKEDITOR.replace('html'); CKEDITOR.replace('css'); CKEDITOR.replace('js');
  function loadPage(){ const n=document.getElementById('pageSel').value; fetch(`/get_page/{{ website_name }}/${n}`).then(r=>r.json()).then(d=>{ CKEDITOR.instances.html.setData(d.html_content||''); CKEDITOR.instances.css.setData(d.css_content||''); CKEDITOR.instances.js.setData(d.js_content||''); }); }
  function save(){ const n=document.getElementById('pageSel').value; const payload={website_name:'{{ website_name }}', page_name:n, html_content:CKEDITOR.instances.html.getData(), css_content:CKEDITOR.instances.css.getData(), js_content:CKEDITOR.instances.js.getData()}; fetch('/update_page',{method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)}).then(r=>r.json()).then(d=>{ alert(d.message||d.error||'OK'); }); }
  window.onload=loadPage;
  </script>
</body>
</html>
```

---

```README.md (snippet)

# 99Proxys – Windows‑Centric Modular Edition

- Run in a venv; install from `requirements.txt`.
- For OS virtual IP assignment, run **as Administrator** and set `ASSIGN_VIRTUAL_IP=true`.
- Tor integration expects `tor.exe` in PATH or set `TOR_PATH` env var.
- Listener TLS is off by default (`LISTENER_TLS=false`).
```
