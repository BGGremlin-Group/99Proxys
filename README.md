# 99Proxys - Private Local VPN Network

<p align="center">
  <img src="[https://github.com/BGGremlin-Group/99Proxys/blob/main/Screenshot_20250805-232112.png]" alt="99Proxys Logo" />
</p>

<p align="center">
  <strong>A robust, cross-platform, local virtual VPN mimicking a private Tor network.</strong><br>
  Designed for journalists and privacy-focused users, 99Proxys offers 5–99 configurable proxy nodes with rolling IPs, MACs, and 99 global locales for maximum anonymity.
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#installation">Installation</a> •
  <a href="#usage">Usage</a> •
  <a href="#configuration">Configuration</a> •
  <a href="#dependencies">Dependencies</a> •
  <a href="#troubleshooting">Troubleshooting</a> •
  <a href="#contributing">Contributing</a>
</p>

---

## Introduction

**99Proxys** is a powerful tool that creates a local virtual VPN network, emulating a private Tor-like onion routing system. It spins up 5–99 user-configurable proxy nodes, each with rolling IP addresses, MAC addresses, and locale simulation (covering 99 countries). Built for cross-platform compatibility (Windows, Kali, Parrot, Ubuntu), it features an interactive CLI and GUI with a sleek black background and vibrant cyan, yellow, green, and magenta accents. The project prioritizes anonymity, robust error handling, and user-friendly automation, making it ideal for journalists and privacy advocates.

---

## Features

- **Local Proxy Chain**: Configurable chain of 5–99 SOCKS5 proxy nodes, all running locally to ensure no third-party dependencies.
- **HTTPS Support**: Full support for HTTPS websites via SOCKS5 `CONNECT` method, preserving end-to-end encryption.
- **Rolling IPs/MACs**: Virtual and real network interface IPs and MACs, with user-configurable ranges and automatic rolling for anonymity.
- **99 Locale Simulation**: Supports 99 countries with timezone, geolocation headers, and metadata simulation for each node.
- **Interactive CLI**: Rich-colored interface with ASCII art, progress bars, tables, and real-time graphs (`plotext`).
- **Cross-Platform GUI**: `tkinter`-based GUI with black background, colorful buttons, and real-time latency graphs (`matplotlib`).
- **Robust Error Handling**: Handles port conflicts, network errors, and system resource limits with graceful exits and detailed logging.
- **Automation**: Auto-installs dependencies, selects ports, configures networks, and creates local config/logs folders.
- **Real-Time Feedback**: Displays connection stats, progress bars, and graphs in CLI and GUI, with verbose logging.
- **Performance**: Ensures minimum throughput of 7 KB/s (56k modem speeds) with resource monitoring via `psutil`.
- **Security**: Node-to-node SSL/TLS encryption and traffic obfuscation for enhanced anonymity.

| Feature | Description | CLI Support | GUI Support |
|---------|-------------|-------------|-------------|
| Proxy Nodes | 5–99 local SOCKS5 nodes | ✅ | ✅ |
| HTTPS Access | SOCKS5 `CONNECT` for HTTPS | ✅ | ✅ |
| IP/MAC Rolling | Virtual/real IPs and MACs | ✅ | ✅ |
| Locale Simulation | 99 countries with metadata | ✅ | ✅ |
| Real-Time Stats | Latency, requests, bytes | ✅ | ✅ |
| Graphs | CLI (`plotext`), GUI (`matplotlib`) | ✅ | ✅ |
| Setup Wizard | Configure nodes, IPs, locales | ✅ | ✅ |
| Error Handling | Port conflicts, network errors | ✅ | ✅ |

---

## Installation

### Prerequisites
- **Operating Systems**: Windows, Kali Linux, Parrot OS, Ubuntu
- **Python**: 3.8 or higher
- **Internet Connection**: Required for initial dependency installation
- **System Resources**: At least 4GB RAM and 2 CPU cores (for 99 nodes)

### Steps
1. **Clone or Download**:
   - Download `99proxys.py` or clone the repository:
     ```bash
     git clone https://github.com/your-repo/99proxys.git
     cd 99proxys
     ```

2. **Run the Program**:
   - **GUI Mode**:
     ```bash
     python 99proxys.py
     ```
   - **CLI Mode**:
     ```bash
     python 99proxys.py --cli
     ```

3. **Automatic Setup**:
   - On first run, the program:
     - Installs dependencies silently via `pip`.
     - Creates folders: `config/`, `logs/`, `data/`, `assets/`.
     - Generates `config/99proxys_config.json` with defaults (5 nodes, 192.168.0.0/16 IPs, 5 locales).

4. **Verify Installation**:
   - Check the CLI/GUI for the ASCII art banner and menu.
   - Ensure `logs/` contains a log file (e.g., `99proxys_20250805_225200.log`).

> **Note**: Ensure you have administrative privileges on Linux for network operations (`sudo` may be required).

---

## Usage

### CLI Mode
Run `python 99proxys.py --cli` to access the interactive CLI:
```
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

99Proxys Menu
1. Setup Nodes
2. Roll All Nodes
3. Roll Single Node
4. Show Stats
5. Plot Stats
6. Stop All Nodes
7. Run Setup Wizard
0. Exit
Enter choice:
```

- **Options**:
  - **1**: Initialize the proxy chain (5–99 nodes).
  - **2**: Roll IPs, MACs, and locales for all nodes.
  - **3**: Roll a single node’s IP, MAC, and locale.
  - **4**: Display a table of node stats (IP, MAC, locale, requests, latency).
  - **5**: Plot real-time latency graph in CLI.
  - **6**: Stop all nodes and clean up.
  - **7**: Run setup wizard to configure node count, IP range, and locales.
  - **0**: Exit gracefully, stopping all nodes.

### GUI Mode
Run `python 99proxys.py` to launch the GUI:
- Displays ASCII art banner, node status table, and real-time latency graph.
- Buttons: Roll All Nodes, Stop All, Setup Wizard, Exit.
- Configure via the Setup Wizard (node count, IP range, locales).

### Connecting to the VPN
1. **Find the Entry Node**:
   - The first node’s port is displayed in the CLI/GUI (e.g., `127.0.0.1:12345`).
2. **Configure a SOCKS5 Client**:
   - Set your browser or application to use a SOCKS5 proxy at `127.0.0.1:<entry_port>`.
   - Example (Firefox):
     - Settings > Network Settings > Manual Proxy Configuration
     - SOCKS Host: `127.0.0.1`, Port: `<entry_port>`, SOCKS v5
3. **Access HTTPS Sites**:
   - Visit sites like `https://httpbin.org` to verify connectivity and anonymity.

### Example Workflow
1. Run `python 99proxys.py --cli`.
2. Select option `7` to run the setup wizard.
3. Enter `99` nodes, `192.168.0.0/16` IP range, and locales (e.g., `USA,Japan,France`).
4. Select option `1` to set up the proxy chain.
5. Configure your browser to use the entry node’s port.
6. Monitor stats (option `4`) or graphs (option `5`).
7. Roll nodes (option `2` or `3`) to change IPs/MACs/locales.
8. Exit (option `0`) to shut down cleanly.

---

## Configuration

The configuration is stored in `config/99proxys_config.json`. You can edit it manually or use the setup wizard.

| Parameter | Description | Default Value |
|-----------|-------------|---------------|
| `node_count` | Number of proxy nodes (5–99) | 5 |
| `ip_range` | IP range for virtual IPs | 192.168.0.0/16 |
| `locales` | List of countries for locale simulation | ["USA", "Switzerland", "Mexico", "Canada", "Japan"] |
| `min_port` | Minimum port for nodes | 1024 |
| `max_port` | Maximum port for nodes | 65535 |
| `min_speed_kbps` | Minimum throughput (KB/s) | 56 |

### Setup Wizard
- **CLI**: Option `7` prompts for node count, IP range, and locales (comma-separated).
- **GUI**: Click "Setup Wizard" to enter values in a form.
- Example:
  ```json
  {
    "node_count": 99,
    "ip_range": "192.168.0.0/16",
    "locales": ["USA", "Japan", "France", "Germany", "Brazil"],
    "min_port": 1024,
    "max_port": 65535,
    "min_speed_kbps": 56
  }
  ```

### Supported Locales
99Proxys supports 99 countries for locale simulation, each with timezone, latitude, and longitude. Examples include:

| Country | Timezone | Latitude | Longitude |
|---------|----------|----------|-----------|
| USA | America/New_York | 40.7128 | -74.0060 |
| Japan | Asia/Tokyo | 35.6762 | 139.6503 |
| Brazil | America/Sao_Paulo | -23.5505 | -46.6333 |
| ... | ... | ... | ... |
| Fiji | Pacific/Fiji | -18.1248 | 178.4501 |

> **Tip**: See the full list in `99proxys.py` (search for `LOCALES`). Add custom locales by editing the code.

---

## Dependencies

99Proxys uses current, non-deprecated Python libraries (as of August 2025). Dependencies are installed automatically on first run.

| Package | Version | Purpose |
|---------|---------|---------|
| `scapy` | 2.5.0 | Packet manipulation for IPs/MACs |
| `rich` | 13.7.1 | Stylish CLI with colors, tables, progress bars |
| `plotext` | 5.2.8 | CLI-based graphs |
| `psutil` | 5.9.8 | System resource monitoring |
| `requests` | 2.31.0 | Testing external connectivity |
| `cryptography` | 42.0.5 | Node-to-node encryption |
| `timezonefinder` | 6.1.9 | Locale-based timezone simulation |
| `matplotlib` | 3.8.3 | GUI graphs |
| `tkinter` | Standard Library | Cross-platform GUI |

> **Note**: Ensure `pip` is updated (`pip install --upgrade pip`) for smooth installation.

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| **Port conflicts** | The program retries up to 100 times with exponential backoff. Check `logs/` for details. Increase `max_port` in config if needed. |
| **HTTPS sites not loading** | Ensure your client is configured for SOCKS5 (not HTTP) proxy. Verify the entry node’s port in CLI/GUI. |
| **High CPU/memory usage** | Setup/rolling stops if CPU/memory > 80%. Reduce `node_count` or close other applications. |
| **Dependency errors** | Run `pip install -r requirements.txt` manually or check `logs/` for errors. Ensure internet connectivity. |
| **Nodes not chaining** | Check `logs/` for connectivity test failures. Restart with option `1` or `6` then `1`. |
| **GUI not displaying** | Ensure `tkinter` is installed (`sudo apt install python3-tk` on Linux). Try CLI mode (`--cli`). |

### Logs
- Location: `logs/99proxys_<timestamp>.log`
- Contains: Node setup, port attempts, errors, stats, and chaining details.
- Example:
  ```
  2025-08-05 22:52:00 - INFO - Node started on 127.0.0.1:12345
  2025-08-05 22:52:01 - WARNING - Port 12346 in use, trying another (attempt 1/100)
  ```

### Testing Recommendations
- **HTTPS**: Configure a browser (e.g., Firefox) to use the entry node’s port and visit `https://httpbin.org`.
- **99 Nodes**: Set `node_count` to 99 in the wizard and monitor setup in CLI/GUI.
- **Port Conflicts**: Run multiple instances to test fallback behavior.
- **Resources**: Use `htop` (Linux) or Task Manager (Windows) to monitor CPU/memory.

---

## Contributing

Contributions are closed to the public at this time! To contribute: contact the BGGG on GitHub.


### Development Notes
- **Code Style**: Follow PEP 8 for Python.
- **Testing**: Test on Windows, Kali, Parrot, and Ubuntu.
- **Features**: Add new locales, enhance GUI, or improve performance.

---

## License
Proprietary Software, created by the BG Gremlin Group.

---

<p align="center">
  <strong>99Proxys - by the BG Gremlin Group</strong><br>
  Creating Unique Tools for Unique Individuals
</p>
```

---

### Notes for Testers
- **HTTPS Testing**: Verify HTTPS sites load correctly using a SOCKS5 client (e.g., Firefox, `curl --socks5 127.0.0.1:<port>`).
- **99 Nodes**: Test with `node_count=99` to confirm stability and chaining.
- **Logs**: Check `logs/` for detailed error messages if issues arise.
- **Feedback**: Report any UI issues, performance bottlenecks, or missing features to refine the tool.
