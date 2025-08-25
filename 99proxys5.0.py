#!/usr/bin/env python3
"""
# 99Proxys - A proprietary local virtual VPN network from the BG Gremlin Group
# Copyright (c) 2025 BG Gremlin Group. All rights reserved.
# This software is proprietary and confidential.
# Unauthorized copying, distribution, or modification
# is strictly prohibited without express permission from the BG Gremlin Group.
# Contact: https://github.com/BGGremlin-Group
# Purpose: Creates a private Tor-like network with 5–99 SOCKS5 proxy nodes
# supporting HTTPS, rolling IPs/MACs, and 99 locale simulations for enhanced anonymity.
# Version: 5.0.0
"""
import os
import sys
import socket
import threading
import random
import time
import json
import logging
import subprocess
import shutil
import webbrowser
import base64
from datetime import datetime, timedelta, timezone
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
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from timezonefinder import TimezoneFinder
import pytz
import pkg_resources
from packaging import version
import ipaddress
import queue
import unittest
from flask import Flask, request, redirect, flash, render_template_string, send_from_directory, jsonify
from flask_socketio import SocketIO
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, IntegerField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, NumberRange
import uuid
from scapy.all import get_if_list, get_if_addr, get_if_hwaddr
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, Text

# Initialize Rich console for CLI
console = Console()

# Define project directories
BASE_DIR = Path(__file__).parent
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

# Create directories if they don't exist
for directory in [CONFIG_DIR, LOG_DIR, DATA_DIR, ASSETS_DIR, CERT_DIR, TOR_DIR, HIDDEN_SERVICE_DIR, UPLOAD_DIR, SITES_DIR, DOCS_DIR]:
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

# Configuration
CONFIG = {
    "TOR_PATH": "tor",
    "TOR_DATA_DIR": str(TOR_DIR),
    "HIDDEN_SERVICE_BASE_DIR": str(HIDDEN_SERVICE_DIR),
    "PROXY_PORT": 8080,
    "WEB_PORT": 5000,
    "UPLOAD_FOLDER": str(UPLOAD_DIR),
    "SITES_FOLDER": str(SITES_DIR),
    "MIN_PORT": 1024,
    "MAX_PORT": 65535,
    "IP_RANGE": "192.168.0.0/16",
    "NODE_COUNT": 5,
    "LOCALES": ["United States", "Canada", "United Kingdom", "Germany", "France"],
    "MIN_SPEED_KBPS": 56,
    "MAX_BANDWIDTH_KBPS": 1000,
    "RATE_LIMIT": 100,
    "HEALTH_CHECK_INTERVAL": 30
}

# IoT manufacturer OUIs for realistic MAC addresses
IOT_OUIS = [
    "00:0D:3F",  # Samsung (Smart Fridge, Smart TV)
    "00:16:6C",  # Nest Labs (Thermostat)
    "00:24:E4",  # LG Electronics (Smart Appliances)
    "00:1E:C0",  # Philips Hue (Smart Lamps)
    "00:26:66",  # TP-Link (Smart Plugs, Routers)
    "00:1A:22",  # Belkin (Smart Switches)
    "00:17:88",  # LIFX (Smart Bulbs)
    "00:21:CC",  # Ecobee (Smart Thermostat)
    "00:24:81",  # Honeywell (Smart Thermostat)
    "00:1D:0F"   # D-Link (Smart Cameras, IoT Devices)
]

# Full list of 99 locales
LOCALES = [
    {"country": "United States", "timezone": "America/New_York", "lat": 40.7128, "lon": -74.0060, "ip_prefix": "192.168.1.0/24"},
    {"country": "Canada", "timezone": "America/Toronto", "lat": 43.6532, "lon": -79.3832, "ip_prefix": "192.168.2.0/24"},
    {"country": "United Kingdom", "timezone": "Europe/London", "lat": 51.5074, "lon": -0.1278, "ip_prefix": "192.168.3.0/24"},
    {"country": "Germany", "timezone": "Europe/Berlin", "lat": 52.5200, "lon": 13.4050, "ip_prefix": "192.168.4.0/24"},
    {"country": "France", "timezone": "Europe/Paris", "lat": 48.8566, "lon": 2.3522, "ip_prefix": "192.168.5.0/24"},
    {"country": "Japan", "timezone": "Asia/Tokyo", "lat": 35.6762, "lon": 139.6503, "ip_prefix": "192.168.6.0/24"},
    {"country": "Australia", "timezone": "Australia/Sydney", "lat": -33.8688, "lon": 151.2093, "ip_prefix": "192.168.7.0/24"},
    {"country": "Brazil", "timezone": "America/Sao_Paulo", "lat": -23.5505, "lon": -46.6333, "ip_prefix": "192.168.8.0/24"},
    {"country": "India", "timezone": "Asia/Kolkata", "lat": 28.6139, "lon": 77.2090, "ip_prefix": "192.168.9.0/24"},
    {"country": "China", "timezone": "Asia/Shanghai", "lat": 31.2304, "lon": 121.4737, "ip_prefix": "192.168.10.0/24"},
    {"country": "Russia", "timezone": "Europe/Moscow", "lat": 55.7558, "lon": 37.6173, "ip_prefix": "192.168.11.0/24"},
    {"country": "South Africa", "timezone": "Africa/Johannesburg", "lat": -26.2041, "lon": 28.0473, "ip_prefix": "192.168.12.0/24"},
    {"country": "Mexico", "timezone": "America/Mexico_City", "lat": 19.4326, "lon": -99.1332, "ip_prefix": "192.168.13.0/24"},
    {"country": "Italy", "timezone": "Europe/Rome", "lat": 41.9028, "lon": 12.4964, "ip_prefix": "192.168.14.0/24"},
    {"country": "Spain", "timezone": "Europe/Madrid", "lat": 40.4168, "lon": -3.7038, "ip_prefix": "192.168.15.0/24"},
    {"country": "South Korea", "timezone": "Asia/Seoul", "lat": 37.5665, "lon": 126.9780, "ip_prefix": "192.168.16.0/24"},
    {"country": "Argentina", "timezone": "America/Argentina/Buenos_Aires", "lat": -34.6037, "lon": -58.3816, "ip_prefix": "192.168.17.0/24"},
    {"country": "Nigeria", "timezone": "Africa/Lagos", "lat": 6.5244, "lon": 3.3792, "ip_prefix": "192.168.18.0/24"},
    {"country": "Indonesia", "timezone": "Asia/Jakarta", "lat": -6.2088, "lon": 106.8456, "ip_prefix": "192.168.19.0/24"},
    {"country": "Netherlands", "timezone": "Europe/Amsterdam", "lat": 52.3676, "lon": 4.9041, "ip_prefix": "192.168.20.0/24"},
    {"country": "Switzerland", "timezone": "Europe/Zurich", "lat": 47.3769, "lon": 8.5417, "ip_prefix": "192.168.21.0/24"},
    {"country": "Sweden", "timezone": "Europe/Stockholm", "lat": 59.3293, "lon": 18.0686, "ip_prefix": "192.168.22.0/24"},
    {"country": "Norway", "timezone": "Europe/Oslo", "lat": 59.9139, "lon": 10.7522, "ip_prefix": "192.168.23.0/24"},
    {"country": "New Zealand", "timezone": "Pacific/Auckland", "lat": -36.8485, "lon": 174.7633, "ip_prefix": "192.168.24.0/24"},
    {"country": "Singapore", "timezone": "Asia/Singapore", "lat": 1.3521, "lon": 103.8198, "ip_prefix": "192.168.25.0/24"},
    {"country": "Malaysia", "timezone": "Asia/Kuala_Lumpur", "lat": 3.1390, "lon": 101.6869, "ip_prefix": "192.168.26.0/24"},
    {"country": "Thailand", "timezone": "Asia/Bangkok", "lat": 13.7563, "lon": 100.5018, "ip_prefix": "192.168.27.0/24"},
    {"country": "Vietnam", "timezone": "Asia/Ho_Chi_Minh", "lat": 10.8231, "lon": 106.6297, "ip_prefix": "192.168.28.0/24"},
    {"country": "Philippines", "timezone": "Asia/Manila", "lat": 14.5995, "lon": 120.9842, "ip_prefix": "192.168.29.0/24"},
    {"country": "Turkey", "timezone": "Europe/Istanbul", "lat": 41.0082, "lon": 28.9784, "ip_prefix": "192.168.30.0/24"},
    {"country": "Egypt", "timezone": "Africa/Cairo", "lat": 30.0444, "lon": 31.2357, "ip_prefix": "192.168.31.0/24"},
    {"country": "Saudi Arabia", "timezone": "Asia/Riyadh", "lat": 24.7136, "lon": 46.6753, "ip_prefix": "192.168.32.0/24"},
    {"country": "United Arab Emirates", "timezone": "Asia/Dubai", "lat": 25.2048, "lon": 55.2708, "ip_prefix": "192.168.33.0/24"},
    {"country": "Israel", "timezone": "Asia/Jerusalem", "lat": 31.7683, "lon": 35.2137, "ip_prefix": "192.168.34.0/24"},
    {"country": "Chile", "timezone": "America/Santiago", "lat": -33.4489, "lon": -70.6693, "ip_prefix": "192.168.35.0/24"},
    {"country": "Colombia", "timezone": "America/Bogota", "lat": 4.7110, "lon": -74.0721, "ip_prefix": "192.168.36.0/24"},
    {"country": "Peru", "timezone": "America/Lima", "lat": -12.0464, "lon": -77.0428, "ip_prefix": "192.168.37.0/24"},
    {"country": "Venezuela", "timezone": "America/Caracas", "lat": 10.4806, "lon": -66.9036, "ip_prefix": "192.168.38.0/24"},
    {"country": "Poland", "timezone": "Europe/Warsaw", "lat": 52.2297, "lon": 21.0122, "ip_prefix": "192.168.39.0/24"},
    {"country": "Ukraine", "timezone": "Europe/Kiev", "lat": 50.4501, "lon": 30.5234, "ip_prefix": "192.168.40.0/24"},
    {"country": "Romania", "timezone": "Europe/Bucharest", "lat": 44.4268, "lon": 26.1025, "ip_prefix": "192.168.41.0/24"},
    {"country": "Greece", "timezone": "Europe/Athens", "lat": 37.9838, "lon": 23.7275, "ip_prefix": "192.168.42.0/24"},
    {"country": "Portugal", "timezone": "Europe/Lisbon", "lat": 38.7223, "lon": -9.1393, "ip_prefix": "192.168.43.0/24"},
    {"country": "Belgium", "timezone": "Europe/Brussels", "lat": 50.8503, "lon": 4.3517, "ip_prefix": "192.168.44.0/24"},
    {"country": "Austria", "timezone": "Europe/Vienna", "lat": 48.2082, "lon": 16.3738, "ip_prefix": "192.168.45.0/24"},
    {"country": "Denmark", "timezone": "Europe/Copenhagen", "lat": 55.6761, "lon": 12.5683, "ip_prefix": "192.168.46.0/24"},
    {"country": "Finland", "timezone": "Europe/Helsinki", "lat": 60.1699, "lon": 24.9384, "ip_prefix": "192.168.47.0/24"},
    {"country": "Ireland", "timezone": "Europe/Dublin", "lat": 53.3498, "lon": -6.2603, "ip_prefix": "192.168.48.0/24"},
    {"country": "Czech Republic", "timezone": "Europe/Prague", "lat": 50.0755, "lon": 14.4378, "ip_prefix": "192.168.49.0/24"},
    {"country": "Hungary", "timezone": "Europe/Budapest", "lat": 47.4979, "lon": 19.0402, "ip_prefix": "192.168.50.0/24"},
    {"country": "Slovakia", "timezone": "Europe/Bratislava", "lat": 48.1486, "lon": 17.1077, "ip_prefix": "192.168.51.0/24"},
    {"country": "Croatia", "timezone": "Europe/Zagreb", "lat": 45.8150, "lon": 15.9819, "ip_prefix": "192.168.52.0/24"},
    {"country": "Serbia", "timezone": "Europe/Belgrade", "lat": 44.7866, "lon": 20.4489, "ip_prefix": "192.168.53.0/24"},
    {"country": "Bulgaria", "timezone": "Europe/Sofia", "lat": 42.6977, "lon": 23.3219, "ip_prefix": "192.168.54.0/24"},
    {"country": "Albania", "timezone": "Europe/Tirane", "lat": 41.3275, "lon": 19.8187, "ip_prefix": "192.168.55.0/24"},
    {"country": "Bosnia and Herzegovina", "timezone": "Europe/Sarajevo", "lat": 43.8486, "lon": 18.3564, "ip_prefix": "192.168.56.0/24"},
    {"country": "Montenegro", "timezone": "Europe/Podgorica", "lat": 42.4411, "lon": 19.2636, "ip_prefix": "192.168.57.0/24"},
    {"country": "North Macedonia", "timezone": "Europe/Skopje", "lat": 41.9973, "lon": 21.4280, "ip_prefix": "192.168.58.0/24"},
    {"country": "Slovenia", "timezone": "Europe/Ljubljana", "lat": 46.0569, "lon": 14.5058, "ip_prefix": "192.168.59.0/24"},
    {"country": "Latvia", "timezone": "Europe/Riga", "lat": 56.9496, "lon": 24.1052, "ip_prefix": "192.168.60.0/24"},
    {"country": "Lithuania", "timezone": "Europe/Vilnius", "lat": 54.6872, "lon": 25.2797, "ip_prefix": "192.168.61.0/24"},
    {"country": "Estonia", "timezone": "Europe/Tallinn", "lat": 59.4370, "lon": 24.7536, "ip_prefix": "192.168.62.0/24"},
    {"country": "Iceland", "timezone": "Atlantic/Reykjavik", "lat": 64.1466, "lon": -21.9426, "ip_prefix": "192.168.63.0/24"},
    {"country": "Malta", "timezone": "Europe/Malta", "lat": 35.8989, "lon": 14.5146, "ip_prefix": "192.168.64.0/24"},
    {"country": "Cyprus", "timezone": "Asia/Nicosia", "lat": 35.1856, "lon": 33.3823, "ip_prefix": "192.168.65.0/24"},
    {"country": "Morocco", "timezone": "Africa/Casablanca", "lat": 33.9716, "lon": -6.8498, "ip_prefix": "192.168.66.0/24"},
    {"country": "Algeria", "timezone": "Africa/Algiers", "lat": 36.7372, "lon": 3.0870, "ip_prefix": "192.168.67.0/24"},
    {"country": "Tunisia", "timezone": "Africa/Tunis", "lat": 36.8065, "lon": 10.1815, "ip_prefix": "192.168.68.0/24"},
    {"country": "Kenya", "timezone": "Africa/Nairobi", "lat": -1.2921, "lon": 36.8219, "ip_prefix": "192.168.69.0/24"},
    {"country": "Ethiopia", "timezone": "Africa/Addis_Ababa", "lat": 9.0240, "lon": 38.7469, "ip_prefix": "192.168.70.0/24"},
    {"country": "Ghana", "timezone": "Africa/Accra", "lat": 5.5600, "lon": -0.2050, "ip_prefix": "192.168.71.0/24"},
    {"country": "Angola", "timezone": "Africa/Luanda", "lat": -8.8390, "lon": 13.2343, "ip_prefix": "192.168.73.0/24"},
    {"country": "Cameroon", "timezone": "Africa/Douala", "lat": 3.8480, "lon": 11.5021, "ip_prefix": "192.168.74.0/24"},
    {"country": "Senegal", "timezone": "Africa/Dakar", "lat": 14.7167, "lon": -17.4677, "ip_prefix": "192.168.75.0/24"},
    {"country": "Zambia", "timezone": "Africa/Lusaka", "lat": -15.3875, "lon": 28.3228, "ip_prefix": "192.168.76.0/24"},
    {"country": "Zimbabwe", "timezone": "Africa/Harare", "lat": -17.8252, "lon": 31.0335, "ip_prefix": "192.168.77.0/24"},
    {"country": "Botswana", "timezone": "Africa/Gaborone", "lat": -24.6282, "lon": 25.9231, "ip_prefix": "192.168.78.0/24"},
    {"country": "Qatar", "timezone": "Asia/Qatar", "lat": 25.2769, "lon": 51.5200, "ip_prefix": "192.168.79.0/24"},
    {"country": "Kuwait", "timezone": "Asia/Kuwait", "lat": 29.3759, "lon": 47.9774, "ip_prefix": "192.168.80.0/24"},
    {"country": "Bahrain", "timezone": "Asia/Bahrain", "lat": 26.0667, "lon": 50.5577, "ip_prefix": "192.168.81.0/24"},
    {"country": "Oman", "timezone": "Asia/Muscat", "lat": 23.5859, "lon": 58.4059, "ip_prefix": "192.168.82.0/24"},
    {"country": "Jordan", "timezone": "Asia/Amman", "lat": 31.9566, "lon": 35.9457, "ip_prefix": "192.168.83.0/24"},
    {"country": "Lebanon", "timezone": "Asia/Beirut", "lat": 33.8938, "lon": 35.5018, "ip_prefix": "192.168.84.0/24"},
    {"country": "Pakistan", "timezone": "Asia/Karachi", "lat": 24.8607, "lon": 67.0011, "ip_prefix": "192.168.85.0/24"},
    {"country": "Bangladesh", "timezone": "Asia/Dhaka", "lat": 23.8103, "lon": 90.4125, "ip_prefix": "192.168.86.0/24"},
    {"country": "Sri Lanka", "timezone": "Asia/Colombo", "lat": 6.9271, "lon": 79.8612, "ip_prefix": "192.168.87.0/24"},
    {"country": "Nepal", "timezone": "Asia/Kathmandu", "lat": 27.7172, "lon": 85.3240, "ip_prefix": "192.168.88.0/24"},
    {"country": "Bhutan", "timezone": "Asia/Thimphu", "lat": 27.5142, "lon": 89.6349, "ip_prefix": "192.168.89.0/24"},
    {"country": "Mongolia", "timezone": "Asia/Ulaanbaatar", "lat": 47.8864, "lon": 106.9057, "ip_prefix": "192.168.90.0/24"},
    {"country": "Kazakhstan", "timezone": "Asia/Almaty", "lat": 43.2220, "lon": 76.8512, "ip_prefix": "192.168.91.0/24"},
    {"country": "Uzbekistan", "timezone": "Asia/Tashkent", "lat": 41.2995, "lon": 69.2401, "ip_prefix": "192.168.92.0/24"},
    {"country": "Georgia", "timezone": "Asia/Tbilisi", "lat": 41.7151, "lon": 44.8271, "ip_prefix": "192.168.93.0/24"},
    {"country": "Armenia", "timezone": "Asia/Yerevan", "lat": 40.1872, "lon": 44.5152, "ip_prefix": "192.168.94.0/24"},
    {"country": "Azerbaijan", "timezone": "Asia/Baku", "lat": 40.4093, "lon": 49.8671, "ip_prefix": "192.168.95.0/24"},
    {"country": "Ecuador", "timezone": "America/Guayaquil", "lat": -2.1894, "lon": -79.8891, "ip_prefix": "192.168.96.0/24"},
    {"country": "Bolivia", "timezone": "America/La_Paz", "lat": -16.4897, "lon": -68.1193, "ip_prefix": "192.168.97.0/24"},
    {"country": "Paraguay", "timezone": "America/Asuncion", "lat": -25.2637, "lon": -57.5759, "ip_prefix": "192.168.98.0/24"},
    {"country": "Fiji", "timezone": "Pacific/Fiji", "lat": -18.1248, "lon": 178.4501, "ip_prefix": "192.168.99.0/24"}
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
    "psutil": "5.9.8",
    "requests": "2.31.0",
    "cryptography": "42.0.5",
    "timezonefinder": "6.1.9",
    "matplotlib": "3.8.3",
    "flask": "2.3.3",
    "flask-socketio": "5.3.6",
    "flask-sqlalchemy": "3.0.5",
    "werkzeug": "3.0.1",
    "flask-wtf": "1.2.1",
    "pytz": "2023.3"
}

install_dependencies()
generate_self_signed_cert()

flask_app = Flask(__name__)
flask_app.config['SECRET_KEY'] = str(uuid.uuid4())
flask_app.config['UPLOAD_FOLDER'] = CONFIG["UPLOAD_FOLDER"]
flask_app.config['SITES_FOLDER'] = CONFIG["SITES_FOLDER"]
flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sites.db'
flask_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
flask_app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_size': 10, 'max_overflow': 20}
csrf = CSRFProtect(flask_app)
socketio = SocketIO(flask_app)
db = SQLAlchemy(flask_app)

# Review form for CSRF protection
class ReviewForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    rating = IntegerField('Rating', validators=[DataRequired(), NumberRange(min=1, max=5)])
    comment = TextAreaField('Comment', validators=[DataRequired()])
    submit = SubmitField('Submit Review')

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
            "timestamp": self.timestamp
        }

with flask_app.app_context():
    db.create_all()
    logging.info("Database tables created.")

class ProxyNode:
    """
    Represents a single proxy node in the chain with enhanced features.

    Attributes:
        host (str): Node host address.
        port (int): Node port.
        locale (Dict): Locale information (country, timezone, etc.).
        virtual_ip (str): Virtual IP address.
        virtual_mac (str): Virtual MAC address.
        server (socketserver.ThreadingTCPServer): TCP server instance.
        active (bool): Node status.
        stats (Dict): Performance statistics.
        fernet (Fernet): Symmetric encryption instance.
        rsa_private_key (RSAPrivateKey): RSA private key.
        rsa_public_key (RSAPublicKey): RSA public key.
        rate_limit (int): Maximum requests per minute.
        request_timestamps (Queue): Timestamps of recent requests.
        bandwidth_limit_kbps (float): Bandwidth limit in kbps.
        bucket_tokens (float): Current tokens in bandwidth bucket.
        bucket_capacity (float): Maximum tokens in bandwidth bucket.
        last_refill (float): Last bucket refill time.
        lock (Lock): Threading lock for synchronization.
        health_check_thread (Thread): Thread for health checks.
        running (Event): Event to control health check loop.
        timezone (tzinfo): Timezone for locale-specific timestamps.
        health_check_interval (int): Interval for health checks in seconds.
    """
    def __init__(self, host: str, port: int, locale: Dict, virtual_ip: str, virtual_mac: str, health_check_interval: int = 30):
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
        key_file = CERT_DIR / f"fernet_{port}.key"
        try:
            if key_file.exists():
                with open(key_file, "rb") as f:
                    self.fernet = Fernet(f.read())
            else:
                key = Fernet.generate_key()
                self.fernet = Fernet(key)
                with open(key_file, "wb") as f:
                    f.write(key)
        except Exception as e:
            console.print(f"[red]Error initializing Fernet key for node {port}: {e}[/red]")
            logging.error(f"Fernet key initialization failed: {e}")
            raise
        self.rsa_private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.rsa_public_key = self.rsa_private_key.public_key()
        self.rate_limit = CONFIG["RATE_LIMIT"]
        self.request_timestamps = queue.Queue()
        self.bandwidth_limit_kbps = CONFIG["MAX_BANDWIDTH_KBPS"]
        self.bucket_tokens = self.bandwidth_limit_kbps * 1000 / 8  # Bytes per second
        self.bucket_capacity = self.bucket_tokens
        self.last_refill = time.time()
        self.lock = threading.Lock()
        self.health_check_thread = None
        self.running = threading.Event()
        self.running.set()
        self.timezone = pytz.timezone(locale["timezone"])
        self.health_check_interval = health_check_interval
        try:
            self.assign_virtual_ip()
        except Exception as e:
            console.print(f"[red]Failed to assign virtual IP for node {port}: {e}[/red]")
            logging.error(f"Virtual IP assignment failed: {e}")
            raise

    def assign_virtual_ip(self, interface: str = "lo"):
        """
        Assign a virtual IP to a network interface using scapy.

        Args:
            interface (str): Network interface name (default: "lo").

        Raises:
            ValueError: If the interface is invalid.
            RuntimeError: If IP assignment fails or root privileges are missing.
        """
        try:
            if os.geteuid() != 0:
                raise RuntimeError("Root privileges required for virtual IP assignment. Run with sudo or configure setcap (e.g., 'sudo setcap cap_net_admin=eip $(which python3)').")
            if interface not in get_if_list():
                raise ValueError(f"Interface {interface} not found")
            subprocess.run(['ip', 'addr', 'add', f"{self.virtual_ip}/24", 'dev', interface], check=True)
            logging.info(f"Assigned virtual IP {self.virtual_ip} to {interface}")
        except Exception as e:
            logging.error(f"Failed to assign virtual IP {self.virtual_ip}: {e}")
            raise RuntimeError(f"Virtual IP assignment failed: {e}")

    def encrypt_data(self, data: bytes, next_node: Optional['ProxyNode'] = None) -> bytes:
        """
        Encrypt data using Fernet and RSA.

        Args:
            data (bytes): Data to encrypt.
            next_node (Optional[ProxyNode]): Next node in the chain for RSA encryption.

        Returns:
            bytes: Encrypted data.

        Raises:
            Exception: If encryption fails.
        """
        try:
            encrypted_data = self.fernet.encrypt(data)
            if next_node:
                full_raw_key = base64.urlsafe_b64decode(self.fernet._encryption_key + self.fernet._signing_key)
                encrypted_key = next_node.rsa_public_key.encrypt(
                    full_raw_key,
                    padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
                )
                return encrypted_key + b"||" + encrypted_data
            return encrypted_data
        except Exception as e:
            logging.error(f"Encryption error in node {self.port}: {e}")
            self.stats["errors"] += 1
            return data

    def decrypt_data(self, data: bytes, prev_node: Optional['ProxyNode'] = None) -> bytes:
        """
        Decrypt data using Fernet and RSA.

        Args:
            data (bytes): Data to decrypt.
            prev_node (Optional[ProxyNode]): Previous node in the chain for RSA decryption.

        Returns:
            bytes: Decrypted data.

        Raises:
            Exception: If decryption fails.
        """
        try:
            if prev_node and b"||" in data:
                encrypted_key, encrypted_data = data.split(b"||", 1)
                fernet_key = self.rsa_private_key.decrypt(
                    encrypted_key,
                    padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
                )
                encoded_key = base64.urlsafe_b64encode(fernet_key)
                temp_fernet = Fernet(encoded_key)
                return temp_fernet.decrypt(encrypted_data)
            return self.fernet.decrypt(data)
        except Exception as e:
            logging.error(f"Decryption error in node {self.port}: {e}")
            self.stats["errors"] += 1
            return data

    def check_rate_limit(self) -> bool:
        """
        Check if the node is within the rate limit.

        Returns:
            bool: True if within rate limit, False otherwise.
        """
        with self.lock:
            current_time = time.time()
            while not self.request_timestamps.empty() and self.request_timestamps.qsize() > self.rate_limit:
                self.request_timestamps.get()
            while not self.request_timestamps.empty():
                if current_time - self.request_timestamps.queue[0] > 60:
                    self.request_timestamps.get()
                else:
                    break
            self.request_timestamps.put(current_time)
            return self.request_timestamps.qsize() <= self.rate_limit

    def refill_bucket(self):
        """Refill token bucket based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill
        self.bucket_tokens = min(self.bucket_capacity, self.bucket_tokens + elapsed * (self.bandwidth_limit_kbps * 1000 / 8))
        self.last_refill = now

    def throttle_bandwidth(self, data_size: int) -> float:
        """
        Simulate bandwidth throttling using token bucket.

        Args:
            data_size (int): Size of data to transmit in bytes.

        Returns:
            float: Time taken for throttling.
        """
        with self.lock:
            self.refill_bucket()
            if data_size > self.bucket_tokens:
                sleep_time = (data_size - self.bucket_tokens) / (self.bandwidth_limit_kbps * 1000 / 8)
                time.sleep(sleep_time)
                self.bucket_tokens = 0
            else:
                self.bucket_tokens -= data_size
            return time.time() - self.last_refill

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
            time.sleep(self.health_check_interval)

    def get_local_time(self) -> str:
        """
        Get the current time in the node's locale.

        Returns:
            str: Formatted local time.
        """
        return datetime.now(self.timezone).strftime("%Y-%m-%d %H:%M:%S")

    def start(self, next_node: Optional['ProxyNode'] = None):
        """
        Start the proxy node as a SOCKS5 server with SSL/TLS.

        Args:
            next_node (Optional[ProxyNode]): Next node in the chain.

        Raises:
            Exception: If server startup fails.
        """
        try:
            class SOCKS5Handler(socketserver.BaseRequestHandler):
                def handle(self):
                    start_time = time.time()
                    with self.server.node.lock:
                        self.server.node.stats["requests"] += 1
                        self.server.node.stats["connection_time"] = time.time()
                    if not self.server.node.check_rate_limit():
                        self.request.sendall(b"\x05\x08\x00\x01" + b"\x00" * 4 + b"\x00\x00")
                        logging.warning(f"Node {self.server.node.port} rate limit exceeded")
                        return
                    try:
                        data = self.request.recv(2)
                        if data != b"\x05\x01\x00":
                            self.request.sendall(b"\x05\xff")
                            return
                        self.request.sendall(b"\x05\x00")
                        data = self.request.recv(4)
                        if len(data) < 4:
                            return
                        cmd, _, atyp = data[1:4]
                        if atyp == 1:
                            addr = self.request.recv(4)
                            ip = socket.inet_ntoa(addr)
                            port = int.from_bytes(self.request.recv(2), 'big')
                        else:
                            self.request.sendall(b"\x05\x01\x00\x01" + b"\x00" * 4 + b"\x00\x00")
                            return
                        if cmd == 1:
                            if next_node:
                                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                                    try:
                                        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
                                        context.check_hostname = False
                                        context.verify_mode = ssl.CERT_NONE
                                        sock = context.wrap_socket(sock, server_hostname=next_node.host)
                                        sock.connect((next_node.host, next_node.port))
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
                            self.request.sendall(b"\x05\x07\x00\x01" + b"\x00" * 4 + b"\x00\x00")
                        with self.server.node.lock:
                            self.server.node.stats["latency"] = time.time() - start_time
                            self.server.node.stats["connection_time"] = time.time() - self.server.node.stats["connection_time"]
                    except Exception as e:
                        logging.error(f"Node {self.server.node.port} error: {e}")
                        self.server.node.stats["errors"] += 1
                        self.request.sendall(b"\x05\x01\x00\x01" + b"\x00" * 4 + b"\x00\x00")

                def tunnel(self, client_sock, target_sock, next_node: Optional['ProxyNode']):
                    """
                    Tunnel data between client and target sockets.

                    Args:
                        client_sock (socket): Client socket.
                        target_sock (socket): Target socket.
                        next_node (Optional[ProxyNode]): Next node in the chain.
                    """
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
                    except socket.timeout:
                        logging.warning(f"Timeout in tunnel for node {self.server.node.port}")
                        self.server.node.stats["errors"] += 1
                    except ssl.SSLError as e:
                        logging.error(f"SSL error in tunnel for node {self.server.node.port}: {e}")
                        self.server.node.stats["errors"] += 1
                    except Exception as e:
                        logging.error(f"Tunnel error in node {self.server.node.port}: {e}")
                        self.server.node.stats["errors"] += 1
                    finally:
                        try:
                            client_sock.close()
                            target_sock.close()
                        except Exception as e:
                            logging.error(f"Error closing sockets in node {self.server.node.port}: {e}")

            self.server = socketserver.ThreadingTCPServer((self.host, self.port), SOCKS5Handler)
            self.server.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            context.load_cert_chain(certfile=CERT_FILE, keyfile=KEY_FILE)
            self.server.socket = context.wrap_socket(self.server.socket, server_side=True)
            self.server.node = self
            self.active = True
            threading.Thread(target=self.server.serve_forever, daemon=True).start()
            self.health_check_thread = threading.Thread(target=self.health_check, daemon=True)
            self.health_check_thread.start()
            console.print(f"[green]Started node on {self.host}:{self.port} ({self.locale['country']}, MAC: {self.virtual_mac})[/green]")
            logging.info(f"Node started on {self.host}:{self.port}, MAC: {self.virtual_mac} at {self.get_local_time()}")
        except Exception as e:
            console.print(f"[red]Failed to start node on {self.host}:{self.port}: {e}[/red]")
            logging.error(f"Node start failed on {self.host}:{self.port}: {e}")
            self.active = False
            self.stats["errors"] += 1

    def stop(self):
        """
        Stop the proxy node gracefully.

        Raises:
            Exception: If server shutdown fails.
        """
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
                logging.info(f"Node stopped on {self.host}:{self.port} at {self.get_local_time()}")

    def restart(self):
        """Restart the proxy node."""
        self.stop()
        time.sleep(1)
        next_node = None
        if hasattr(self, 'nodes') and self in self.nodes:
            index = self.nodes.index(self)
            next_node = self.nodes[index + 1] if index < len(self.nodes) - 1 else None
        self.start(next_node)

class ProxyChain:
    """
    Manages the chain of proxy nodes, Tor hidden services, and website creation.

    Attributes:
        nodes (List[ProxyNode]): List of proxy nodes.
        websites (List[Dict]): List of websites with metadata.
        config (Dict): Configuration settings.
        tf (TimezoneFinder): Timezone finder instance.
        used_ips (set): Set of used virtual IPs.
        used_ports (set): Set of used ports.
        tor_processes (Dict): Dictionary of Tor processes.
        web_servers (Dict): Dictionary of Flask web servers.
    """
    def __init__(self):
        self.nodes: List[ProxyNode] = []
        self.websites: List[Dict] = []
        self.config = self.load_config()
        self.tf = TimezoneFinder()
        self.used_ips = set()
        self.used_ports = set()
        self.tor_processes = {}
        self.web_servers = {}

    def validate_ip_range(self, ip_range: str) -> bool:
        """
        Validate the IP range format.

        Args:
            ip_range (str): IP range in CIDR notation.

        Returns:
            bool: True if valid, False otherwise.
        """
        try:
            network = ipaddress.IPv4Network(ip_range, strict=False)
            available_ips = len(list(network.hosts()))
            if available_ips < self.config["node_count"]:
                console.print(f"[red]IP range {ip_range} has insufficient IPs for {self.config['node_count']} nodes[/red]")
                logging.error(f"Insufficient IPs in range {ip_range}")
                return False
            return True
        except ValueError as e:
            console.print(f"[red]Invalid IP range: {e}[/red]")
            logging.error(f"Invalid IP range: {e}")
            return False

    def validate_port_range(self, min_port: int, max_port: int) -> bool:
        """
        Validate the port range.

        Args:
            min_port (int): Minimum port number.
            max_port (int): Maximum port number.

        Returns:
            bool: True if valid, False otherwise.
        """
        if not (1 <= min_port <= max_port <= 65535):
            console.print(f"[red]Invalid port range: {min_port}-{max_port}[/red]")
            logging.error(f"Invalid port range: {min_port}-{max_port}")
            return False
        available_ports = max_port - min_port + 1
        if available_ports < self.config["node_count"] + len(self.websites):
            console.print(f"[red]Insufficient ports for {self.config['node_count']} nodes and {len(self.websites)} websites[/red]")
            logging.error(f"Insufficient ports: {available_ports} available, {self.config['node_count'] + len(self.websites)} needed")
            return False
        return True

    def load_config(self) -> Dict:
        """
        Load or create configuration file.

        Returns:
            Dict: Configuration settings.

        Raises:
            Exception: If config file operations fail.
        """
        default_config = {
            "node_count": CONFIG["NODE_COUNT"],
            "ip_range": CONFIG["IP_RANGE"],
            "locales": [locale["country"] for locale in LOCALES],
            "min_port": CONFIG["MIN_PORT"],
            "max_port": CONFIG["MAX_PORT"],
            "min_speed_kbps": CONFIG["MIN_SPEED_KBPS"],
            "max_bandwidth_kbps": CONFIG["MAX_BANDWIDTH_KBPS"],
            "rate_limit": CONFIG["RATE_LIMIT"],
            "health_check_interval": CONFIG["HEALTH_CHECK_INTERVAL"]
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
                if not (5 <= config.get("node_count", default_config["node_count"]) <= 99):
                    config["node_count"] = default_config["node_count"]
                if not (10 <= config.get("min_speed_kbps", default_config["min_speed_kbps"]) <= 1000):
                    config["min_speed_kbps"] = default_config["min_speed_kbps"]
                if not (100 <= config.get("max_bandwidth_kbps", default_config["max_bandwidth_kbps"]) <= 10000):
                    config["max_bandwidth_kbps"] = default_config["max_bandwidth_kbps"]
                if not (1 <= config.get("rate_limit", default_config["rate_limit"]) <= 1000):
                    config["rate_limit"] = default_config["rate_limit"]
                if not (10 <= config.get("health_check_interval", default_config["health_check_interval"]) <= 300):
                    config["health_check_interval"] = default_config["health_check_interval"]
                return config
            except Exception as e:
                console.print(f"[red]Error loading config: {e}, using defaults[/red]")
                logging.error(f"Config load failed: {e}")
        with open(CONFIG_FILE, "w") as f:
            json.dump(default_config, f, indent=4)
        return default_config

    def save_config(self):
        """
        Save configuration to file.

        Raises:
            Exception: If config file write fails.
        """
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(self.config, f, indent=4)
            logging.info("Configuration saved")
        except Exception as e:
            console.print(f"[red]Error saving config: {e}[/red]")
            logging.error(f"Config save failed: {e}")

    def get_available_port(self) -> int:
        """
        Find an available port.

        Returns:
            int: Available port number.

        Raises:
            RuntimeError: If no ports are available after max attempts.
        """
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
        """
        Generate a virtual IP within the locale's IP range.

        Args:
            locale (Dict): Locale information with ip_prefix.

        Returns:
            str: Virtual IP address.

        Raises:
            ValueError: If no available IPs are found.
        """
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
        """
        Generate a random MAC address resembling an IoT device.

        Returns:
            str: MAC address.
        """
        oui = random.choice(IOT_OUIS)
        vendor_bytes = ''.join(random.choices('0123456789ABCDEF', k=6))
        mac = f"{oui}:{vendor_bytes[0:2]}:{vendor_bytes[2:4]}:{vendor_bytes[4:6]}"
        return mac.lower()

    def initialize_nodes(self):
        """
        Initialize proxy nodes with locales.

        Raises:
            SystemExit: If node initialization fails.
        """
        try:
            if not self.validate_port_range(self.config["min_port"], self.config["max_port"]):
                raise ValueError("Invalid port range or insufficient ports")
            if not self.validate_ip_range(self.config["ip_range"]):
                raise ValueError("Invalid IP range or insufficient IPs")
            for _ in range(self.config["node_count"]):
                locale = random.choice(LOCALES)
                port = self.get_available_port()
                virtual_ip = self.generate_virtual_ip(locale)
                virtual_mac = self.generate_virtual_mac()
                node = ProxyNode("127.0.0.1", port, locale, virtual_ip, virtual_mac, self.config["health_check_interval"])
                node.nodes = self.nodes
                self.nodes.append(node)
            for i in range(len(self.nodes) - 1):
                self.nodes[i].start(next_node=self.nodes[i + 1])
            self.nodes[-1].start()
            console.print(f"[green]Initialized {len(self.nodes)} proxy nodes.[/green]")
            logging.info(f"Initialized {len(self.nodes)} proxy nodes")
        except Exception as e:
            console.print(f"[red]Error initializing nodes: {e}[/red]")
            logging.error(f"Node initialization failed: {e}")
            sys.exit(1)

    def create_hidden_service(self, website_name: str, port: int) -> str:
        """
        Create a Tor hidden service for a website.

        Args:
            website_name (str): Name of the website.
            port (int): Port for the hidden service.

        Returns:
            str: Onion address if successful, empty string otherwise.

        Raises:
            RuntimeError: If Tor executable is missing or process fails.
        """
        try:
            if not shutil.which(CONFIG["TOR_PATH"]):
                raise RuntimeError("Tor executable not found")
            hidden_service_dir = HIDDEN_SERVICE_DIR / website_name
            hidden_service_dir.mkdir(exist_ok=True)
            torrc_content = f"""
HiddenServiceDir {hidden_service_dir}
HiddenServicePort 80 127.0.0.1:{port}
"""
            torrc_file = hidden_service_dir / "torrc"
            with open(torrc_file, "w") as f:
                f.write(torrc_content)
            tor_cmd = [
                CONFIG["TOR_PATH"],
                "-f", str(torrc_file),
                "--DataDirectory", str(TOR_DIR / website_name),
                "--quiet"
            ]
            process = subprocess.Popen(tor_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            time.sleep(3)
            if process.poll() is not None:
                stdout, stderr = process.communicate()
                raise RuntimeError(f"Tor process failed: {stderr.decode()}")
            self.tor_processes[website_name] = process
            hostname_file = hidden_service_dir / "hostname"
            if hostname_file.exists():
                with open(hostname_file, "r") as f:
                    onion_address = f.read().strip()
                console.print(f"[green]Created hidden service for {website_name}: {onion_address}[/green]")
                logging.info(f"Created hidden service for {website_name}: {onion_address}")
                return onion_address
            else:
                raise RuntimeError("Failed to create hidden service: hostname file not found")
        except Exception as e:
            console.print(f"[red]Error creating hidden service for {website_name}: {e}[/red]")
            logging.error(f"Hidden service creation failed for {website_name}: {e}")
            return ""

    def create_website(self, name: str, pages: List[Dict]):
        """
        Create a multi-page website with chatroom and WYSIWYG assets.

        Args:
            name (str): Website name.
            pages (List[Dict]): List of page dictionaries with name, html_content, css_content, js_content.

        Raises:
            ValueError: If name is invalid or pages are empty.
            Exception: If website creation fails.
        """
        try:
            if not name or not pages:
                raise ValueError("Website name and pages cannot be empty")
            name = secure_filename(name)
            site_dir = SITES_DIR / name
            site_dir.mkdir(exist_ok=True)
            port = self.get_available_port()
            onion_address = self.create_hidden_service(name, port)
            with flask_app.app_context():
                website = Website(
                    name=name,
                    onion_address=onion_address,
                    port=port,
                    timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )
                db.session.add(website)
                db.session.commit()
                for page in pages:
                    page_name = secure_filename(page["name"])
                    page_path = site_dir / page_name
                    page_path.mkdir(exist_ok=True)
                    html_file = page_path / "index.html"
                    css_file = page_path / "styles.css"
                    js_file = page_path / "script.js"
                    with open(html_file, "w") as f:
                        f.write(page["html_content"])
                    if page.get("css_content"):
                        with open(css_file, "w") as f:
                            f.write(page["css_content"])
                    if page.get("js_content"):
                        with open(js_file, "w") as f:
                            f.write(page["js_content"])
                    page_entry = Page(
                        website_id=website.id,
                        name=page_name,
                        html_content=page["html_content"],
                        css_content=page.get("css_content", ""),
                        js_content=page.get("js_content", ""),
                        path=str(page_path.relative_to(SITES_DIR))
                    )
                    db.session.add(page_entry)
                db.session.commit()
            self.start_web_server(name, port, site_dir)
            self.websites.append({"name": name, "port": port, "onion_address": onion_address, "site_dir": site_dir})
            console.print(f"[green]Website '{name}' created with {len(pages)} pages on port {port} ({onion_address})[/green]")
            logging.info(f"Website '{name}' created with {len(pages)} pages on port {port}")
        except Exception as e:
            console.print(f"[red]Error creating website '{name}': {e}[/red]")
            logging.error(f"Website creation failed for {name}: {e}")

    def start_web_server(self, website_name: str, port: int, site_dir: Path):
        """
        Start a Flask web server for the website with chatroom and reviews.

        Args:
            website_name (str): Name of the website.
            port (int): Port for the web server.
            site_dir (Path): Directory containing website files.

        Raises:
            Exception: If web server startup fails.
        """
        def create_app():
            app = Flask(website_name, template_folder=str(site_dir), static_folder=str(site_dir))
            app.config['SECRET_KEY'] = str(uuid.uuid4())
            socketio_instance = SocketIO(app)

            @app.route('/')
            @app.route('/<path:path>')
            def serve_page(path="index.html"):
                try:
                    page_path = (site_dir / path).resolve()
                    if not page_path.is_file() or not str(page_path).startswith(str(site_dir)):
                        return "Page not found", 404
                    return send_from_directory(str(site_dir), path)
                except Exception as e:
                    logging.error(f"Error serving page {path} for {website_name}: {e}")
                    return "Page not found", 404

            @app.route('/chat')
            def chat():
                try:
                    return render_template_string(CHAT_TEMPLATE, website_name=website_name)
                except Exception as e:
                    logging.error(f"Error rendering chat for {website_name}: {e}")
                    return "Error loading chat", 500

            @app.route('/reviews', methods=['GET', 'POST'])
            def reviews():
                try:
                    with flask_app.app_context():
                        website = Website.query.filter_by(name=website_name).first()
                        if not website:
                            return "Website not found", 404
                        form = ReviewForm()
                        if form.validate_on_submit():
                            review = Review(
                                website_id=website.id,
                                name=form.name.data,
                                rating=form.rating.data,
                                comment=form.comment.data,
                                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            )
                            db.session.add(review)
                            db.session.commit()
                            flash('Review submitted successfully!', 'success')
                            return redirect(f'/reviews')
                        reviews = Review.query.filter_by(website_id=website.id).all()
                    return render_template_string(REVIEW_TEMPLATE, website_name=website_name, reviews=reviews, form=form)
                except Exception as e:
                    logging.error(f"Error rendering reviews for {website_name}: {e}")
                    return "Error loading reviews", 500

            @socketio_instance.on('message')
            def handle_message(data):
                try:
                    with flask_app.app_context():
                        msg = ChatMessage(
                            website_id=Website.query.filter_by(name=website_name).first().id,
                            username=secure_filename(data['username']),
                            message=data['message'],
                            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        )
                        db.session.add(msg)
                        db.session.commit()
                        socketio_instance.emit('message', msg.as_dict(), broadcast=True)
                except Exception as e:
                    logging.error(f"Error handling chat message for {website_name}: {e}")

            return app, socketio_instance

        try:
            app, socketio_instance = create_app()
            self.web_servers[website_name] = (app, socketio_instance, port)
            threading.Thread(
                target=lambda: socketio_instance.run(app, host="127.0.0.1", port=port, debug=False, use_reloader=False),
                daemon=True
            ).start()
            logging.info(f"Web server started for {website_name} on port {port}")
        except Exception as e:
            console.print(f"[red]Error starting web server for {website_name}: {e}[/red]")
            logging.error(f"Web server start failed for {website_name}: {e}")

    def import_assets(self, website_name: str, html_file: str = None, css_file: str = None, js_file: str = None) -> Dict:
        """
        Import HTML, CSS, and JavaScript files for a website page.

        Args:
            website_name (str): Name of the website.
            html_file (str, optional): Path to HTML file.
            css_file (str, optional): Path to CSS file.
            js_file (str, optional): Path to JavaScript file.

        Returns:
            Dict: Imported page details.

        Raises:
            ValueError: If website does not exist.
            Exception: If asset import fails.
        """
        try:
            website_name = secure_filename(website_name)
            site_dir = SITES_DIR / website_name
            if not site_dir.exists():
                raise ValueError(f"Website '{website_name}' does not exist")
            page_name = f"page_{len(list(site_dir.iterdir())) + 1}"
            page_path = site_dir / page_name
            page_path.mkdir(exist_ok=True)
            
            html_content = "<html><body><h1>New Page</h1></body></html>"
            css_content = ""
            js_content = ""
            
            if html_file and os.path.exists(html_file):
                with open(html_file, "r") as f:
                    html_content = f.read()
            if css_file and os.path.exists(css_file):
                with open(css_file, "r") as f:
                    css_content = f.read()
            if js_file and os.path.exists(js_file):
                with open(js_file, "r") as f:
                    js_content = f.read()
            
            with open(page_path / "index.html", "w") as f:
                f.write(html_content)
            if css_content:
                with open(page_path / "styles.css", "w") as f:
                    f.write(css_content)
            if js_content:
                with open(page_path / "script.js", "w") as f:
                    f.write(js_content)
            
            with flask_app.app_context():
                website = Website.query.filter_by(name=website_name).first()
                if not website:
                    raise ValueError(f"Website '{website_name}' not found in database")
                page = Page(
                    website_id=website.id,
                    name=page_name,
                    html_content=html_content,
                    css_content=css_content,
                    js_content=js_content,
                    path=str(page_path.relative_to(SITES_DIR))
                )
                db.session.add(page)
                db.session.commit()
            
            console.print(f"[green]Imported assets for page '{page_name}' in website '{website_name}'[/green]")
            logging.info(f"Imported assets for page '{page_name}' in website '{website_name}'")
            return {"page_name": page_name, "html_content": html_content, "css_content": css_content, "js_content": js_content}
        except Exception as e:
            console.print(f"[red]Error importing assets for {website_name}: {e}[/red]")
            logging.error(f"Asset import failed for {website_name}: {e}")
            return {}

    def stop(self):
        """
        Stop all nodes, Tor processes, and web servers, and clean up resources.

        Raises:
            Exception: If resource cleanup fails.
        """
        for node in self.nodes:
            node.stop()
        for website_name, process in self.tor_processes.items():
            try:
                process.terminate()
                process.wait(timeout=5)
                console.print(f"[yellow]Stopped Tor process for {website_name}[/yellow]")
                logging.info(f"Stopped Tor process for {website_name}")
            except Exception as e:
                console.print(f"[red]Error stopping Tor process for {website_name}: {e}[/red]")
                logging.error(f"Error stopping Tor process for {website_name}: {e}")
        for website_name, (app, socketio_instance, port) in self.web_servers.items():
            try:
                socketio_instance.stop()
                console.print(f"[yellow]Stopped web server for {website_name} on port {port}[/yellow]")
                logging.info(f"Stopped web server for {website_name} on port {port}")
            except Exception as e:
                console.print(f"[red]Error stopping web server for {website_name}: {e}[/red]")
                logging.error(f"Error stopping web server for {website_name}: {e}")
        with flask_app.app_context():
            db.session.remove()
        for dir_path in [TOR_DIR, HIDDEN_SERVICE_DIR]:
            for item in dir_path.iterdir():
                try:
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()
                except Exception as e:
                    logging.error(f"Error cleaning up {item}: {e}")
        self.nodes.clear()
        self.tor_processes.clear()
        self.web_servers.clear()
        self.used_ports.clear()
        self.used_ips.clear()
        console.print("[yellow]Proxy chain stopped and resources cleaned up.[/yellow]")
        logging.info("Proxy chain stopped and resources cleaned up")

# Flask routes for management interface
@flask_app.route('/editor/<website_name>')
def editor(website_name):
    """
    Render the WYSIWYG editor for a website.

    Args:
        website_name (str): Name of the website.

    Returns:
        str: Rendered editor template or error message.
    """
    try:
        website_name = secure_filename(website_name)
        with flask_app.app_context():
            website = Website.query.filter_by(name=website_name).first()
            if not website:
                return "Website not found", 404
            pages = Page.query.filter_by(website_id=website.id).all()
            if not pages:
                return "No pages found", 404
        return render_template_string(WYSIWYG_TEMPLATE, website_name=website_name, pages=pages)
    except Exception as e:
        logging.error(f"Error rendering editor for {website_name}: {e}")
        return f"Error loading editor: {e}", 500

@flask_app.route('/get_page/<website_name>/<page_name>')
def get_page(website_name, page_name):
    """
    Get page content for the WYSIWYG editor.

    Args:
        website_name (str): Name of the website.
        page_name (str): Name of the page.

    Returns:
        JSON: Page content or error message.
    """
    try:
        website_name = secure_filename(website_name)
        page_name = secure_filename(page_name)
        with flask_app.app_context():
            website = Website.query.filter_by(name=website_name).first()
            if not website:
                return jsonify({"error": "Website not found"}), 404
            page = Page.query.filter_by(website_id=website.id, name=page_name).first()
            if not page:
                return jsonify({"error": "Page not found"}), 404
            return jsonify({
                "html_content": page.html_content,
                "css_content": page.css_content,
                "js_content": page.js_content
            })
    except Exception as e:
        logging.error(f"Error fetching page {page_name} for {website_name}: {e}")
        return jsonify({"error": str(e)}), 500

@flask_app.route('/update_page', methods=['POST'])
def update_page():
    """
    Update page content via the WYSIWYG editor.

    Returns:
        JSON: Success or error message.
    """
    try:
        data = request.get_json()
        website_name = secure_filename(data['website_name'])
        page_name = secure_filename(data['page_name'])
        if not website_name or not page_name:
            return jsonify({"error": "Invalid website or page name"}), 400
        html_content = data['html_content']
        css_content = data.get('css_content', '')
        js_content = data.get('js_content', '')
        with flask_app.app_context():
            website = Website.query.filter_by(name=website_name).first()
            if not website:
                return jsonify({"error": "Website not found"}), 404
            page = Page.query.filter_by(website_id=website.id, name=page_name).first()
            if not page:
                return jsonify({"error": "Page not found"}), 404
            page.html_content = html_content
            page.css_content = css_content
            page.js_content = js_content
            page_path = SITES_DIR / page.path
            with open(page_path / "index.html", "w") as f:
                f.write(html_content)
            if css_content:
                with open(page_path / "styles.css", "w") as f:
                    f.write(css_content)
            if js_content:
                with open(page_path / "script.js", "w") as f:
                    f.write(js_content)
            db.session.commit()
            return jsonify({"message": "Page updated successfully"})
        except Exception as e:
            logging.error(f"Error updating page {page_name} for {website_name}: {e}")
            return jsonify({"error": str(e)}), 500

@flask_app.route('/add_page', methods=['POST'])
def add_page():
    """
    Add a new page to a website.

    Returns:
        JSON: Success or error message.
    """
    try:
        data = request.get_json()
        website_name = secure_filename(data['website_name'])
        page_name = secure_filename(data['page_name'])
        if not website_name or not page_name:
            return jsonify({"error": "Invalid website or page name"}), 400
        html_content = data.get('html_content', '<html><body><h1>New Page</h1></body></html>')
        css_content = data.get('css_content', '')
        js_content = data.get('js_content', '')
        with flask_app.app_context():
            website = Website.query.filter_by(name=website_name).first()
            if not website:
                return jsonify({"error": "Website not found"}), 404
            page_path = SITES_DIR / website_name / page_name
            page_path.mkdir(exist_ok=True)
            with open(page_path / "index.html", "w") as f:
                f.write(html_content)
            if css_content:
                with open(page_path / "styles.css", "w") as f:
                    f.write(css_content)
            if js_content:
                with open(page_path / "script.js", "w") as f:
                    f.write(js_content)
            page = Page(
                website_id=website.id,
                name=page_name,
                html_content=html_content,
                css_content=css_content,
                js_content=js_content,
                path=str(page_path.relative_to(SITES_DIR))
            )
            db.session.add(page)
            db.session.commit()
            return jsonify({"message": "Page added successfully"})
        except Exception as e:
            logging.error(f"Error adding page {page_name} for {website_name}: {e}")
            return jsonify({"error": str(e)}), 500

@flask_app.route('/submit_review/<website_name>', methods=['POST'])
def submit_review(website_name):
    """
    Submit a review for a website.

    Args:
        website_name (str): Name of the website.

    Returns:
        JSON: Success or error message.
    """
    try:
        website_name = secure_filename(website_name)
        data = request.get_json()
        name = secure_filename(data['name'])
        rating = int(data['rating'])
        comment = data['comment']
        if not name or not comment or not (1 <= rating <= 5):
            return jsonify({"error": "Invalid review data"}), 400
        with flask_app.app_context():
            website = Website.query.filter_by(name=website_name).first()
            if not website:
                return jsonify({"error": "Website not found"}), 404
            review = Review(
                website_id=website.id,
                name=name,
                rating=rating,
                comment=comment,
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            db.session.add(review)
            db.session.commit()
            return jsonify({"message": "Review submitted successfully"})
        except Exception as e:
            logging.error(f"Error submitting review for {website_name}: {e}")
            return jsonify({"error": str(e)}), 500

@flask_app.route('/get_reviews/<website_name>')
def get_reviews(website_name):
    """
    Get all reviews for a website.

    Args:
        website_name (str): Name of the website.

    Returns:
        JSON: List of reviews or error message.
    """
    try:
        website_name = secure_filename(website_name)
        with flask_app.app_context():
            website = Website.query.filter_by(name=website_name).first()
            if not website:
                logging.error(f"Website '{website_name}' not found in database")
                return jsonify({"error": "Website not found"}), 404
            reviews = Review.query.filter_by(website_id=website.id).order_by(Review.timestamp.desc()).all()
            review_list = [{
                "id": r.id,
                "name": r.name,
                "rating": r.rating,
                "comment": r.comment,
                "timestamp": r.timestamp
            } for r in reviews]
            logging.info(f"Retrieved {len(review_list)} reviews for website '{website_name}'")
            return jsonify({"reviews": review_list})
    except Exception as e:
        logging.error(f"Error fetching reviews for {website_name}: {e}")
        return jsonify({"error": f"Failed to fetch reviews: {str(e)}"}), 500

@flask_app.route('/delete_review/<website_name>/<int:review_id>', methods=['DELETE'])
def delete_review(website_name, review_id):
    """
    Delete a specific review for a website.

    Args:
        website_name (str): Name of the website.
        review_id (int): ID of the review to delete.

    Returns:
        JSON: Success or error message.
    """
    try:
        website_name = secure_filename(website_name)
        with flask_app.app_context():
            website = Website.query.filter_by(name=website_name).first()
            if not website:
                logging.error(f"Website '{website_name}' not found in database")
                return jsonify({"error": "Website not found"}), 404
            review = Review.query.filter_by(id=review_id, website_id=website.id).first()
            if not review:
                logging.error(f"Review ID {review_id} not found for website '{website_name}'")
                return jsonify({"error": "Review not found"}), 404
            db.session.delete(review)
            db.session.commit()
            logging.info(f"Deleted review ID {review_id} for website '{website_name}'")
            return jsonify({"message": "Review deleted successfully"})
    except Exception as e:
        logging.error(f"Error deleting review {review_id} for {website_name}: {e}")
        return jsonify({"error": f"Failed to delete review: {str(e)}"}), 500

@flask_app.route('/get_chat_messages/<website_name>')
def get_chat_messages(website_name):
    """
    Get all chat messages for a website.

    Args:
        website_name (str): Name of the website.

    Returns:
        JSON: List of chat messages or error message.
    """
    try:
        website_name = secure_filename(website_name)
        with flask_app.app_context():
            website = Website.query.filter_by(name=website_name).first()
            if not website:
                logging.error(f"Website '{website_name}' not found in database")
                return jsonify({"error": "Website not found"}), 404
            messages = ChatMessage.query.filter_by(website_id=website.id).order_by(ChatMessage.timestamp.desc()).limit(100).all()
            message_list = [msg.as_dict() for msg in messages]
            logging.info(f"Retrieved {len(message_list)} chat messages for website '{website_name}'")
            return jsonify({"messages": message_list})
    except Exception as e:
        logging.error(f"Error fetching chat messages for {website_name}: {e}")
        return jsonify({"error": f"Failed to fetch chat messages: {str(e)}"}), 500

@flask_app.route('/status')
def get_status():
    """
    Get the status of all proxy nodes and websites.

    Returns:
        JSON: Status of nodes and websites.
    """
    try:
        chain = ProxyChain()
        node_statuses = [{
            "host": node.host,
            "port": node.port,
            "locale": node.locale['country'],
            "virtual_ip": node.virtual_ip,
            "virtual_mac": node.virtual_mac,
            "active": node.active,
            "stats": node.stats
        } for node in chain.nodes]
        website_statuses = [{
            "name": website['name'],
            "port": website['port'],
            "onion_address": website['onion_address'],
            "running": website['name'] in chain.web_servers
        } for website in chain.websites]
        logging.info("Retrieved system status")
        return jsonify({
            "nodes": node_statuses,
            "websites": website_statuses,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    except Exception as e:
        logging.error(f"Error fetching system status: {e}")
        return jsonify({"error": f"Failed to fetch status: {str(e)}"}), 500

# Templates
CHAT_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ website_name }} - Chatroom</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f4f4f4;
            margin: 0;
            padding: 20px;
        }
        .chat-container {
            max-width: 800px;
            margin: auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
            padding: 20px;
        }
        .chat-messages {
            height: 400px;
            overflow-y: auto;
            border: 1px solid #ccc;
            padding: 10px;
            margin-bottom: 20px;
        }
        .chat-message {
            margin: 10px 0;
        }
        .chat-message .username {
            font-weight: bold;
            color: #333;
        }
        .chat-message .timestamp {
            font-size: 0.8em;
            color: #777;
        }
        .chat-input {
            display: flex;
            gap: 10px;
        }
        .chat-input input[type="text"] {
            flex: 1;
            padding: 10px;
            border: 1px solid #ccc;
            border-radius: 4px;
        }
        .chat-input button {
            padding: 10px 20px;
            background-color: #28a745;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        .chat-input button:hover {
            background-color: #218838;
        }
    </style>
    <script src="https://cdn.socket.io/4.7.5/socket.io.min.js"></script>
</head>
<body>
    <div class="chat-container">
        <h2>{{ website_name }} Chatroom</h2>
        <div class="chat-messages" id="chatMessages"></div>
        <div class="chat-input">
            <input type="text" id="username" placeholder="Your name" required>
            <input type="text" id="message" placeholder="Type a message..." required>
            <button onclick="sendMessage()">Send</button>
        </div>
    </div>
    <script>
        const socket = io();
        socket.on('connect', () => {
            console.log('Connected to chat server');
        });
        socket.on('message', (msg) => {
            const messages = document.getElementById('chatMessages');
            const messageElement = document.createElement('div');
            messageElement.className = 'chat-message';
            messageElement.innerHTML = `
                <span class="username">${msg.username}</span> 
                <span class="timestamp">(${msg.timestamp})</span>: 
                ${msg.message}
            `;
            messages.appendChild(messageElement);
            messages.scrollTop = messages.scrollHeight;
        });
        function sendMessage() {
            const username = document.getElementById('username').value.trim();
            const message = document.getElementById('message').value.trim();
            if (username && message) {
                socket.emit('message', { username, message });
                document.getElementById('message').value = '';
            }
        }
        document.getElementById('message').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });
        // Fetch initial messages
        fetch('/get_chat_messages/{{ website_name }}')
            .then(response => response.json())
            .then(data => {
                if (data.messages) {
                    const messages = document.getElementById('chatMessages');
                    data.messages.reverse().forEach(msg => {
                        const messageElement = document.createElement('div');
                        messageElement.className = 'chat-message';
                        messageElement.innerHTML = `
                            <span class="username">${msg.username}</span> 
                            <span class="timestamp">(${msg.timestamp})</span>: 
                            ${msg.message}
                        `;
                        messages.appendChild(messageElement);
                    });
                    messages.scrollTop = messages.scrollHeight;
                }
            });
    </script>
</body>
</html>
"""

REVIEW_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ website_name }} - Reviews</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f4f4f4;
            margin: 0;
            padding: 20px;
        }
        .review-container {
            max-width: 800px;
            margin: auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
            padding: 20px;
        }
        .review-form {
            margin-bottom: 20px;
        }
        .review-form input, .review-form textarea {
            width: 100%;
            padding: 10px;
            margin: 5px 0;
            border: 1px solid #ccc;
            border-radius: 4px;
        }
        .review-form button {
            padding: 10px 20px;
            background-color: #28a745;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        .review-form button:hover {
            background-color: #218838;
        }
        .review-list {
            border-top: 1px solid #ccc;
            padding-top: 20px;
        }
        .review-item {
            margin: 10px 0;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        .review-item .rating {
            color: #f39c12;
            font-weight: bold;
        }
        .review-item .timestamp {
            font-size: 0.8em;
            color: #777;
        }
    </style>
</head>
<body>
    <div class="review-container">
        <h2>{{ website_name }} Reviews</h2>
        <div class="review-form">
            <form method="POST">
                {{ form.hidden_tag() }}
                <div>
                    {{ form.name.label }} {{ form.name() }}
                </div>
                <div>
                    {{ form.rating.label }} {{ form.rating(min=1, max=5) }}
                </div>
                <div>
                    {{ form.comment.label }} {{ form.comment() }}
                </div>
                {{ form.submit() }}
            </form>
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <p style="color: {{ 'green' if category == 'success' else 'red' }}">{{ message }}</p>
                    {% endfor %}
                {% endif %}
            {% endwith %}
        </div>
        <div class="review-list">
            {% for review in reviews %}
                <div class="review-item">
                    <p><strong>{{ review.name }}</strong> <span class="rating">{{ '★' * review.rating }}{{ '☆' * (5 - review.rating) }}</span></p>
                    <p>{{ review.comment }}</p>
                    <p class="timestamp">{{ review.timestamp }}</p>
                </div>
            {% endfor %}
        </div>
    </div>
</body>
</html>
"""

WYSIWYG_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ website_name }} - WYSIWYG Editor</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f4f4f4;
        }
        .editor-container {
            max-width: 1200px;
            margin: auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
            padding: 20px;
            display: flex;
            gap: 20px;
        }
        .sidebar {
            width: 200px;
        }
        .editor {
            flex: 1;
        }
        .page-list {
            list-style: none;
            padding: 0;
        }
        .page-list li {
            padding: 10px;
            cursor: pointer;
            border-bottom: 1px solid #ddd;
        }
        .page-list li:hover {
            background-color: #f0f0f0;
        }
        .editor textarea {
            width: 100%;
            height: 200px;
            margin: 10px 0;
            border: 1px solid #ccc;
            border-radius: 4px;
            padding: 10px;
        }
        .editor button {
            padding: 10px 20px;
            background-color: #007bff;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            margin-right: 10px;
        }
        .editor button:hover {
            background-color: #0056b3;
        }
        .preview {
            border: 1px solid #ccc;
            padding: 10px;
            min-height: 200px;
            background: white;
        }
    </style>
    <script src="https://cdn.ckeditor.com/4.22.1/standard/ckeditor.js"></script>
</head>
<body>
    <div class="editor-container">
        <div class="sidebar">
            <h3>Pages</h3>
            <ul class="page-list">
                {% for page in pages %}
                    <li onclick="loadPage('{{ page.name }}')">{{ page.name }}</li>
                {% endfor %}
                <li><button onclick="addPage()">Add New Page</button></li>
            </ul>
        </div>
        <div class="editor">
            <h2>{{ website_name }} Editor</h2>
            <div>
                <label>Page Name:</label>
                <input type="text" id="pageName" readonly>
            </div>
            <div>
                <label>HTML Content:</label>
                <textarea id="htmlContent"></textarea>
            </div>
            <div>
                <label>CSS Content:</label>
                <textarea id="cssContent"></textarea>
            </div>
            <div>
                <label>JavaScript Content:</label>
                <textarea id="jsContent"></textarea>
            </div>
            <button onclick="savePage()">Save Page</button>
            <button onclick="previewPage()">Preview Page</button>
            <div class="preview" id="preview"></div>
        </div>
    </div>
    <script>
        CKEDITOR.replace('htmlContent');
        CKEDITOR.replace('cssContent', { height: 100 });
        CKEDITOR.replace('jsContent', { height: 100 });

        function loadPage(pageName) {
            fetch(`/get_page/{{ website_name }}/${pageName}`)
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        alert(data.error);
                        return;
                    }
                    document.getElementById('pageName').value = pageName;
                    CKEDITOR.instances.htmlContent.setData(data.html_content);
                    CKEDITOR.instances.cssContent.setData(data.css_content);
                    CKEDITOR.instances.jsContent.setData(data.js_content);
                    previewPage();
                })
                .catch(error => alert('Error loading page: ' + error));
        }

        function savePage() {
            const pageName = document.getElementById('pageName').value;
            if (!pageName) {
                alert('No page selected');
                return;
            }
            const data = {
                website_name: '{{ website_name }}',
                page_name: pageName,
                html_content: CKEDITOR.instances.htmlContent.getData(),
                css_content: CKEDITOR.instances.cssContent.getData(),
                js_content: CKEDITOR.instances.jsContent.getData()
            };
            fetch('/update_page', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            })
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        alert(data.error);
                    } else {
                        alert(data.message);
                        previewPage();
                    }
                })
                .catch(error => alert('Error saving page: ' + error));
        }

        function addPage() {
            const pageName = prompt('Enter new page name:');
            if (pageName) {
                const data = {
                    website_name: '{{ website_name }}',
                    page_name: pageName,
                    html_content: '<html><body><h1>New Page</h1></body></html>',
                    css_content: '',
                    js_content: ''
                };
                fetch('/add_page', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                })
                    .then(response => response.json())
                    .then(data => {
                        if (data.error) {
                            alert(data.error);
                        } else {
                            alert(data.message);
                            location.reload();
                        }
                    })
                    .catch(error => alert('Error adding page: ' + error));
            }
        }

        function previewPage() {
            const html = CKEDITOR.instances.htmlContent.getData();
            const css = CKEDITOR.instances.cssContent.getData();
            const js = CKEDITOR.instances.jsContent.getData();
            const preview = document.getElementById('preview');
            preview.innerHTML = html;
            if (css) {
                const style = document.createElement('style');
                style.innerHTML = css;
                preview.appendChild(style);
            }
            if (js) {
                const script = document.createElement('script');
                script.innerHTML = js;
                preview.appendChild(script);
            }
        }
    </script>
</body>
</html>
"""

class ProxyGUI:
    """
    GUI interface for managing the proxy chain, websites, and monitoring.

    Attributes:
        chain (ProxyChain): The proxy chain instance.
        root (tk.Tk): Main Tkinter window.
        node_frame (ttk.Frame): Frame for node status display.
        website_frame (ttk.Frame): Frame for website management.
        log_text (Text): Widget for displaying logs.
        stats_canvas (FigureCanvasTkAgg): Matplotlib canvas for statistics.
    """
    def __init__(self, chain: ProxyChain):
        self.chain = chain
        self.root = tk.Tk()
        self.root.title("99Proxys v5.0.0 - BG Gremlin Group")
        self.root.geometry("1200x800")
        self.node_frame = None
        self.website_frame = None
        self.log_text = None
        self.stats_canvas = None
        self.setup_gui()
        self.update_status()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

    def setup_gui(self):
        """
        Set up the Tkinter GUI with tabs for nodes, websites, and logs.
        """
        # Display ASCII art in console
        console.print(Panel(ASCII_ART, title="99Proxys", style="cyan"))

        # Main notebook (tabs)
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # Nodes tab
        self.node_frame = ttk.Frame(notebook)
        notebook.add(self.node_frame, text="Proxy Nodes")
        self.setup_node_tab()

        # Websites tab
        self.website_frame = ttk.Frame(notebook)
        notebook.add(self.website_frame, text="Websites")
        self.setup_website_tab()

        # Logs tab
        log_frame = ttk.Frame(notebook)
        notebook.add(log_frame, text="Logs")
        self.setup_log_tab(log_frame)

        # Statistics tab
        stats_frame = ttk.Frame(notebook)
        notebook.add(stats_frame, text="Statistics")
        self.setup_stats_tab(stats_frame)

    def setup_node_tab(self):
        """
        Set up the node management tab.
        """
        # Control buttons
        control_frame = ttk.Frame(self.node_frame)
        control_frame.pack(fill='x', pady=5)

        ttk.Button(control_frame, text="Start Chain", command=self.start_chain).pack(side='left', padx=5)
        ttk.Button(control_frame, text="Stop Chain", command=self.stop_chain).pack(side='left', padx=5)
        ttk.Button(control_frame, text="Restart Chain", command=self.restart_chain).pack(side='left', padx=5)

        # Node status table
        tree = ttk.Treeview(self.node_frame, columns=("Host", "Port", "Locale", "Virtual IP", "MAC", "Active", "Requests", "Latency", "Errors"), show='headings')
        tree.heading("Host", text="Host")
        tree.heading("Port", text="Port")
        tree.heading("Locale", text="Locale")
        tree.heading("Virtual IP", text="Virtual IP")
        tree.heading("MAC", text="MAC Address")
        tree.heading("Active", text="Active")
        tree.heading("Requests", text="Requests")
        tree.heading("Latency", text="Latency (s)")
        tree.heading("Errors", text="Errors")
        tree.pack(fill='both', expand=True, padx=10, pady=10)
        self.node_tree = tree

    def setup_website_tab(self):
        """
        Set up the website management tab.
        """
        # Website creation form
        form_frame = ttk.Frame(self.website_frame)
        form_frame.pack(fill='x', pady=5)

        ttk.Label(form_frame, text="Website Name:").pack(side='left', padx=5)
        self.website_name_entry = ttk.Entry(form_frame)
        self.website_name_entry.pack(side='left', padx=5)
        ttk.Button(form_frame, text="Create Website", command=self.create_website).pack(side='left', padx=5)
        ttk.Button(form_frame, text="Import Assets", command=self.import_assets).pack(side='left', padx=5)

        # Website table
        tree = ttk.Treeview(self.website_frame, columns=("Name", "Port", "Onion Address", "Status"), show='headings')
        tree.heading("Name", text="Name")
        tree.heading("Port", text="Port")
        tree.heading("Onion Address", text="Onion Address")
        tree.heading("Status", text="Status")
        tree.pack(fill='both', expand=True, padx=10, pady=10)
        tree.bind('<Double-1>', self.open_website)
        self.website_tree = tree

    def setup_log_tab(self, log_frame):
        """
        Set up the log display tab.

        Args:
            log_frame (ttk.Frame): Frame for the log tab.
        """
        self.log_text = Text(log_frame, height=20, width=100)
        self.log_text.pack(fill='both', expand=True, padx=10, pady=10)
        self.log_text.config(state='disabled')

        # Tail the log file
        threading.Thread(target=self.tail_log, daemon=True).start()

    def setup_stats_tab(self, stats_frame):
        """
        Set up the statistics visualization tab.

        Args:
            stats_frame (ttk.Frame): Frame for the stats tab.
        """
        fig, ax = plt.subplots(figsize=(8, 4))
        self.stats_canvas = FigureCanvasTkAgg(fig, master=stats_frame)
        self.stats_canvas.get_tk_widget().pack(fill='both', expand=True, padx=10, pady=10)
        self.stats_ax = ax
        ttk.Button(stats_frame, text="Refresh Stats", command=self.update_stats).pack(pady=5)

    def start_chain(self):
        """
        Start the proxy chain.
        """
        try:
            self.chain.initialize_nodes()
            console.print("[green]Proxy chain started.[/green]")
            logging.info("Proxy chain started")
            self.update_status()
        except Exception as e:
            console.print(f"[red]Error starting proxy chain: {e}[/red]")
            logging.error(f"Error starting proxy chain: {e}")
            messagebox.showerror("Error", f"Failed to start proxy chain: {str(e)}")

    def stop_chain(self):
        """
        Stop the proxy chain.
        """
        try:
            self.chain.stop()
            console.print("[yellow]Proxy chain stopped.[/yellow]")
            logging.info("Proxy chain stopped")
            self.update_status()
        except Exception as e:
            console.print(f"[red]Error stopping proxy chain: {e}[/red]")
            logging.error(f"Error stopping proxy chain: {e}")
            messagebox.showerror("Error", f"Failed to stop proxy chain: {str(e)}")

    def restart_chain(self):
        """
        Restart the proxy chain.
        """
        try:
            self.stop_chain()
            time.sleep(2)
            self.start_chain()
            console.print("[green]Proxy chain restarted.[/green]")
            logging.info("Proxy chain restarted")
        except Exception as e:
            console.print(f"[red]Error restarting proxy chain: {e}[/red]")
            logging.error(f"Error restarting proxy chain: {e}")
            messagebox.showerror("Error", f"Failed to restart proxy chain: {str(e)}")

    def create_website(self):
        """
        Create a new website with a default page.
        """
        website_name = self.website_name_entry.get().strip()
        if not website_name:
            messagebox.showerror("Error", "Website name cannot be empty")
            return
        try:
            pages = [{
                "name": "index",
                "html_content": "<html><body><h1>Welcome to " + website_name + "</h1></body></html>",
                "css_content": "body { font-family: Arial; }",
                "js_content": ""
            }]
            self.chain.create_website(website_name, pages)
            self.update_status()
            webbrowser.open(f"http://127.0.0.1:{CONFIG['WEB_PORT']}/editor/{website_name}")
        except Exception as e:
            console.print(f"[red]Error creating website '{website_name}': {e}[/red]")
            logging.error(f"Error creating website '{website_name}': {e}")
            messagebox.showerror("Error", f"Failed to create website: {str(e)}")

    def import_assets(self):
        """
        Import assets for a website.
        """
        website_name = self.website_name_entry.get().strip()
        if not website_name:
            messagebox.showerror("Error", "Website name cannot be empty")
            return
        html_file = filedialog.askopenfilename(title="Select HTML File", filetypes=[("HTML files", "*.html")])
        css_file = filedialog.askopenfilename(title="Select CSS File", filetypes=[("CSS files", "*.css")])
        js_file = filedialog.askopenfilename(title="Select JavaScript File", filetypes=[("JavaScript files", "*.js")])
        try:
            self.chain.import_assets(website_name, html_file or None, css_file or None, js_file or None)
            self.update_status()
            messagebox.showinfo("Success", f"Assets imported for website '{website_name}'")
        except Exception as e:
            console.print(f"[red]Error importing assets for '{website_name}': {e}[/red]")
            logging.error(f"Error importing assets for '{website_name}': {e}")
            messagebox.showerror("Error", f"Failed to import assets: {str(e)}")

    def open_website(self, event):
        """
        Open the selected website in the editor.

        Args:
            event: Tkinter event for double-click.
        """
        selection = self.website_tree.selection()
        if not selection:
            return
        item = self.website_tree.item(selection[0])
        website_name = item['values'][0]
        webbrowser.open(f"http://127.0.0.1:{CONFIG['WEB_PORT']}/editor/{website_name}")

    def update_status(self):
        """
        Update the GUI with the current status of nodes and websites.
        """
        # Update node table
        for item in self.node_tree.get_children():
            self.node_tree.delete(item)
        for node in self.chain.nodes:
            self.node_tree.insert("", "end", values=(
                node.host,
                node.port,
                node.locale['country'],
                node.virtual_ip,
                node.virtual_mac,
                "Active" if node.active else "Inactive",
                node.stats["requests"],
                f"{node.stats['latency']:.2f}",
                node.stats["errors"]
            ))

        # Update website table
        for item in self.website_tree.get_children():
            self.website_tree.delete(item)
        for website in self.chain.websites:
            self.website_tree.insert("", "end", values=(
                website["name"],
                website["port"],
                website["onion_address"],
                "Running" if website["name"] in self.chain.web_servers else "Stopped"
            ))

        # Update stats
        self.update_stats()

    def update_stats(self):
        """
        Update the statistics plot.
        """
        self.stats_ax.clear()
        nodes = [f"Node {n.port}" for n in self.chain.nodes]
        requests = [n.stats["requests"] for n in self.chain.nodes]
        errors = [n.stats["errors"] for n in self.chain.nodes]
        if nodes:
            x = range(len(nodes))
            self.stats_ax.bar(x, requests, width=0.4, label="Requests", color="blue")
            self.stats_ax.bar([i + 0.4 for i in x], errors, width=0.4, label="Errors", color="red")
            self.stats_ax.set_xticks([i + 0.2 for i in x])
            self.stats_ax.set_xticklabels(nodes, rotation=45)
            self.stats_ax.set_ylabel("Count")
            self.stats_ax.set_title("Node Performance")
            self.stats_ax.legend()
            self.stats_canvas.draw()

    def tail_log(self):
        """
        Tail the log file and display updates in the GUI.
        """
        log_file = LOG_DIR / f"99proxys_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        while not log_file.exists():
            time.sleep(1)
        with open(log_file, 'r') as f:
            f.seek(0, os.SEEK_END)
            while True:
                line = f.readline()
                if not line:
                    time.sleep(0.1)
                    continue
                self.log_text.config(state='normal')
                self.log_text.insert(tk.END, line)
                self.log_text.see(tk.END)
                self.log_text.config(state='disabled')

    def on_closing(self):
        """
        Handle window closing event.
        """
        if messagebox.askokcancel("Quit", "Do you want to quit and stop all services?"):
            self.chain.stop()
            self.root.destroy()

def install_dependencies():
    """
    Install required Python packages if not present or outdated.
    """
    console.print("[cyan]Checking dependencies...[/cyan]")
    for pkg, required_version in REQUIRED_PACKAGES.items():
        try:
            installed_version = pkg_resources.get_distribution(pkg).version
            if version.parse(installed_version) < version.parse(required_version):
                console.print(f"[yellow]Upgrading {pkg} from {installed_version} to {required_version}...[/yellow]")
                subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", f"{pkg}=={required_version}"], check=True)
                logging.info(f"Upgraded {pkg} to version {required_version}")
            else:
                console.print(f"[green]{pkg} {installed_version} is up to date.[/green]")
        except pkg_resources.DistributionNotFound:
            console.print(f"[yellow]Installing {pkg} {required_version}...[/yellow]")
            subprocess.run([sys.executable, "-m", "pip", "install", f"{pkg}=={required_version}"], check=True)
            logging.info(f"Installed {pkg} version {required_version}")
        except Exception as e:
            console.print(f"[red]Error installing {pkg}: {e}[/red]")
            logging.error(f"Error installing {pkg}: {e}")
            sys.exit(1)

def generate_self_signed_cert():
    """
    Generate a self-signed SSL certificate if not already present.
    """
    if CERT_FILE.exists() and KEY_FILE.exists():
        console.print("[green]SSL certificates already exist.[/green]")
        logging.info("SSL certificates already exist")
        return
    try:
        console.print("[cyan]Generating self-signed SSL certificate...[/cyan]")
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, "99Proxys Local VPN"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "BG Gremlin Group"),
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US")
        ])
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(private_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.utcnow())
            .not_valid_after(datetime.utcnow() + timedelta(days=365))
            .add_extension(
                x509.SubjectAlternativeName([x509.DNSName("localhost")]),
                critical=False
            )
        ).sign(private_key, hashes.SHA256())
        with open(CERT_FILE, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        with open(KEY_FILE, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            ))
        console.print("[green]SSL certificate generated.[/green]")
        logging.info("SSL certificate generated")
    except Exception as e:
        console.print(f"[red]Error generating SSL certificate: {e}[/red]")
        logging.error(f"Error generating SSL certificate: {e}")
        sys.exit(1)

def create_documentation():
    """
    Generate detailed documentation for the 99Proxys application.
    """
    try:
        doc_content = """
# 99Proxys v5.0.0 Documentation

## Overview
99Proxys is a proprietary local virtual VPN network developed by the BG Gremlin Group. It emulates a Tor-like onion routing network with SOCKS5 proxy nodes, supporting up to 99 nodes with simulated locales, rolling virtual IPs, and MAC addresses. The system includes features for creating hidden services, hosting websites with chatrooms and reviews, and a WYSIWYG editor for website management.

## Features
- **SOCKS5 Proxy Nodes**: Configurable nodes (5–99) with SSL/TLS encryption, rate limiting, and bandwidth throttling.
- **Locale Simulation**: Emulates 99 different geographic locales with corresponding timezones and IP ranges.
- **Hidden Services**: Tor-compatible hidden services for anonymous website hosting.
- **Website Management**: Create multi-page websites with HTML, CSS, and JavaScript, including chatrooms and review systems.
- **WYSIWYG Editor**: Browser-based editor for real-time website content management.
- **GUI Interface**: Tkinter-based interface for managing nodes, websites, and monitoring performance.
- **Security**: Fernet and RSA encryption for data, self-signed SSL certificates, and CSRF protection.
- **Monitoring**: Real-time node status, performance statistics, and logging.

## Installation
1. Ensure Python 3.8+ is installed.
2. Install Tor (`tor` package) on your system.
3. Run the script with root privileges for virtual IP assignment:
   ```bash
   sudo python3 99proxys.py
   ```
4. The script automatically installs required Python packages (scapy, rich, psutil, etc.).

## Configuration
Configuration is stored in `config/99proxys_config.json`. Default settings:
- **Node Count**: 5 (configurable 5–99)
- **IP Range**: 192.168.0.0/16
- **Port Range**: 1024–65535
- **Bandwidth Limit**: 1000 kbps
- **Rate Limit**: 100 requests/min
- **Health Check Interval**: 30 seconds

## Usage
1. **Start the Application**:
   - Run the script to launch the GUI.
   - The Flask server starts on `http://127.0.0.1:5000` for the WYSIWYG editor and API.

2. **Manage Proxy Nodes**:
   - Use the "Nodes" tab to start, stop, or restart the proxy chain.
   - View node status, including host, port, locale, virtual IP/MAC, and performance metrics.

3. **Create Websites**:
   - In the "Websites" tab, enter a website name and click "Create Website".
   - A default page is created, and a Tor hidden service is set up.
   - Access the WYSIWYG editor at `http://127.0.0.1:5000/editor/<website_name>`.

4. **Import Assets**:
   - Select HTML, CSS, and JavaScript files to import as new pages for a website.

5. **Monitor Logs and Stats**:
   - The "Logs" tab displays real-time log output.
   - The "Statistics" tab shows bar charts of node requests and errors.

## Security Considerations
- **Root Privileges**: Required for assigning virtual IPs. Use `sudo` or configure `setcap` for the Python executable.
- **SSL/TLS**: Self-signed certificates are generated for secure communication.
- **Encryption**: Data is encrypted using Fernet for symmetric encryption and RSA for key exchange between nodes.
- **CSRF Protection**: Enabled for web forms to prevent cross-site request forgery.

## Directory Structure
- `config/`: Configuration files.
- `logs/`: Log files.
- `data/`: Database and temporary data.
- `assets/`: Static assets for websites.
- `certs/`: SSL certificates and encryption keys.
- `tor_data/`: Tor data directories.
- `hidden_services/`: Tor hidden service configurations.
- `uploads/`: Uploaded assets.
- `sites/`: Website files.
- `docs/`: Documentation.

## Troubleshooting
- **Tor Not Found**: Ensure the `tor` executable is installed and accessible.
- **Port Conflicts**: Check the configured port range and ensure no other services are using them.
- **Permission Errors**: Run with `sudo` or configure `setcap` for network capabilities.
- **Log Files**: Check `logs/` for detailed error messages.

## License
Proprietary software by BG Gremlin Group. Unauthorized use or distribution is prohibited. Contact https://github.com/BGGremlin-Group for licensing inquiries.

## Contact
For support or inquiries, contact the BG Gremlin Group at https://github.com/BGGremlin-Group.
"""
        with open(DOCS_DIR / "README.md", "w") as f:
            f.write(doc_content)
        console.print("[green]Documentation generated at docs/README.md[/green]")
        logging.info("Documentation generated")
    except Exception as e:
        console.print(f"[red]Error generating documentation: {e}[/red]")
        logging.error(f"Error generating documentation: {e}")

class TestProxyChain(unittest.TestCase):
    """
    Unit tests for the ProxyChain and related components.
    """
    def setUp(self):
        self.chain = ProxyChain()
        self.chain.config["node_count"] = 2
        self.chain.config["min_port"] = 10000
        self.chain.config["max_port"] = 11000

    def test_node_initialization(self):
        self.chain.initialize_nodes()
        self.assertEqual(len(self.chain.nodes), 2)
        self.assertTrue(all(node.active for node in self.chain.nodes))
        self.assertTrue(all(node.port >= 10000 and node.port <= 11000 for node in self.chain.nodes))

    def test_website_creation(self):
        pages = [{"name": "index", "html_content": "<html><body>Test</body></html>", "css_content": "", "js_content": ""}]
        self.chain.create_website("test_site", pages)
        self.assertTrue(any(w["name"] == "test_site" for w in self.chain.websites))
        site_dir = SITES_DIR / "test_site" / "index" / "index.html"
        self.assertTrue(site_dir.exists())

    def test_hidden_service(self):
        port = self.chain.get_available_port()
        onion_address = self.chain.create_hidden_service("test_service", port)
        self.assertTrue(onion_address.endswith(".onion"))
        self.assertIn("test_service", self.chain.tor_processes)

    def tearDown(self):
        self.chain.stop()

def main():
    """
    Main entry point for the 99Proxys application.
    """
    console.print(Panel(ASCII_ART, title="99Proxys Launch", style="cyan"))
    console.print("[cyan]Starting 99Proxys v5.0.0...[/cyan]")
    logging.info("Starting 99Proxys v5.0.0")
    
    try:
        create_documentation()
        chain = ProxyChain()
        threading.Thread(
            target=lambda: socketio.run(
                flask_app,
                host="127.0.0.1",
                port=CONFIG["WEB_PORT"],
                debug=False,
                use_reloader=False,
                allow_unsafe_werkzeug=True
            ),
            daemon=True
        ).start()
        console.print(f"[green]Flask server started on http://127.0.0.1:{CONFIG['WEB_PORT']}[/green]")
        logging.info(f"Flask server started on port {CONFIG['WEB_PORT']}")
        
        # Run unit tests in development mode
        if os.getenv("DEV_MODE") == "true":
            console.print("[cyan]Running unit tests...[/cyan]")
            unittest.main(argv=[sys.argv[0]], exit=False)
        
        ProxyGUI(chain)
    except Exception as e:
        console.print(f"[red]Fatal error in main: {e}[/red]")
        logging.error(f"Fatal error in main: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
