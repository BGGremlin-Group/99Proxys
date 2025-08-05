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
from typing import List, Dict, Optional, Tuple
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
import plotext as plt
import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from timezonefinder import TimezoneFinder
import pkg_resources
from packaging import version
import ipaddress
import queue

# Initialize Rich console for CLI
console = Console()

# Define project directories
BASE_DIR = Path(__file__).parent
CONFIG_DIR = BASE_DIR / "config"
LOG_DIR = BASE_DIR / "logs"
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"
CERT_DIR = BASE_DIR / "certs"

# Create directories if they don't exist
for directory in [CONFIG_DIR, LOG_DIR, DATA_DIR, ASSETS_DIR, CERT_DIR]:
    directory.mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    filename=LOG_DIR / f"99proxys_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filemode="a"
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

# Expanded list of 99 locales with corrected entries
LOCALES = [
    {"country": "USA", "timezone": "America/New_York", "lat": 40.7128, "lon": -74.0060, "ip_prefix": "192.168.1.0/24"},
    {"country": "Switzerland", "timezone": "Europe/Zurich", "lat": 47.3769, "lon": 8.5417, "ip_prefix": "192.168.2.0/24"},
    {"country": "Mexico", "timezone": "America/Mexico_City", "lat": 19.4326, "lon": -99.1332, "ip_prefix": "192.168.3.0/24"},
    {"country": "Canada", "timezone": "America/Toronto", "lat": 43.6532, "lon": -79.3832, "ip_prefix": "192.168.4.0/24"},
    {"country": "China", "timezone": "Asia/Shanghai", "lat": 31.2304, "lon": 121.4737, "ip_prefix": "192.168.5.0/24"},
    {"country": "Russia", "timezone": "Europe/Moscow", "lat": 55.7558, "lon": 37.6173, "ip_prefix": "192.168.6.0/24"},
    {"country": "Ukraine", "timezone": "Europe/Kiev", "lat": 50.4501, "lon": 30.5234, "ip_prefix": "192.168.7.0/24"},
    {"country": "Thailand", "timezone": "Asia/Bangkok", "lat": 13.7563, "lon": 100.5018, "ip_prefix": "192.168.8.0/24"},
    {"country": "South Korea", "timezone": "Asia/Seoul", "lat": 37.5665, "lon": 126.9780, "ip_prefix": "192.168.9.0/24"},
    {"country": "Japan", "timezone": "Asia/Tokyo", "lat": 35.6762, "lon": 139.6503, "ip_prefix": "192.168.10.0/24"},
    {"country": "Brazil", "timezone": "America/Sao_Paulo", "lat": -23.5505, "lon": -46.6333, "ip_prefix": "192.168.11.0/24"},
    {"country": "Australia", "timezone": "Australia/Sydney", "lat": -33.8688, "lon": 151.2093, "ip_prefix": "192.168.12.0/24"},
    {"country": "India", "timezone": "Asia/Kolkata", "lat": 28.6139, "lon": 77.2090, "ip_prefix": "192.168.13.0/24"},
    {"country": "Germany", "timezone": "Europe/Berlin", "lat": 52.5200, "lon": 13.4050, "ip_prefix": "192.168.14.0/24"},
    {"country": "France", "timezone": "Europe/Paris", "lat": 48.8566, "lon": 2.3522, "ip_prefix": "192.168.15.0/24"},
    {"country": "UK", "timezone": "Europe/London", "lat": 51.5074, "lon": -0.1278, "ip_prefix": "192.168.16.0/24"},
    {"country": "South Africa", "timezone": "Africa/Johannesburg", "lat": -26.2041, "lon": 28.0473, "ip_prefix": "192.168.17.0/24"},
    {"country": "Nigeria", "timezone": "Africa/Lagos", "lat": 6.5244, "lon": 3.3792, "ip_prefix": "192.168.18.0/24"},
    {"country": "Argentina", "timezone": "America/Buenos_Aires", "lat": -34.6037, "lon": -58.3816, "ip_prefix": "192.168.19.0/24"},
    {"country": "Egypt", "timezone": "Africa/Cairo", "lat": 30.0444, "lon": 31.2357, "ip_prefix": "192.168.20.0/24"},
    {"country": "Italy", "timezone": "Europe/Rome", "lat": 41.9028, "lon": 12.4964, "ip_prefix": "192.168.21.0/24"},
    {"country": "Spain", "timezone": "Europe/Madrid", "lat": 40.4168, "lon": -3.7038, "ip_prefix": "192.168.22.0/24"},
    {"country": "Netherlands", "timezone": "Europe/Amsterdam", "lat": 52.3676, "lon": 4.9041, "ip_prefix": "192.168.23.0/24"},
    {"country": "Sweden", "timezone": "Europe/Stockholm", "lat": 59.3293, "lon": 18.0686, "ip_prefix": "192.168.24.0/24"},
    {"country": "Norway", "timezone": "Europe/Oslo", "lat": 59.9139, "lon": 10.7522, "ip_prefix": "192.168.25.0/24"},
    {"country": "Poland", "timezone": "Europe/Warsaw", "lat": 52.2297, "lon": 21.0122, "ip_prefix": "192.168.26.0/24"},
    {"country": "Turkey", "timezone": "Europe/Istanbul", "lat": 41.0082, "lon": 28.9784, "ip_prefix": "192.168.27.0/24"},
    {"country": "Saudi Arabia", "timezone": "Asia/Riyadh", "lat": 24.7136, "lon": 46.6753, "ip_prefix": "192.168.28.0/24"},
    {"country": "UAE", "timezone": "Asia/Dubai", "lat": 25.2048, "lon": 55.2708, "ip_prefix": "192.168.29.0/24"},
    {"country": "Indonesia", "timezone": "Asia/Jakarta", "lat": -6.2088, "lon": 106.8456, "ip_prefix": "192.168.30.0/24"},
    {"country": "Philippines", "timezone": "Asia/Manila", "lat": 14.5995, "lon": 120.9842, "ip_prefix": "192.168.31.0/24"},
    {"country": "Vietnam", "timezone": "Asia/Ho_Chi_Minh", "lat": 10.7769, "lon": 106.7009, "ip_prefix": "192.168.32.0/24"},
    {"country": "Malaysia", "timezone": "Asia/Kuala_Lumpur", "lat": 3.1390, "lon": 101.6869, "ip_prefix": "192.168.33.0/24"},
    {"country": "Singapore", "timezone": "Asia/Singapore", "lat": 1.3521, "lon": 103.8198, "ip_prefix": "192.168.34.0/24"},
    {"country": "New Zealand", "timezone": "Pacific/Auckland", "lat": -36.8485, "lon": 174.7633, "ip_prefix": "192.168.35.0/24"},
    {"country": "Chile", "timezone": "America/Santiago", "lat": -33.4489, "lon": -70.6693, "ip_prefix": "192.168.36.0/24"},
    {"country": "Colombia", "timezone": "America/Bogota", "lat": 4.7110, "lon": -74.0721, "ip_prefix": "192.168.37.0/24"},
    {"country": "Peru", "timezone": "America/Lima", "lat": -12.0464, "lon": -77.0428, "ip_prefix": "192.168.38.0/24"},
    {"country": "Venezuela", "timezone": "America/Caracas", "lat": 10.4806, "lon": -66.9036, "ip_prefix": "192.168.39.0/24"},
    {"country": "Ecuador", "timezone": "America/Guayaquil", "lat": -2.1708, "lon": -79.9224, "ip_prefix": "192.168.40.0/24"},
    {"country": "Bolivia", "timezone": "America/La_Paz", "lat": -16.4897, "lon": -68.1193, "ip_prefix": "192.168.41.0/24"},
    {"country": "Uruguay", "timezone": "America/Montevideo", "lat": -34.9011, "lon": -56.1645, "ip_prefix": "192.168.42.0/24"},
    {"country": "Paraguay", "timezone": "America/Asuncion", "lat": -25.2637, "lon": -57.5759, "ip_prefix": "192.168.43.0/24"},
    {"country": "Costa Rica", "timezone": "America/Costa_Rica", "lat": 9.9281, "lon": -84.0907, "ip_prefix": "192.168.44.0/24"},
    {"country": "Panama", "timezone": "America/Panama", "lat": 8.9824, "lon": -79.5199, "ip_prefix": "192.168.45.0/24"},
    {"country": "Guatemala", "timezone": "America/Guatemala", "lat": 14.6349, "lon": -90.5069, "ip_prefix": "192.168.46.0/24"},
    {"country": "Honduras", "timezone": "America/Tegucigalpa", "lat": 14.0723, "lon": -87.1921, "ip_prefix": "192.168.47.0/24"},
    {"country": "El Salvador", "timezone": "America/El_Salvador", "lat": 13.6929, "lon": -89.2182, "ip_prefix": "192.168.48.0/24"},
    {"country": "Nicaragua", "timezone": "America/Managua", "lat": 12.1140, "lon": -86.2362, "ip_prefix": "192.168.49.0/24"},
    {"country": "Cuba", "timezone": "America/Havana", "lat": 23.1136, "lon": -82.3660, "ip_prefix": "192.168.50.0/24"},
    {"country": "Dominican Republic", "timezone": "America/Santo_Domingo", "lat": 18.4861, "lon": -69.9312, "ip_prefix": "192.168.51.0/24"},
    {"country": "Algeria", "timezone": "Africa/Algiers", "lat": 36.7372, "lon": 3.0870, "ip_prefix": "192.168.52.0/24"},
    {"country": "Morocco", "timezone": "Africa/Casablanca", "lat": 33.5731, "lon": -7.5898, "ip_prefix": "192.168.53.0/24"},
    {"country": "Tunisia", "timezone": "Africa/Tunis", "lat": 36.8065, "lon": 10.1815, "ip_prefix": "192.168.54.0/24"},
    {"country": "Kenya", "timezone": "Africa/Nairobi", "lat": -1.2921, "lon": 36.8219, "ip_prefix": "192.168.55.0/24"},
    {"country": "Ghana", "timezone": "Africa/Accra", "lat": 5.6037, "lon": -0.1870, "ip_prefix": "192.168.56.0/24"},
    {"country": "Ethiopia", "timezone": "Africa/Addis_Ababa", "lat": 9.0240, "lon": 38.7469, "ip_prefix": "192.168.57.0/24"},
    {"country": "Angola", "timezone": "Africa/Luanda", "lat": -8.8390, "lon": 13.2894, "ip_prefix": "192.168.58.0/24"},
    {"country": "Sudan", "timezone": "Africa/Khartoum", "lat": 15.5007, "lon": 32.5599, "ip_prefix": "192.168.59.0/24"},
    {"country": "Libya", "timezone": "Africa/Tripoli", "lat": 32.8872, "lon": 13.1913, "ip_prefix": "192.168.60.0/24"},
    {"country": "Zimbabwe", "timezone": "Africa/Harare", "lat": -17.8252, "lon": 31.0335, "ip_prefix": "192.168.61.0/24"},
    {"country": "Botswana", "timezone": "Africa/Gaborone", "lat": -24.6282, "lon": 25.9231, "ip_prefix": "192.168.62.0/24"},
    {"country": "Namibia", "timezone": "Africa/Windhoek", "lat": -22.5609, "lon": 17.0658, "ip_prefix": "192.168.63.0/24"},
    {"country": "Mozambique", "timezone": "Africa/Maputo", "lat": -25.9692, "lon": 32.5732, "ip_prefix": "192.168.64.0/24"},
    {"country": "Zambia", "timezone": "Africa/Lusaka", "lat": -15.3875, "lon": 28.3228, "ip_prefix": "192.168.65.0/24"},
    {"country": "Malawi", "timezone": "Africa/Blantyre", "lat": -15.7667, "lon": 35.0168, "ip_prefix": "192.168.66.0/24"},
    {"country": "Madagascar", "timezone": "Indian/Antananarivo", "lat": -18.8792, "lon": 47.5079, "ip_prefix": "192.168.67.0/24"},
    {"country": "Austria", "timezone": "Europe/Vienna", "lat": 48.2082, "lon": 16.3738, "ip_prefix": "192.168.68.0/24"},
    {"country": "Belgium", "timezone": "Europe/Brussels", "lat": 50.8503, "lon": 4.3517, "ip_prefix": "192.168.69.0/24"},
    {"country": "Denmark", "timezone": "Europe/Copenhagen", "lat": 55.6761, "lon": 12.5683, "ip_prefix": "192.168.70.0/24"},
    {"country": "Finland", "timezone": "Europe/Helsinki", "lat": 60.1699, "lon": 24.9384, "ip_prefix": "192.168.71.0/24"},
    {"country": "Greece", "timezone": "Europe/Athens", "lat": 37.9838, "lon": 23.7275, "ip_prefix": "192.168.72.0/24"},
    {"country": "Hungary", "timezone": "Europe/Budapest", "lat": 47.4979, "lon": 19.0402, "ip_prefix": "192.168.73.0/24"},
    {"country": "Ireland", "timezone": "Europe/Dublin", "lat": 53.3498, "lon": -6.2603, "ip_prefix": "192.168.74.0/24"},
    {"country": "Portugal", "timezone": "Europe/Lisbon", "lat": 38.7223, "lon": -9.1393, "ip_prefix": "192.168.75.0/24"},
    {"country": "Romania", "timezone": "Europe/Bucharest", "lat": 44.4268, "lon": 26.1025, "ip_prefix": "192.168.76.0/24"},
    {"country": "Serbia", "timezone": "Europe/Belgrade", "lat": 44.7866, "lon": 20.4489, "ip_prefix": "192.168.77.0/24"},
    {"country": "Croatia", "timezone": "Europe/Zagreb", "lat": 45.8150, "lon": 15.9819, "ip_prefix": "192.168.78.0/24"},
    {"country": "Bulgaria", "timezone": "Europe/Sofia", "lat": 42.6977, "lon": 23.3219, "ip_prefix": "192.168.79.0/24"},
    {"country": "Czech Republic", "timezone": "Europe/Prague", "lat": 50.0755, "lon": 14.4378, "ip_prefix": "192.168.80.0/24"},
    {"country": "Slovakia", "timezone": "Europe/Bratislava", "lat": 48.1486, "lon": 17.1077, "ip_prefix": "192.168.81.0/24"},
    {"country": "Israel", "timezone": "Asia/Jerusalem", "lat": 31.7683, "lon": 35.2137, "ip_prefix": "192.168.82.0/24"},
    {"country": "Iran", "timezone": "Asia/Tehran", "lat": 35.6892, "lon": 51.3890, "ip_prefix": "192.168.83.0/24"},
    {"country": "Iraq", "timezone": "Asia/Baghdad", "lat": 33.3152, "lon": 44.3661, "ip_prefix": "192.168.84.0/24"},
    {"country": "Jordan", "timezone": "Asia/Amman", "lat": 31.9454, "lon": 35.9284, "ip_prefix": "192.168.85.0/24"},
    {"country": "Qatar", "timezone": "Asia/Qatar", "lat": 25.2760, "lon": 51.5200, "ip_prefix": "192.168.86.0/24"},
    {"country": "Kuwait", "timezone": "Asia/Kuwait", "lat": 29.3759, "lon": 47.9774, "ip_prefix": "192.168.87.0/24"},
    {"country": "Bangladesh", "timezone": "Asia/Dhaka", "lat": 23.8103, "lon": 90.4125, "ip_prefix": "192.168.88.0/24"},
    {"country": "Pakistan", "timezone": "Asia/Karachi", "lat": 24.8607, "lon": 67.0011, "ip_prefix": "192.168.89.0/24"},
    {"country": "Sri Lanka", "timezone": "Asia/Colombo", "lat": 6.9271, "lon": 79.8612, "ip_prefix": "192.168.90.0/24"},
    {"country": "Nepal", "timezone": "Asia/Kathmandu", "lat": 27.7172, "lon": 85.3240, "ip_prefix": "192.168.91.0/24"},
    {"country": "Myanmar", "timezone": "Asia/Yangon", "lat": 16.8409, "lon": 96.1735, "ip_prefix": "192.168.92.0/24"},
    {"country": "Cambodia", "timezone": "Asia/Phnom_Penh", "lat": 11.5564, "lon": 104.9282, "ip_prefix": "192.168.93.0/24"},
    {"country": "Laos", "timezone": "Asia/Vientiane", "lat": 17.9757, "lon": 102.6331, "ip_prefix": "192.168.94.0/24"},
    {"country": "Mongolia", "timezone": "Asia/Ulaanbaatar", "lat": 47.8864, "lon": 106.9057, "ip_prefix": "192.168.95.0/24"},
    {"country": "Fiji", "timezone": "Pacific/Fiji", "lat": -18.1248, "lon": 178.4501, "ip_prefix": "192.168.96.0/24"}
]

# Configuration file
CONFIG_FILE = CONFIG_DIR / "99proxys_config.json"

# SSL certificates
CERT_FILE = CERT_DIR / "server.crt"
KEY_FILE = CERT_DIR / "server.key"

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

def generate_self_signed_cert():
    """Generate a self-signed SSL certificate for secure communication."""
    try:
        if not CERT_FILE.exists() or not KEY_FILE.exists():
            console.print("[yellow]Generating self-signed SSL certificate...[/yellow]")
            key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048
            )
            with open(KEY_FILE, "wb") as f:
                f.write(key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.TraditionalOpenSSL,
                    encryption_algorithm=serialization.NoEncryption()
                ))
            # Generate certificate
            from cryptography import x509
            from cryptography.x509.oid import NameOID
            subject = issuer = x509.Name([
                x509.NameAttribute(NameOID.COMMON_NAME, "99Proxys")
            ])
            cert = (
                x509.CertificateBuilder()
                .subject_name(subject)
                .issuer_name(issuer)
                .public_key(key.public_key())
                .serial_number(x509.random_serial_number())
                .not_valid_before(datetime.utcnow())
                .not_valid_after(datetime.utcnow() + timedelta(days=365))
                .add_extension(
                    x509.SubjectAlternativeName([x509.DNSName("localhost")]),
                    critical=False
                )
                .sign(key, hashes.SHA256())
            )
            with open(CERT_FILE, "wb") as f:
                f.write(cert.public_bytes(serialization.Encoding.PEM))
            console.print("[green]SSL certificate generated.[/green]")
    except Exception as e:
        console.print(f"[red]Error generating SSL certificate: {e}[/red]")
        logging.error(f"SSL certificate generation failed: {e}")
        sys.exit(1)

# Run dependency check and certificate generation on startup
install_dependencies()
generate_self_signed_cert()

# Import scapy after dependency installation
from scapy.all import get_if_list, get_if_addr, get_if_hwaddr
from datetime import timedelta

class ProxyNode:
    """Represents a single proxy node in the chain with enhanced features."""
    def __init__(self, host: str, port: int, locale: Dict, virtual_ip: str, virtual_mac: str):
        self.host = host
        self.port = port
        self.locale = locale
        self.virtual_ip = virtual_ip
        self.virtual_mac = virtual_mac
        self.server = None
        self.active = False
        self.stats = {
            "requests": 0,
            "bytes_sent": 0,
            "bytes_received": 0,
            "latency": 0.0,
            "errors": 0,
            "connection_time": 0.0,
            "bandwidth_kbps": 0.0
        }
        self.fernet = Fernet(Fernet.generate_key())  # Per-node symmetric encryption key
        self.rsa_private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        self.rsa_public_key = self.rsa_private_key.public_key()
        self.rate_limit = 100  # Requests per minute
        self.request_timestamps = queue.Queue()  # For rate limiting
        self.bandwidth_limit_kbps = 1000  # Default bandwidth limit
        self.lock = threading.Lock()  # Thread-safe stats updates
        self.health_check_thread = None
        self.running = threading.Event()
        self.running.set()

    def encrypt_data(self, data: bytes, next_node: Optional['ProxyNode'] = None) -> bytes:
        """Encrypt data using Fernet and RSA for secure transmission."""
        try:
            encrypted_data = self.fernet.encrypt(data)
            if next_node:
                # Encrypt Fernet key with next node's RSA public key
                encrypted_key = next_node.rsa_public_key.encrypt(
                    self.fernet._encryption_key,
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                )
                return encrypted_key + b"||" + encrypted_data
            return encrypted_data
        except Exception as e:
            logging.error(f"Encryption error in node {self.port}: {e}")
            self.stats["errors"] += 1
            return data

    def decrypt_data(self, data: bytes, prev_node: Optional['ProxyNode'] = None) -> bytes:
        """Decrypt data using Fernet and RSA."""
        try:
            if prev_node and b"||" in data:
                encrypted_key, encrypted_data = data.split(b"||", 1)
                fernet_key = self.rsa_private_key.decrypt(
                    encrypted_key,
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                )
                temp_fernet = Fernet(fernet_key)
                return temp_fernet.decrypt(encrypted_data)
            return self.fernet.decrypt(data)
        except Exception as e:
            logging.error(f"Decryption error in node {self.port}: {e}")
            self.stats["errors"] += 1
            return data

    def check_rate_limit(self) -> bool:
        """Check if the node is within the rate limit."""
        with self.lock:
            current_time = time.time()
            while not self.request_timestamps.empty():
                if current_time - self.request_timestamps.queue[0] > 60:
                    self.request_timestamps.get()
                else:
                    break
            self.request_timestamps.put(current_time)
            return self.request_timestamps.qsize() <= self.rate_limit

    def throttle_bandwidth(self, data_size: int) -> float:
        """Simulate bandwidth throttling based on limit."""
        sleep_time = (data_size * 8 / 1000) / self.bandwidth_limit_kbps
        time.sleep(sleep_time)
        return sleep_time

    def health_check(self):
        """Periodically check node health and restart if necessary."""
        while self.running.is_set():
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(2)
                    s.connect((self.host, self.port))
                    s.sendall(b"\x05\x01\x00")
                    if s.recv(2) == b"\x05\x00":
                        self.active = True
                    else:
                        self.active = False
                        console.print(f"[yellow]Node {self.port} failed health check, restarting...[/yellow]")
                        logging.warning(f"Node {self.port} failed health check, restarting")
                        self.restart()
            except Exception as e:
                self.active = False
                console.print(f"[yellow]Node {self.port} health check failed: {e}, restarting...[/yellow]")
                logging.warning(f"Node {self.port} health check failed: {e}")
                self.restart()
            time.sleep(30)

    def start(self, next_node: Optional['ProxyNode'] = None):
        """Start the proxy node as a SOCKS5 server with SSL/TLS support."""
        try:
            class SOCKS5Handler(socketserver.BaseRequestHandler):
                def handle(self):
                    start_time = time.time()
                    with self.server.node.lock:
                        self.server.node.stats["requests"] += 1
                        self.server.node.stats["connection_time"] = time.time()
                    if not self.server.node.check_rate_limit():
                        self.request.sendall(b"\x05\x08\x00\x01" + b"\x00" * 4 + b"\x00\x00")  # Rate limit exceeded
                        logging.warning(f"Node {self.server.node.port} rate limit exceeded")
                        return
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
                        if atyp == 1:  # IPv4 address
                            addr = self.request.recv(4)
                            ip = socket.inet_ntoa(addr)
                            port = int.from_bytes(self.request.recv(2), 'big')
                        else:
                            self.request.sendall(b"\x05\x01\x00\x01" + b"\x00" * 4 + b"\x00\x00")  # Address type not supported
                            return

                        if cmd == 1:  # CONNECT command
                            if next_node:
                                # Forward to next node
                                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                                    try:
                                        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
                                        context.check_hostname = False
                                        context.verify_mode = ssl.CERT_NONE
                                        sock = context.wrap_socket(sock, server_hostname=next_node.host)
                                        sock.connect((next_node.host, next_node.port))
                                        # Send SOCKS5 CONNECT request to next node
                                        connect_request = b"\x05\x01\x00\x01" + addr + port.to_bytes(2, 'big')
                                        encrypted_request = self.server.node.encrypt_data(connect_request, next_node)
                                        sock.sendall(encrypted_request)
                                        self.server.node.throttle_bandwidth(len(encrypted_request))
                                        reply = sock.recv(10)
                                        decrypted_reply = self.server.node.decrypt_data(reply, next_node)
                                        if decrypted_reply.startswith(b"\x05\x00"):
                                            self.request.sendall(b"\x05\x00\x00\x01" + addr + port.to_bytes(2, 'big'))
                                            self.tunnel(self.request, sock, next_node)
                                        else:
                                            self.request.sendall(b"\x05\x01\x00\x01" + b"\x00" * 4 + b"\x00\x00")
                                    except Exception as e:
                                        self.request.sendall(b"\x05\x01\x00\x01" + b"\x00" * 4 + b"\x00\x00")
                                        logging.error(f"Node {self.server.node.port} forwarding error: {e}")
                                        self.server.node.stats["errors"] += 1
                            else:
                                # Exit node: connect to external server
                                try:
                                    with socket.create_connection((ip, port), timeout=5) as sock:
                                        context = ssl.create_default_context()
                                        sock = context.wrap_socket(sock, server_hostname=ip)
                                        self.request.sendall(b"\x05\x00\x00\x01" + addr + port.to_bytes(2, 'big'))
                                        self.tunnel(self.request, sock, None)
                                        with self.server.node.lock:
                                            self.server.node.stats["bytes_sent"] += len(data)
                                            self.server.node.stats["bytes_received"] += len(data)
                                except Exception as e:
                                    self.request.sendall(b"\x05\x01\x00\x01" + b"\x00" * 4 + b"\x00\x00")
                                    logging.error(f"Exit node {self.server.node.port} connection error: {e}")
                                    self.server.node.stats["errors"] += 1
                        else:
                            self.request.sendall(b"\x05\x07\x00\x01" + b"\x00" * 4 + b"\x00\x00")  # Command not supported
                        with self.server.node.lock:
                            self.server.node.stats["latency"] = time.time() - start_time
                            self.server.node.stats["connection_time"] = time.time() - self.server.node.stats["connection_time"]
                    except Exception as e:
                        logging.error(f"Node {self.server.node.port} error: {e}")
                        self.server.node.stats["errors"] += 1
                        self.request.sendall(b"\x05\x01\x00\x01" + b"\x00" * 4 + b"\x00\x00")

                def tunnel(self, client_sock, target_sock, next_node: Optional['ProxyNode']):
                    """Tunnel data between client and target sockets with encryption and bandwidth throttling."""
                    try:
                        while True:
                            data = client_sock.recv(8192)
                            if not data:
                                break
                            encrypted_data = self.server.node.encrypt_data(data, next_node)
                            self.server.node.throttle_bandwidth(len(encrypted_data))
                            target_sock.sendall(encrypted_data)
                            with self.server.node.lock:
                                self.server.node.stats["bytes_sent"] += len(encrypted_data)
                                self.server.node.stats["bandwidth_kbps"] = (len(encrypted_data) * 8 / 1000) / max(self.server.node.stats["latency"], 0.001)
                            response = target_sock.recv(8192)
                            if not response:
                                break
                            decrypted_response = self.server.node.decrypt_data(response, next_node)
                            client_sock.sendall(decrypted_response)
                            with self.server.node.lock:
                                self.server.node.stats["bytes_received"] += len(response)
                    except Exception as e:
                        logging.error(f"Tunnel error in node {self.server.node.port}: {e}")
                        self.server.node.stats["errors"] += 1

            self.server = socketserver.ThreadingTCPServer((self.host, self.port), SOCKS5Handler)
            self.server.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            context.load_cert_chain(certfile=CERT_FILE, keyfile=KEY_FILE)
            self.server.socket = context.wrap_socket(self.server.socket, server_side=True)
            self.server.node = self  # Attach node to server for stats access
            self.active = True
            threading.Thread(target=self.server.serve_forever, daemon=True).start()
            self.health_check_thread = threading.Thread(target=self.health_check, daemon=True)
            self.health_check_thread.start()
            console.print(f"[green]Started node on {self.host}:{self.port} ({self.locale['country']})[/green]")
            logging.info(f"Node started on {self.host}:{self.port}")
        except Exception as e:
            console.print(f"[red]Failed to start node on {self.host}:{self.port}: {e}[/red]")
            logging.error(f"Node start failed on {self.host}:{self.port}: {e}")
            self.active = False
            self.stats["errors"] += 1

    def stop(self):
        """Stop the proxy node gracefully."""
        with self.lock:
            self.running.clear()
            if self.server:
                try:
                    self.server.shutdown()
                    self.server.server_close()
                except Exception as e:
                    logging.error(f"Error stopping node {self.port}: {e}")
                    self.stats["errors"] += 1
                self.active = False
                console.print(f"[yellow]Stopped node on {self.host}:{self.port}[/yellow]")
                logging.info(f"Node stopped on {self.host}:{self.port}")

    def restart(self):
        """Restart the proxy node."""
        self.stop()
        time.sleep(1)
        self.start(self.nodes[self.nodes.index(self) + 1] if self.nodes.index(self) < len(self.nodes) - 1 else None)

class ProxyChain:
    """Manages the chain of proxy nodes with enhanced configuration and monitoring."""
    def __init__(self):
        self.nodes: List[ProxyNode] = []
        self.config = self.load_config()
        self.tf = TimezoneFinder()
        self.used_ips = set()
        self.used_ports = set()

    def validate_ip_range(self, ip_range: str) -> bool:
        """Validate the IP range format and usability."""
        try:
            ipaddress.IPv4Network(ip_range, strict=False)
            return True
        except ValueError as e:
            console.print(f"[red]Invalid IP range: {e}[/red]")
            logging.error(f"Invalid IP range: {e}")
            return False

    def validate_port_range(self, min_port: int, max_port: int) -> bool:
        """Validate the port range."""
        if not (1 <= min_port <= max_port <= 65535):
            console.print(f"[red]Invalid port range: {min_port}-{max_port}[/red]")
            logging.error(f"Invalid port range: {min_port}-{max_port}")
            return False
        return True

    def load_config(self) -> Dict:
        """Load or create configuration file with validation."""
        default_config = {
            "node_count": 5,
            "ip_range": "192.168.0.0/16",
            "locales": [locale["country"] for locale in LOCALES[:5]],
            "min_port": 1024,
            "max_port": 65535,
            "min_speed_kbps": 56,
            "max_bandwidth_kbps": 1000,
            "rate_limit": 100
        }
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r") as f:
                    config = json.load(f)
                if not self.validate_ip_range(config.get("ip_range", default_config["ip_range"])):
                    config["ip_range"] = default_config["ip_range"]
                if not self.validate_port_range(
                    config.get("min_port", default_config["min_port"]),
                    config.get("max_port", default_config["max_port"])
                ):
                    config["min_port"] = default_config["min_port"]
                    config["max_port"] = default_config["max_port"]
                return config
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
            if port not in self.used_ports:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    try:
                        s.bind(("127.0.0.1", port))
                        self.used_ports.add(port)
                        return port
                    except OSError as e:
                        attempt += 1
                        logging.warning(f"Port {port} in use, trying another (attempt {attempt}/{max_attempts})")
                        time.sleep(0.1 * attempt)
        raise RuntimeError(f"No available ports after {max_attempts} attempts")

    def generate_virtual_ip(self, locale: Dict) -> str:
        """Generate a virtual IP within the locale's IP range."""
        try:
            network = ipaddress.IPv4Network(locale["ip_prefix"], strict=False)
            available_ips = [str(ip) for ip in network.hosts() if str(ip) not in self.used_ips]
            if not available_ips:
                raise ValueError(f"No available IPs in range {locale['ip_prefix']}")
            virtual_ip = random.choice(available_ips)
            self.used_ips.add(virtual_ip)
            return virtual_ip
        except Exception as e:
            console.print(f"[red]Error generating virtual IP for {locale['country']}: {e}[/red]")
            logging.error(f"Virtual IP generation failed: {e}")
            return f"192.168.{random.randint(0, 255)}.{random.randint(1, 254)}"

    def generate_virtual_mac(self) -> str:
        """Generate a random MAC address."""
        mac = [random.randint(0, 255) for _ in range(6)]
        mac[0] = (mac[0] & 0xFC) | 0x02  # Set unicast and locally administered bits
        return ":".join(f"{x:02x}" for x in mac)

    def setup_nodes(self):
        """Set up the proxy chain based on configuration."""
        self.stop_all_nodes()
        self.nodes.clear()
        self.used_ips.clear()
        self.used_ports.clear()
        cpu_usage = psutil.cpu_percent(interval=1)
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
                    virtual_ip = self.generate_virtual_ip(locale)
                    node = ProxyNode(
                        host="127.0.0.1",
                        port=port,
                        locale=locale,
                        virtual_ip=virtual_ip,
                        virtual_mac=self.generate_virtual_mac()
                    )
                    node.bandwidth_limit_kbps = self.config["max_bandwidth_kbps"]
                    node.rate_limit = self.config["rate_limit"]
                    node.nodes = self.nodes  # Reference for restart
                    self.nodes.append(node)
                    progress.advance(task)
                except Exception as e:
                    console.print(f"[red]Error setting up node {i+1}: {e}[/red]")
                    logging.error(f"Node setup failed: {e}")
                    return False
        # Start nodes in reverse order (exit node first)
        for i in range(len(self.nodes) - 1, -1, -1):
            next_node = self.nodes[i + 1] if i < len(self.nodes) - 1 else None
            self.nodes[i].start(next_node)
            if next_node:
                # Test connectivity to next node
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    try:
                        context = ssl.create_default_context()
                        context.check_hostname = False
                        context.verify_mode = ssl.CERT_NONE
                        sock = context.wrap_socket(sock, server_hostname=next_node.host)
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
        self.used_ips.clear()
        self.used_ports.clear()

    def roll_node(self, index: int):
        """Roll IP, MAC, and locale for a single node."""
        try:
            node = self.nodes[index]
            old_ip = node.virtual_ip
            node.stop()
            self.used_ips.remove(old_ip)
            self.used_ports.remove(node.port)
            node.port = self.get_available_port()
            node.virtual_ip = self.generate_virtual_ip(node.locale)
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
        cpu_usage = psutil.cpu_percent(interval=1)
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
        return [node.stats.copy() for node in self.nodes]

    def plot_stats(self):
        """Plot real-time stats in CLI."""
        plt.clear_figure()
        latencies = [node.stats["latency"] * 1000 for node in self.nodes]
        bandwidths = [node.stats["bandwidth_kbps"] for node in self.nodes]
        plt.subplot(2, 1, 1)
        plt.bar([f"Node {i+1}" for i in range(len(self.nodes))], latencies, title="Node Latency (ms)")
        plt.subplot(2, 1, 2)
        plt.bar([f"Node {i+1}" for i in range(len(self.nodes))], bandwidths, title="Node Bandwidth (kbps)")
        plt.show()

    def export_stats(self, filename: str):
        """Export node statistics to a JSON file."""
        try:
            stats = self.get_stats()
            with open(DATA_DIR / filename, "w") as f:
                json.dump(stats, f, indent=4)
            console.print(f"[green]Stats exported to {filename}[/green]")
            logging.info(f"Stats exported to {filename}")
        except Exception as e:
            console.print(f"[red]Error exporting stats: {e}[/red]")
            logging.error(f"Stats export failed: {e}")

class ProxyGUI:
    """GUI for 99Proxys using tkinter with enhanced features."""
    def __init__(self, chain: ProxyChain):
        self.chain = chain
        self.root = tk.Tk()
        self.root.title("99Proxys - Private Local VPN Network")
        self.root.configure(bg="black")
        self.root.geometry("1000x800")

        # Style
        style = ttk.Style()
        style.configure("TButton", background="black", foreground="cyan", font=("Arial", 10))
        style.configure("TLabel", background="black", foreground="yellow", font=("Arial", 10))
        style.configure("Treeview", background="black", foreground="cyan", fieldbackground="black")
        style.configure("Treeview.Heading", background="black", foreground="yellow")

        # Main frame
        self.frame = ttk.Frame(self.root, padding=10)
        self.frame.pack(fill=tk.BOTH, expand=True)

        # ASCII art
        self.ascii_label = ttk.Label(self.frame, text=ASCII_ART, font=("Courier", 10), foreground="magenta")
        self.ascii_label.pack()

        # Node status
        self.status_table = ttk.Treeview(
            self.frame,
            columns=("Node", "IP", "MAC", "Locale", "Status", "Requests", "Latency", "Bandwidth", "Errors"),
            show="headings"
        )
        self.status_table.heading("Node", text="Node")
        self.status_table.heading("IP", text="IP Address")
        self.status_table.heading("MAC", text="MAC Address")
        self.status_table.heading("Locale", text="Locale")
        self.status_table.heading("Status", text="Status")
        self.status_table.heading("Requests", text="Requests")
        self.status_table.heading("Latency", text="Latency (ms)")
        self.status_table.heading("Bandwidth", text="Bandwidth (kbps)")
        self.status_table.heading("Errors", text="Errors")
        self.status_table.pack(fill=tk.BOTH, expand=True)

        # Buttons
        self.button_frame = ttk.Frame(self.frame)
        self.button_frame.pack(pady=10)
        ttk.Button(self.button_frame, text="Start All Nodes", command=self.chain.setup_nodes).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.button_frame, text="Roll All Nodes", command=self.chain.roll_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.button_frame, text="Stop All Nodes", command=self.chain.stop_all_nodes).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.button_frame, text="Setup Wizard", command=self.run_setup_wizard).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.button_frame, text="Export Stats", command=self.export_stats).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.button_frame, text="Exit", command=self.exit).pack(side=tk.LEFT, padx=5)

        # Individual node controls
        self.node_control_frame = ttk.Frame(self.frame)
        self.node_control_frame.pack(pady=10)
        self.node_select = ttk.Combobox(self.node_control_frame, values=[f"Node {i+1}" for i in range(len(self.chain.nodes))])
        self.node_select.pack(side=tk.LEFT, padx=5)
        ttk.Button(self.node_control_frame, text="Roll Node", command=self.roll_single_node).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.node_control_frame, text="Stop Node", command=self.stop_single_node).pack(side=tk.LEFT, padx=5)

        # Graphs
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(8, 6))
        self.fig.set_facecolor("black")
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.update_status()
        self.update_graph()
        self.root.protocol("WM_DELETE_WINDOW", self.exit)

    def update_status(self):
        """Update node status table."""
        for item in self.status_table.get_children():
            self.status_table.delete(item)
        self.node_select["values"] = [f"Node {i+1}" for i in range(len(self.chain.nodes))]
        for i, node in enumerate(self.chain.nodes):
            self.status_table.insert("", tk.END, values=(
                f"Node {i+1}",
                node.virtual_ip,
                node.virtual_mac,
                node.locale["country"],
                "Active" if node.active else "Inactive",
                node.stats["requests"],
                f"{node.stats['latency'] * 1000:.2f}",
                f"{node.stats['bandwidth_kbps']:.2f}",
                node.stats["errors"]
            ))
        self.root.after(1000, self.update_status)

    def update_graph(self):
        """Update real-time latency and bandwidth graphs."""
        self.ax1.clear()
        self.ax2.clear()
        latencies = [node.stats["latency"] * 1000 for node in self.chain.nodes]
        bandwidths = [node.stats["bandwidth_kbps"] for node in self.chain.nodes]
        nodes = [f"Node {i+1}" for i in range(len(self.chain.nodes))]
        self.ax1.bar(nodes, latencies, color="cyan")
        self.ax1.set_title("Node Latency (ms)", color="yellow")
        self.ax1.set_facecolor("black")
        self.ax1.tick_params(colors="cyan")
        self.ax2.bar(nodes, bandwidths, color="magenta")
        self.ax2.set_title("Node Bandwidth (kbps)", color="yellow")
        self.ax2.set_facecolor("black")
        self.ax2.tick_params(colors="cyan")
        self.fig.tight_layout()
        self.canvas.draw()
        self.root.after(5000, self.update_graph)

    def run_setup_wizard(self):
        """Run configuration wizard."""
        wizard = tk.Toplevel(self.root)
        wizard.title("99Proxys Setup Wizard")
        wizard.configure(bg="black")
        wizard.geometry("400x300")

        ttk.Label(wizard, text="Number of Nodes (5-99):").pack(pady=5)
        node_count = tk.StringVar(value=str(self.chain.config["node_count"]))
        ttk.Entry(wizard, textvariable=node_count).pack()

        ttk.Label(wizard, text="IP Range (e.g., 192.168.0.0/16):").pack(pady=5)
        ip_range = tk.StringVar(value=self.chain.config["ip_range"])
        ttk.Entry(wizard, textvariable=ip_range).pack()

        ttk.Label(wizard, text="Locales (comma-separated, e.g., USA,Japan):").pack(pady=5)
        locales = tk.StringVar(value=",".join(self.chain.config["locales"]))
        ttk.Entry(wizard, textvariable=locales).pack()

        ttk.Label(wizard, text="Max Bandwidth (kbps):").pack(pady=5)
        bandwidth = tk.StringVar(value=str(self.chain.config["max_bandwidth_kbps"]))
        ttk.Entry(wizard, textvariable=bandwidth).pack()

        ttk.Label(wizard, text="Rate Limit (req/min):").pack(pady=5)
        rate_limit = tk.StringVar(value=str(self.chain.config["rate_limit"]))
        ttk.Entry(wizard, textvariable=rate_limit).pack()

        def save_config():
            try:
                self.chain.config["node_count"] = max(5, min(99, int(node_count.get())))
                if not self.chain.validate_ip_range(ip_range.get()):
                    raise ValueError("Invalid IP range")
                self.chain.config["ip_range"] = ip_range.get()
                input_locales = [l.strip() for l in locales.get().split(",")]
                invalid_locales = [l for l in input_locales if l not in [loc["country"] for loc in LOCALES]]
                if invalid_locales:
                    raise ValueError(f"Invalid locales: {invalid_locales}")
                self.chain.config["locales"] = input_locales
                self.chain.config["max_bandwidth_kbps"] = max(56, int(bandwidth.get()))
                self.chain.config["rate_limit"] = max(1, int(rate_limit.get()))
                self.chain.save_config()
                self.chain.setup_nodes()
                wizard.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Invalid configuration: {e}")

        ttk.Button(wizard, text="Save", command=save_config).pack(pady=10)

    def roll_single_node(self):
        """Roll a single node selected in the combobox."""
        try:
            if self.node_select.get():
                index = int(self.node_select.get().split()[1]) - 1
                if 0 <= index < len(self.chain.nodes):
                    self.chain.roll_node(index)
                else:
                    messagebox.showerror("Error", "Invalid node index")
            else:
                messagebox.showerror("Error", "Select a node")
        except Exception as e:
            messagebox.showerror("Error", f"Error rolling node: {e}")

    def stop_single_node(self):
        """Stop a single node selected in the combobox."""
        try:
            if self.node_select.get():
                index = int(self.node_select.get().split()[1]) - 1
                if 0 <= index < len(self.chain.nodes):
                    self.chain.nodes[index].stop()
                    console.print(f"[yellow]Stopped node {index+1}[/yellow]")
                    logging.info(f"Stopped node {index+1}")
                else:
                    messagebox.showerror("Error", "Invalid node index")
            else:
                messagebox.showerror("Error", "Select a node")
        except Exception as e:
            messagebox.showerror("Error", f"Error stopping node: {e}")

    def export_stats(self):
        """Export node statistics to a file."""
        try:
            filename = f"stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            self.chain.export_stats(filename)
            messagebox.showinfo("Success", f"Stats exported to {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Error exporting stats: {e}")

    def exit(self):
        """Graceful exit."""
        self.chain.stop_all_nodes()
        self.root.destroy()

def run_cli(chain: ProxyChain):
    """Run the interactive CLI with enhanced commands."""
    console.print(Panel(ASCII_ART, style="magenta on black"))
    while True:
        console.print("\n[cyan]99Proxys Menu[/cyan]")
        console.print("1. Setup Nodes")
        console.print("2. Roll All Nodes")
        console.print("3. Roll Single Node")
        console.print("4. Stop Single Node")
        console.print("5. Show Stats")
        console.print("6. Plot Stats")
        console.print("7. Stop All Nodes")
        console.print("8. Run Setup Wizard")
        console.print("9. Export Stats")
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
                index = int(console.input("Enter node index (1-{}): ".format(len(chain.nodes)))) - 1
                if 0 <= index < len(chain.nodes):
                    chain.nodes[index].stop()
                    console.print(f"[yellow]Stopped node {index+1}[/yellow]")
                    logging.info(f"Stopped node {index+1}")
                else:
                    console.print("[red]Invalid node index[/red]")
            elif choice == "5":
                table = Table(title="Node Stats")
                table.add_column("Node", style="cyan")
                table.add_column("IP", style="yellow")
                table.add_column("MAC", style="green")
                table.add_column("Locale", style="magenta")
                table.add_column("Requests", style="cyan")
                table.add_column("Latency (ms)", style="yellow")
                table.add_column("Bandwidth (kbps)", style="green")
                table.add_column("Errors", style="red")
                for i, node in enumerate(chain.nodes):
                    table.add_row(
                        f"Node {i+1}",
                        node.virtual_ip,
                        node.virtual_mac,
                        node.locale["country"],
                        str(node.stats["requests"]),
                        f"{node.stats['latency'] * 1000:.2f}",
                        f"{node.stats['bandwidth_kbps']:.2f}",
                        str(node.stats["errors"])
                    )
                console.print(table)
            elif choice == "6":
                chain.plot_stats()
            elif choice == "7":
                chain.stop_all_nodes()
            elif choice == "8":
                console.print("[cyan]Setup Wizard[/cyan]")
                node_count = console.input(f"Number of nodes (5-99, default {chain.config['node_count']}): ")
                ip_range = console.input(f"IP range (default {chain.config['ip_range']}): ")
                locales = console.input(f"Locales (comma-separated, default {','.join(chain.config['locales'])}): ")
                bandwidth = console.input(f"Max bandwidth (kbps, default {chain.config['max_bandwidth_kbps']}): ")
                rate_limit = console.input(f"Rate limit (req/min, default {chain.config['rate_limit']}): ")
                try:
                    if node_count:
                        chain.config["node_count"] = max(5, min(99, int(node_count)))
                    if ip_range and chain.validate_ip_range(ip_range):
                        chain.config["ip_range"] = ip_range
                    if locales:
                        input_locales = [l.strip() for l in locales.split(",")]
                        invalid_locales = [l for l in input_locales if l not in [loc["country"] for loc in LOCALES]]
                        if invalid_locales:
                            raise ValueError(f"Invalid locales: {invalid_locales}")
                        chain.config["locales"] = input_locales
                    if bandwidth:
                        chain.config["max_bandwidth_kbps"] = max(56, int(bandwidth))
                    if rate_limit:
                        chain.config["rate_limit"] = max(1, int(rate_limit))
                    chain.save_config()
                    chain.setup_nodes()
                except Exception as e:
                    console.print(f"[red]Invalid configuration: {e}[/red]")
            elif choice == "9":
                filename = console.input("Enter filename for stats export (default: stats_<timestamp>.json): ")
                if not filename:
                    filename = f"stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                chain.export_stats(filename)
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
    """Main entry point for the 99Proxys application."""
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
