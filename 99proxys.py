#!/usr/bin/env python3
"""
# 99Proxys - A proprietary local virtual VPN network from the BG Gremlin Group
# Copyright (c) 2025 BG Gremlin Group. All rights reserved.
# This software is proprietary and confidential. 
# Unauthorized copying, distribution, or modification
# Is strictly prohibited without express permission from the BG Gremlin Group.
# Contact: https://github.com/BGGremlin-Group
# Purpose: Creates a private Tor-like network with 5–99 SOCKS5 proxy nodes
# Supporting HTTPS, rolling IPs/MACs, and 99 locale simulations for enhanced anonymity.
# BGGG We Got 99Poxys, but Tibet Ain't One
"""
import os
import sys
import socket
import threading
import random
import time
import json
import logging
from datetime import datetime
import subprocess
import platform
from typing import List, Dict, Optional
from pathlib import Path
import socketserver
import ssl
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes
import psutil
import requests
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, BarColumn, TextColumn
from rich.panel import Panel
from plotext import plot
import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from timezonefinder import TimezoneFinder
import pkg_resources
from packaging import version

# Initialize Rich console for CLI
console = Console()

# Define project directories
BASE_DIR = Path(__file__).parent
CONFIG_DIR = BASE_DIR / "config"
LOG_DIR = BASE_DIR / "logs"
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"

# Create directories if they don't exist
for directory in [CONFIG_DIR, LOG_DIR, DATA_DIR, ASSETS_DIR]:
    directory.mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    filename=LOG_DIR / f"99proxys_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ASCII art banner
ASCII_ART = """
┏━━━┓┏━━━┓━━━━┏━━━┓━━━━━━━━━━━━━━━━━━━━
┃┏━┓┃┃┏━┓┃━━━━┃┏━┓┃━━━━━━━━━━━━━━━━━━━━
┃┗━┛┃┃┗━┛┃━━━━┃┗━┛┃┏━┓┏━━┓┏┓┏┓┏┓━┏┓┏━━┓
┗━━┓┃┗━━┓┃━━━━┃┏━━┛┃┏┛┃┏┓┃┗╋╋┛┃┃━┃┃┃━━┫
┏━━┛┃┏━━┛┃━━━━┃┃━━━┃┃━┃┗┛┃┏╋╋┓┃┗━┛┃┣━━┃
┗━━━┛┗━━━┛━━━━┗┛━━━┗┛━┗━━┛┗┛┗┛┗━┓┏┛┗━━┛
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┏━┛┃━━━━━
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┗━━┛━━━━━
                 99Proxys 
      - Private Local VPN Network -
       - BGGG Gremlin Group ©2025-
"""

# Expanded list of 99 locales
LOCALES = [
    {"country": "USA", "timezone": "America/New_York", "lat": 40.7128, "lon": -74.0060},
    {"country": "Switzerland", "timezone": "Europe/Zurich", "lat": 47.3769, "lon": 8.5417},
    {"country": "Mexico", "timezone": "America/Mexico_City", "lat": 19.4326, "lon": -99.1332},
    {"country": "Canada", "timezone": "America/Toronto", "lat": 43.6532, "lon": -79.3832},
    {"country": "China", "timezone": "Asia/Shanghai", "lat": 31.2304, "lon": 121.4737},
    {"country": "Russia", "timezone": "Europe/Moscow", "lat": 55.7558, "lon": 37.6173},
    {"country": "Ukraine", "timezone": "Europe/Kiev", "lat": 50.4501, "lon": 30.5234},
    {"country": "Thailand", "timezone": "Asia/Bangkok", "lat": 13.7563, "lon": 100.5018},
    {"country": "South Korea", "timezone": "Asia/Seoul", "lat": 37.5665, "lon": 126.9780},
    {"country": "Japan", "timezone": "Asia/Tokyo", "lat": 35.6762, "lon": 139.6503},
    {"country": "Brazil", "timezone": "America/Sao_Paulo", "lat": -23.5505, "lon": -46.6333},
    {"country": "Australia", "timezone": "Australia/Sydney", "lat": -33.8688, "lon": 151.2093},
    {"country": "India", "timezone": "Asia/Kolkata", "lat": 28.6139, "lon": 77.2090},
    {"country": "Germany", "timezone": "Europe/Berlin", " обратно: lat": 52.5200, "lon": 13.4050},
    {"country": "France", "timezone": "Europe/Paris", "lat": 48.8566, "lon": 2.3522},
    {"country": "UK", "timezone": "Europe/London", "lat": 51.5074, "lon": -0.1278},
    {"country": "South Africa", "timezone": "Africa/Johannesburg", "lat": -26.2041, "lon": 28.0473},
    {"country": "Nigeria", "timezone": "Africa/Lagos", "lat": 6.5244, "lon": 3.3792},
    {"country": "Argentina", "timezone": "America/Buenos_Aires", "lat": -34.6037, "lon": -58.3816},
    {"country": "Egypt", "timezone": "Africa/Cairo", "lat": 30.0444, "lon": 31.2357},
    {"country": "Italy", "timezone": "Europe/Rome", "lat": 41.9028, "lon": 12.4964},
    {"),

    {"country": "Spain", "timezone": "Europe/Madrid", "lat": 40.4168, "lon": -3.7038},
    {"country": "Netherlands", "timezone": "Europe/Amsterdam", "lat": 52.3676, "lon": 4.9041},
    {"country": "Sweden", "timezone": "Europe/Stockholm", "lat": 59.3293, "lon": 18.0686},
    {"country": "Norway", "timezone": "Europe/Oslo", "lat": 59.9139, "lon": 10.7522},
    {"country": "Poland", "timezone": "Europe/Warsaw", "lat": 52.2297, "lon": 21.0122},
    {"country": "Turkey", "timezone": "Europe/Istanbul", "lat": 41.0082, "lon": 28.9784},
    {"country": "Saudi Arabia", "timezone": "Asia/Riyadh", "lat": 24.7136, "lon": 46.6753},
    {"country": "UAE", "timezone": "Asia/Dubai", "lat": 25.2048, "lon": 55.2708},
    {"country": "Indonesia", "timezone": "Asia/Jakarta", "lat": -6.2088, "lon": 106.8456},
    {"country": "Philippines", "timezone": "Asia/Manila", "lat": 14.5995, "lon": 120.9842},
    {"country": "Vietnam", "timezone": "Asia/Ho_Chi_Minh", "lat": 10.7769, "lon": 106.7009},
    {"country": "Malaysia", "timezone": "Asia/Kuala_Lumpur", "lat": 3.1390, "lon": 101.6869},
    {"country": "Singapore", "timezone": "Asia/Singapore", "lat": 1.3521, "lon": 103.8198},
    {"country": "New Zealand", "timezone": "Pacific/Auckland", "lat": -36.8485, "lon": 174.7633},
    {"country": "Chile", "timezone": "America/Santiago", "lat": -33.4489, "lon": -70.6693},
    {"country": "Colombia", "timezone": "America/Bogota", "lat": 4.7110, "lon": -74.0721},
    {"country": "Peru", "timezone": "America/Lസ: Lima", "lat": -12.0464, "lon": -77.0428},
    {"country": "Venezuela", "timezone": "America/Caracas", "lat": 10.4806, "lon": -66.9036},
    {"country": "Ecuador", "timezone": "America/Guayaquil", "lat": -2.1708, "lon": -79.922359},
    {"country": "Bolivia", "timezone": "America/La_Paz", "lat": -16.4897, "lon": -68.1193},
    {"country": "Uruguay", "timezone": "America/Montevideo", "lat": -34.9011, "lon": -56.1645},
    {"country": "Paraguay", "timezone": "America/Asuncion", "lat": -25.2637, "lon": -57.5759},
    {"country": "Costa Rica", "timezone": "America/Costa_Rica", "lat": 9.9281, "lon": -84.0907},
    {"country": "Panama", "timezone": "America/Panama", "lat": 8.9824, "lon": -79.5199},
    {"country": "Guatemala", "timezone": "America/Guatemala", "lat": 14.6349, "lon": - longitude: -90.5069},
    {"country": "Honduras", "timezone": "America/Tegucigalpa", "lat": 14.0723, "lon": -87.1921},
    {"country": "El Salvador", "timezone": "America/El_Salvador", "lat": 13.6929, "lon": -89.2182},
    {"country": "Nicaragua", "timezone": "America/Managua", "lat": 12.1140, "lon": -86.2362},
    {"country": "Cuba", "timezone": "America/Havana", "lat": 23.1136, "lon": -82.3660},
    {"country": "Dominican Republic", "timezone": "America/Santo_Domingo", "lat": 18.4861, "lon": -69.9312},
    {"country": "Algeria", "timezone": "Africa/Algiers", "lat": 36.7372, "lon": 3.0870},
    {"country": "Morocco", "timezone": "Africa/Casablanca", "lat": 33.5731, "lon": -7.5898},
    {"country": "Tunisia", "timezone": "Africa/Tunis", "lat": 36.8065, "lon": 10.1815},
    {"country": "Kenya", "timezone": "Africa/Nairobi", "lat": -1.2921, "lon": 36.8219},
    {"country": "Ghana", "timezone": "Africa/Accra", "lat": 5.6037, "lon": -0.1870},
    {"country": "Ethiopia", "timezone": "Africa/Addis_Ababa", "lat": 9.0240, "lon": 38.7469},
    {"country": "Angola", "timezone": "Africa/Luanda", "lat": -8.8390, "lon": 13.2894},
    {"country": "Sudan", "timezone": "Africa/Khartoum", "lat": 15.5007, "lon": 32.5599},
    {"country": "Libya", "timezone": "Africa/Tripoli", "lat": 32.8872, "lon": 13.1913},
    {"country": "Zimbabwe", "timezone": "Africa/Harare", "lat": -17.8252, "lon": 31.0335},
    {"country": "Botswana", "timezone": "Africa/Gaborone", "lat": -24.6282, "lon": 25.9231},
    {"country": "Namibia", "timezone": "Africa/Windhoek", "lat": -22.5609, "lon": 17.0658},
    {"country": "Mozambique", "timezone": "Africa/Maputo", "lat": -25.9692, "lon": 32.5732},
    {"country": "Zambia", "timezone": "Africa/Lusaka", "lat": -15.3875, "lon": 28.3228},
    {"country": "Malawi", "timezone": "Africa/Blantyre", "lat": -15.7667, "lon": 35.0168},
    {"country": "Madagascar", "timezone": "Indian/Antananarivo", "lat": -18.8792, "lon": 47.5079},
    {"country": "Austria", "timezone": "Europe/Vienna", "lat": 48.2082, "lon": 16.3738},
    {"country": "Belgium", "timezone": "Europe/Brussels", "lat": 50.8503, "lon": 4.3517},
    {"country": "Denmark", "timezone": "Europe/Copenhagen", "lat": 55.6761, "lon": 12.5683},
    {"country": "Finland", "timezone": "Europe/Helsinki", "lat": 60.1699, "lon": 24.9384},
    {"country": "Greece", "timezone": "Europe/Athens", "lat": 37.9838, "lon": 23.7275},
    {"country": "Hungary", "timezone": "Europe/Budapest", "lat": 47.4979, "lon": 19.0402},
    {"country": "Ireland", "timezone": "Europe/Dublin", "lat": 53.3498, "lon": -6.2603},
    {"country": "Portugal", "timezone": "Europe/Lisbon", "lat": 38.7223, "lon": -9.1393},
    {"country": "Romania", "timezone": "Europe/Bucharest", "lat": 44.4268, "lon": 26.1025},
    {"country": "Serbia", "timezone": "Europe/Belgrade", "lat": 44.7866, "lon": 20.4489},
    {"country": "Croatia", "timezone": "Europe/Zagreb", "lat": 45.8150, "lon": 15.9819},
    {"country": "Bulgaria", "timezone": "Europe/Sofia", "lat": 42.6977, "lon": 23.3219},
    {"country": "Czech Republic", "timezone": "Europe/Prague", "lat": 50.0755, "lon": 14.4378},
    {"country": "Slovakia", "timezone": "Europe/Bratislava", "lat": 48.1486, "lon": 17.1077},
    {"country": "Israel", "timezone": "Asia/Jerusalem", "lat": 31.7683, "lon": 35.2137},
    {"country": "Iran", "timezone": "Asia/Tehran", "lat": 35.6892, "lon": 51.3890},
    {"country": "Iraq", "timezone": "Asia/Baghdad", "lat": 33.3152, "lon": 44.3661},
    {"country": "Jordan", "timezone": "Asia/Amman", "lat": 31.9454, "lon": 35.9284},
    {"country": "Qatar", "timezone": "Asia/Qatar", "lat": 25.2760, "lon": 51.5200},
    {"country": "Kuwait", "timezone": "Asia/Kuwait", "lat": 29.3759, "lon": 47.9774},
    {"country": "Bangladesh", "timezone": "Asia/Dhaka", "lat": 23.8103, "lon": 90.4125},
    {"country": "Pakistan", "timezone": "Asia/Karachi", "lat": 24.8607, "lon": 67.0011},
    {"country": "Sri Lanka", "timezone": "Asia/Colombo", "lat": 6.9271, "lon": 79.8612},
    {"country": "Nepal", "timezone": "Asia/Kathmandu", "lat": 27.7172, "lon": 85.3240},
    {"country": "Myanmar", "timezone": "Asia/Yangon", "lat": 16.8409, "lon": 96.1735},
    {"country": "Cambodia", "timezone": "Asia/Phnom_Penh", "lat": 11.5564, "lon": 104.9282},
    {"country": "Laos", "timezone": "Asia/Vientiane", "lat": 17.9757, "lon": 102.6331},
    {"country": "Mongolia", "timezone": "Asia/Ulaanbaatar", "lat": 47.8864, "lon": 106.9057},
    {"country": "Fiji", "timezone": "Pacific/Fiji", "lat": -18.1248, "lon": 178.4501}
]

# Configuration file
CONFIG_FILE = CONFIG_DIR / "99proxys_config.json"

# Dependency requirements
REQUIRED_PACKAGES = {
    "scapy": "2.5.0",
    "rich": "13.7.1",
    "plotext": "5.2.8",
    "psutil": "5.9.8",
    "requests": "2.31.0",
    "cryptography": "42.0.5",
    "timezonefinder": "6.1.9",
    "matplotlib": "3.8.3",
}

def install_dependencies():
    """Install required dependencies silently on first run."""
    try:
        console.print("[green]Checking dependencies...[/green]")
        for package, required_version in REQUIRED_PACKAGES.items():
            try:
                installed_version = pkg_resources.get_distribution(package).version
                if version.parse(installed_version) < version.parse(required_version):
                    console.print(f"[yellow]Updating {package} to version {required_version}...[/yellow]")
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", f"{package}>={required_version}"])
            except pkg_resources.DistributionNotFound:
                console.print(f"[yellow]Installing {package}...[/yellow]")
                subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", f"{package}>={required_version}"])
        console.print("[green]All dependencies installed.[/green]")
    except Exception as e:
        console.print(f"[red]Error installing dependencies: {e}[/red]")
        logging.error(f"Dependency installation failed: {e}")
        sys.exit(1)

# Run dependency check on startup
install_dependencies()

# Import scapy after dependency installation
from scapy.all import get_if_list, get_if_addr, get_if_hwaddr

class ProxyNode:
    """Represents a single proxy node in the chain."""
    def __init__(self, host: str, port: int, locale: Dict, virtual_ip: str, virtual_mac: str):
        self.host = host
        self.port = port
        self.locale = locale
        self.virtual_ip = virtual_ip
        self.virtual_mac = virtual_mac
        self.server = None
        self.active = False
        self.stats = {"requests": 0, "bytes_sent": 0, "bytes_received": 0, "latency": 0.0}
        self.fernet = Fernet(Fernet.generate_key())  # Per-node encryption key

    def start(self, next_node: Optional['ProxyNode'] = None):
        """Start the proxy node as a SOCKS5 server with HTTPS support."""
        try:
            class SOCKS5Handler(socketserver.BaseRequestHandler):
                def handle(self):
                    self.stats["requests"] += 1
                    start_time = time.time()
                    try:
                        # SOCKS5 handshake
                        data = self.request.recv(2)
                        if data != b"\x05\x01\x00":  # SOCKS5, one auth method, no auth
                            self.request.sendall(b"\x05\xff")  # No acceptable methods
                            return
                        self.request.sendall(b"\x05\x00")  # No authentication required
                        data = self.request.recv(4)
                        if len(data) < 4:
                            return
                        cmd, _, atyp = data[1:4]
                        if atyp == 3:  # IPv4 address
                            addr = self.request.recv(4)
                            ip = socket.inet_ntoa(addr)
                            port = int.from_bytes(self.request.recv(2), 'big')
                        else:
                            self.request.sendall(b"\x05\x01\x00\x01" + b"\x00" * 4 + b"\x00\x00")  # Address type not supported
                            return

                        if cmd == 1:  # CONNECT command for HTTPS
                            if next_node:
                                # Forward to next node
                                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                                    try:
                                        sock.connect((next_node.host, next_node.port))
                                        # Send SOCKS5 CONNECT request to next node
                                        sock.sendall(b"\x05\x01\x00\x03" + addr + port.to_bytes(2, 'big'))
                                        reply = sock.recv(10)
                                        if reply.startswith(b"\x05\x00"):
                                            self.request.sendall(b"\x05\x00\x00\x01" + addr + port.to_bytes(2, 'big'))
                                            # Tunnel data
                                            self.tunnel(self.request, sock)
                                        else:
                                            self.request.sendall(b"\x05\x01\x00\x01" + b"\x00" * 4 + b"\x00\x00")
                                    except Exception as e:
                                        self.request.sendall(b"\x05\x01\x00\x01" + b"\x00" * 4 + b"\x00\x00")
                                        logging.error(f"Node {self.port} forwarding error: {e}")
                            else:
                                # Exit node: connect to external HTTPS server
                                try:
                                    with socket.create_connection((ip, port), timeout=5) as sock:
                                        self.request.sendall(b"\x05\x00\x00\x01" + addr + port.to_bytes(2, 'big'))
                                        self.tunnel(self.request, sock)
                                        self.stats["bytes_sent"] += len(data)
                                        self.stats["bytes_received"] += len(data)
                                except Exception as e:
                                    self.request.sendall(b"\x05\x01\x00\x01" + b"\x00" * 4 + b"\x00\x00")
                                    logging.error(f"Exit node {self.port} connection error: {e}")
                        else:
                            self.request.sendall(b"\x05\x07\x00\x01" + b"\x00" * 4 + b"\x00\x00")  # Command not supported
                        self.stats["latency"] = time.time() - start_time
                    except Exception as e:
                        logging.error(f"Node {self.port} error: {e}")
                        self.request.sendall(b"\x05\x01\x00\x01" + b"\x00" * 4 + b"\x00\x00")

                def tunnel(self, client_sock, target_sock):
                    """Tunnel data between client and target sockets."""
                    try:
                        while True:
                            data = client_sock.recv(8192)
                            if not data:
                                break
                            encrypted_data = self.fernet.encrypt(data)
                            target_sock.sendall(encrypted_data)
                            self.stats["bytes_sent"] += len(encrypted_data)
                            response = target_sock.recv(8192)
                            if not response:
                                break
                            decrypted_response = self.fernet.decrypt(response)
                            client_sock.sendall(decrypted_response)
                            self.stats["bytes_received"] += len(response)
                    except Exception as e:
                        logging.error(f"Tunnel error in node {self.port}: {e}")

            self.server = socketserver.ThreadingTCPServer((self.host, self.port), SOCKS5Handler)
            self.server.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server.node = self  # Attach node to server for stats access
            self.active = True
            threading.Thread(target=self.server.serve_forever, daemon=True).start()
            console.print(f"[green]Started node on {self.host}:{self.port} ({self.locale['country']})[/green]")
            logging.info(f"Node started on {self.host}:{self.port}")
        except Exception as e:
            console.print(f"[red]Failed to start node on {self.host}:{self.port}: {e}[/red]")
            logging.error(f"Node start failed on {self.host}:{self.port}: {e}")
            self.active = False

    def stop(self):
        """Stop the proxy node."""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.active = False
            console.print(f"[yellow]Stopped node on {self.host}:{self.port}[/yellow]")
            logging.info(f"Node stopped on {self.host}:{self.port}")

class ProxyChain:
    """Manages the chain of proxy nodes."""
    def __init__(self):
        self.nodes: List[ProxyNode] = []
        self.config = self.load_config()
        self.tf = TimezoneFinder()

    def load_config(self) -> Dict:
        """Load or create configuration file."""
        default_config = {
            "node_count": 5,
            "ip_range": "192.168.0.0/16",
            "locales": [locale["country"] for locale in LOCALES[:5]],  # Default to first 5 locales
            "min_port": 1024,
            "max_port": 65535,
            "min_speed_kbps": 56
        }
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r") as f:
                    return json.load(f)
            except Exception as e:
                console.print(f"[red]Error loading config: {e}, using defaults[/red]")
                logging.error(f"Config load failed: {e}")
        with open(CONFIG_FILE, "w") as f:
            json.dump(default_config, f, indent=4)
        return default_config

    def save_config(self):
        """Save configuration to file."""
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(self.config, f, indent=4)
            logging.info("Configuration saved")
        except Exception as e:
            console.print(f"[red]Error saving config: {e}[/red]")
            logging.error(f"Config save failed: {e}")

    def get_available_port(self) -> int:
        """Find an available port with retry logic."""
        max_attempts = 100
        attempt = 0
        while attempt < max_attempts:
            port = random.randint(self.config["min_port"], self.config["max_port"])
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                try:
                    s.bind(("127.0.0.1", port))
                    return port
                except OSError as e:
                    attempt += 1
                    logging.warning(f"Port {port} in use, trying another (attempt {attempt}/{max_attempts})")
                    time.sleep(0.1 * attempt)  # Exponential backoff
        raise RuntimeError(f"No available ports after {max_attempts} attempts")

    def generate_virtual_ip(self) -> str:
        """Generate a virtual IP within the configured range."""
        base, mask = self.config["ip_range"].split("/")
        octets = base.split(".")
        if mask == "16":
            return f"{octets[0]}.{octets[1]}.{random.randint(0, 255)}.{random.randint(1, 254)}"
        return f"192.168.{random.randint(0, 255)}.{random.randint(1, 254)}"

    def generate_virtual_mac(self) -> str:
        """Generate a random MAC address."""
        return ":".join([f"{random.randint(0, 255):02x}" for _ in range(6)])

    def setup_nodes(self):
        """Set up the proxy chain based on configuration."""
        self.stop_all_nodes()
        self.nodes.clear()
        cpu_usage = psutil.cpu_percent()
        memory_usage = psutil.virtual_memory().percent
        if cpu_usage > 80 or memory_usage > 80:
            console.print(f"[red]High system load (CPU: {cpu_usage}%, Memory: {memory_usage}%). Aborting setup.[/red]")
            logging.error(f"High system load: CPU {cpu_usage}%, Memory {memory_usage}%")
            return False
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            transient=True
        ) as progress:
            task = progress.add_task("Setting up proxy nodes...", total=self.config["node_count"])
            for i in range(self.config["node_count"]):
                try:
                    port = self.get_available_port()
                    locale = random.choice([l for l in LOCALES if l["country"] in self.config["locales"]])
                    node = ProxyNode(
                        host="127.0.0.1",
                        port=port,
                        locale=locale,
                        virtual_ip=self.generate_virtual_ip(),
                        virtual_mac=self.generate_virtual_mac()
                    )
                    self.nodes.append(node)
                    progress.advance(task)
                except Exception as e:
                    console.print(f"[red]Error setting up node {i+1}: {e}[/red]")
                    logging.error(f"Node setup failed: {e}")
                    return False
        # Start nodes in reverse order (exit node first) and validate chaining
        for i in range(len(self.nodes) - 1, -1, -1):
            next_node = self.nodes[i + 1] if i < len(self.nodes) - 1 else None
            self.nodes[i].start(next_node)
            if next_node:
                # Test connectivity to next node
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    try:
                        sock.settimeout(2)
                        sock.connect((next_node.host, next_node.port))
                        sock.sendall(b"\x05\x01\x00")
                        if not sock.recv(2) == b"\x05\x00":
                            console.print(f"[red]Chaining failed for node {i+1} to {i+2}[/red]")
                            logging.error(f"Chaining failed for node {i+1} to {i+2}")
                            return False
                    except Exception as e:
                        console.print(f"[red]Chaining test failed for node {i+1}: {e}[/red]")
                        logging.error(f"Chaining test failed for node {i+1}: {e}")
                        return False
        console.print(f"[green]Successfully set up {len(self.nodes)} nodes[/green]")
        logging.info(f"Successfully set up {len(self.nodes)} nodes")
        return True

    def stop_all_nodes(self):
        """Stop all proxy nodes."""
        for node in self.nodes:
            node.stop()
        self.nodes.clear()

    def roll_node(self, index: int):
        """Roll IP, MAC, and locale for a single node."""
        try:
            node = self.nodes[index]
            node.stop()
            node.virtual_ip = self.generate_virtual_ip()
            node.virtual_mac = self.generate_virtual_mac()
            node.locale = random.choice([l for l in LOCALES if l["country"] in self.config["locales"]])
            next_node = self.nodes[index + 1] if index < len(self.nodes) - 1 else None
            node.start(next_node)
            console.print(f"[cyan]Rolled node {index+1}: {node.virtual_ip}, {node.virtual_mac}, {node.locale['country']}[/cyan]")
            logging.info(f"Rolled node {index+1}: {node.virtual_ip}, {node.virtual_mac}, {node.locale['country']}")
        except Exception as e:
            console.print(f"[red]Error rolling node {index+1}: {e}[/red]")
            logging.error(f"Node roll failed: {e}")

    def roll_all(self):
        """Roll IP, MAC, and locale for all nodes."""
        cpu_usage = psutil.cpu_percent()
        memory_usage = psutil.virtual_memory().percent
        if cpu_usage > 80 or memory_usage > 80:
            console.print(f"[red]High system load (CPU: {cpu_usage}%, Memory: {memory_usage}%). Aborting roll.[/red]")
            logging.error(f"High system load during roll: CPU {cpu_usage}%, Memory {memory_usage}%")
            return
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            transient=True
        ) as progress:
            task = progress.add_task("Rolling all nodes...", total=len(self.nodes))
            for i in range(len(self.nodes)):
                self.roll_node(i)
                progress.advance(task)

    def get_stats(self) -> List[Dict]:
        """Get statistics for all nodes."""
        return [node.stats for node in self.nodes]

    def plot_stats(self):
        """Plot real-time stats in CLI."""
        plot.clear_figure()
        latencies = [node.stats["latency"] * 1000 for node in self.nodes]  # Convert to ms
        plot.bar([f"Node {i+1}" for i in range(len(self.nodes))], latencies, title="Node Latency (ms)")
        plot.show()

class ProxyGUI:
    """GUI for 99Proxys using tkinter."""
    def __init__(self, chain: ProxyChain):
        self.chain = chain
        self.root = tk.Tk()
        self.root.title("99Proxys")
        self.root.configure(bg="black")
        self.root.geometry("800x600")

        # Style
        style = ttk.Style()
        style.configure("TButton", background="black", foreground="cyan")
        style.configure("TLabel", background="black", foreground="yellow")

        # Main frame
        self.frame = ttk.Frame(self.root, padding=10)
        self.frame.pack(fill=tk.BOTH, expand=True)

        # ASCII art
        self.ascii_label = ttk.Label(self.frame, text=ASCII_ART, font=("Courier", 10), foreground="magenta")
        self.ascii_label.pack()

        # Node status
        self.status_table = ttk.Treeview(self.frame, columns=("Node", "IP", "MAC", "Locale", "Status"), show="headings")
        self.status_table.heading("Node", text="Node")
        self.status_table.heading("IP", text="IP Address")
        self.status_table.heading("MAC", text="MAC Address")
        self.status_table.heading("Locale", text="Locale")
        self.status_table.heading("Status", text="Status")
        self.status_table.pack(fill=tk.BOTH, expand=True)

        # Buttons
        self.button_frame = ttk.Frame(self.frame)
        self.button_frame.pack(pady=10)
        ttk.Button(self.button_frame, text="Roll All Nodes", command=self.chain.roll_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.button_frame, text="Stop All", command=self.chain.stop_all_nodes).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.button_frame, text="Setup Wizard", command=self.run_setup_wizard).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.button_frame, text="Exit", command=self.exit).pack(side=tk.LEFT, padx=5)

        # Graph
        self.fig, self.ax = plt.subplots(figsize=(6, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.update_status()
        self.update_graph()
        self.root.protocol("WM_DELETE_WINDOW", self.exit)

    def update_status(self):
        """Update node status table."""
        for item in self.status_table.get_children():
            self.status_table.delete(item)
        for i, node in enumerate(self.chain.nodes):
            self.status_table.insert("", tk.END, values=(
                f"Node {i+1}",
                node.virtual_ip,
                node.virtual_mac,
                node.locale["country"],
                "Active" if node.active else "Inactive"
            ))
        self.root.after(1000, self.update_status)

    def update_graph(self):
        """Update real-time latency graph."""
        self.ax.clear()
        latencies = [node.stats["latency"] * 1000 for node in self.chain.nodes]
        self.ax.bar([f"Node {i+1}" for i in range(len(self.chain.nodes))], latencies)
        self.ax.set_title("Node Latency (ms)", color="yellow")
        self.ax.set_facecolor("black")
        self.fig.set_facecolor("black")
        self.ax.tick_params(colors="cyan")
        self.canvas.draw()
        self.root.after(5000, self.update_graph)

    def run_setup_wizard(self):
        """Run configuration wizard."""
        wizard = tk.Toplevel(self.root)
        wizard.title("99Proxys Setup Wizard")
        wizard.configure(bg="black")

        ttk.Label(wizard, text="Number of Nodes (5-99):").pack(pady=5)
        node_count = tk.StringVar(value=str(self.chain.config["node_count"]))
        ttk.Entry(wizard, textvariable=node_count).pack()

        ttk.Label(wizard, text="IP Range (e.g., 192.168.0.0/16):").pack(pady=5)
        ip_range = tk.StringVar(value=self.chain.config["ip_range"])
        ttk.Entry(wizard, textvariable=ip_range).pack()

        ttk.Label(wizard, text="Locales (comma-separated, e.g., USA,Japan):").pack(pady=5)
        locales = tk.StringVar(value=",".join(self.chain.config["locales"]))
        ttk.Entry(wizard, textvariable=locales).pack()

        def save_config():
            try:
                self.chain.config["node_count"] = max(5, min(99, int(node_count.get())))
                self.chain.config["ip_range"] = ip_range.get()
                input_locales = [l.strip() for l in locales.get().split(",")]
                invalid_locales = [l for l in input_locales if l not in [loc["country"] for loc in LOCALES]]
                if invalid_locales:
                    raise ValueError(f"Invalid locales: {invalid_locales}")
                self.chain.config["locales"] = input_locales
                self.chain.save_config()
                self.chain.setup_nodes()
                wizard.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Invalid configuration: {e}")

        ttk.Button(wizard, text="Save", command=save_config).pack(pady=10)

    def exit(self):
        """Graceful exit."""
        self.chain.stop_all_nodes()
        self.root.destroy()

def run_cli(chain: ProxyChain):
    """Run the interactive CLI."""
    console.print(Panel(ASCII_ART, style="magenta on black"))
    while True:
        console.print("\n[cyan]99Proxys Menu[/cyan]")
        console.print("1. Setup Nodes")
        console.print("2. Roll All Nodes")
        console.print("3. Roll Single Node")
        console.print("4. Show Stats")
        console.print("5. Plot Stats")
        console.print("6. Stop All Nodes")
        console.print("7. Run Setup Wizard")
        console.print("0. Exit")
        choice = console.input("[green]Enter choice: [/green]")
        try:
            if choice == "1":
                chain.setup_nodes()
            elif choice == "2":
                chain.roll_all()
            elif choice == "3":
                index = int(console.input("Enter node index (1-{}): ".format(len(chain.nodes)))) - 1
                if 0 <= index < len(chain.nodes):
                    chain.roll_node(index)
                else:
                    console.print("[red]Invalid node index[/red]")
            elif choice == "4":
                table = Table(title="Node Stats")
                table.add_column("Node", style="cyan")
                table.add_column("IP", style="yellow")
                table.add_column("MAC", style="green")
                table.add_column("Locale", style="magenta")
                table.add_column("Requests", style="cyan")
                table.add_column("Latency (ms)", style="yellow")
                for i, node in enumerate(chain.nodes):
                    table.add_row(
                        f"Node {i+1}",
                        node.virtual_ip,
                        node.virtual_mac,
                        node.locale["country"],
                        str(node.stats["requests"]),
                        f"{node.stats['latency'] * 1000:.2f}"
                    )
                console.print(table)
            elif choice == "5":
                chain.plot_stats()
            elif choice == "6":
                chain.stop_all_nodes()
            elif choice == "7":
                console.print("[cyan]Setup Wizard[/cyan]")
                node_count = console.input(f"Number of nodes (5-99, default {chain.config['node_count']}): ")
                ip_range = console.input(f"IP range (default {chain.config['ip_range']}): ")
                locales = console.input(f"Locales (comma-separated, default {','.join(chain.config['locales'])}): ")
                try:
                    if node_count:
                        chain.config["node_count"] = max(5, min(99, int(node_count)))
                    if ip_range:
                        chain.config["ip_range"] = ip_range
                    if locales:
                        input_locales = [l.strip() for l in locales.split(",")]
                        invalid_locales = [l for l in input_locales if l not in [loc["country"] for loc in LOCALES]]
                        if invalid_locales:
                            raise ValueError(f"Invalid locales: {invalid_locales}")
                        chain.config["locales"] = input_locales
                    chain.save_config()
                    chain.setup_nodes()
                except Exception as e:
                    console.print(f"[red]Invalid configuration: {e}[/red]")
            elif choice == "0":
                chain.stop_all_nodes()
                console.print("[yellow]Exiting 99Proxys...[/yellow]")
                break
            else:
                console.print("[red]Invalid choice[/red]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            logging.error(f"CLI error: {e}")

def main():
    """Main entry point."""
    chain = ProxyChain()
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        run_cli(chain)
    else:
        gui = ProxyGUI(chain)
        gui.root.mainloop()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("[yellow]Received interrupt, shutting down...[/yellow]")
        chain = ProxyChain()
        chain.stop_all_nodes()
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]Fatal error: {e}[/red]")
        logging.error(f"Fatal error: {e}")
        sys.exit(1)
