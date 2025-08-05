# 99Proxys Changelog
**BG Gremlin Group - Proprietary Software**  
*Last Updated: August 05, 2025, 11:44 PM CEST*

This changelog documents the development history of 99Proxys, a local virtual VPN network designed by the BG Gremlin Group. All rights reserved.

## Current - August 05, 2025
- **Added**: Created GitHub Repo
- **Added**: Readme notes for `99proxys.py`, testers.
- **Added**: Changelog
  
## [0.3.0] - August 05, 2025
- **Added**: Comprehensive Python implementation of 99Proxys with:
  - Full SOCKS5 support for HTTPS websites via `CONNECT` method, preserving end-to-end encryption.
  - Enhanced port handling with up to 100 retry attempts and exponential backoff for conflicts.
  - Validation of node chaining and binding, with reverse-order startup for exit node priority.
  - Resource monitoring using `psutil` to prevent CPU/memory overload (>80%).
  - CLI and GUI modes with real-time latency graphs (`plotext` and `matplotlib`) and stats tracking.
  - Support for 5–99 nodes with rolling IPs, MACs, and 99 locale simulations.
- **Added**: Verbose README in Markdown with tables (features, config, dependencies, troubleshooting), stylish layout, and professional tone.
- **Improved**: Robust error handling for port conflicts, network issues, and system limits, with detailed logging to `logs/`.
- **Initial Release to Testers**: Prepared for BG Gremlin Group testers with setup instructions and testing recommendations.

## [0.2.0] - August 05, 2025 (Estimated)
- **Added**: Expanded proxy chain functionality with:
  - Configurable node count (5–99) and locale simulation for 99 countries (e.g., USA, Japan, Brazil).
  - Basic IP and MAC address rolling with virtual network simulation.
  - Interactive CLI with ASCII art, progress bars, and basic stats display.
  - Initial GUI prototype using `tkinter` with node status table.
- **Added**: Automated dependency installation and folder creation (`config/`, `logs/`, `data/`, `assets/`).
- **Improved**: Enhanced node setup with random port selection and basic chaining logic.
- **Fixed**: Initial issues with port binding and node connectivity during setup.

## [0.1.0] - August 05, 2025
- **Added**: Initial concept of a local virtual VPN mimicking a private Tor network.
  - Basic proxy node structure with manual port assignment.
  - Placeholder for 5–10 nodes with static IP and locale settings.
  - Preliminary CLI interface with minimal functionality.
- **Planned**: Outline for HTTPS support, rolling IPs/MACs, and cross-platform compatibility.
- **Created**: First draft submitted to DevOps for development, focusing on anonymity for user.

## [0.0.1] - August 05, 2025
- **Created**: Initial idea.
- **Planned**: Vision for a proprietary tool with configurable proxy nodes and privacy-focused design for the BG Gremlin Group.

---

### Notes
- **Versioning**: Internal milestones for the BG Gremlin Group, not publicly released. Dates are for early iterations based on timeline.
- **Proprietary**: All code, designs, and documentation are confidential to the BG Gremlin Group. Unauthorized use is prohibited.
- **Contact**: [https://github.com/BGGremlin-Group] for inquiries or feedback.
- **Testing**: Testers should refer to the README for setup, usage, and troubleshooting details.
