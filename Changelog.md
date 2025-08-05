# 99Proxys Changelog
**BG Gremlin Group - Proprietary Software**  
**Last Updated: August 06, 2025, 01:46 AM CEST**

This changelog documents the development history of 99Proxys, a local virtual VPN network designed by the BG Gremlin Group. All rights reserved.

## [3.5.0] - August 06, 2025
### Key Features and Improvements
- **Implemented `scapy` for Virtual IP Assignment**: Added `assign_virtual_ip` method in `ProxyNode` to assign virtual IPs to network interfaces using `scapy`, ensuring realistic network simulation.
- **Enhanced Error Handling in `ProxyNode.tunnel`**: Added specific exception handling for socket and SSL errors with proper socket cleanup to improve reliability.
- **Added Missing `webbrowser` Import**: Included `webbrowser` import to support opening the WYSIWYG editor in the default browser.
- **Improved Tor Configuration**: Added validation for the Tor executable path and robust error handling for process failures, ensuring stable hidden service creation.
- **Added Input Validation in Flask Routes**: Implemented `secure_filename` and validation for all user inputs in Flask routes to prevent security vulnerabilities like path traversal.
- **Implemented Bandwidth Throttling with Token Bucket**: Added a token bucket algorithm in `ProxyNode` for precise bandwidth control, configurable via `max_bandwidth_kbps`.
- **Added Review System**: Implemented a fully functional review system with Flask routes (`/reviews`, `/submit_review`, `/get_reviews`) and a database model (`Review`) for user feedback on websites.
- **Added Locale Simulation with Timezones**: Integrated `timezonefinder` and `pytz` for locale-specific timestamps in `ProxyNode.get_local_time`, supporting all 99 locales.
- **Enhanced Configuration Validation**: Added comprehensive validation for all configuration parameters (e.g., `node_count`, `ip_range`, `min_port`, `max_port`, `rate_limit`) with fallback to defaults.
- **Added Comprehensive Documentation**: Included detailed docstrings for all classes (`ProxyNode`, `ProxyChain`, `ProxyGUI`, database models) and methods, improving code maintainability.
- **Improved Resource Cleanup**: Added proper cleanup of database sessions, temporary files, and directories in `ProxyChain.stop` to prevent resource leaks.
- **Updated Version to 3.5**: Changed all version references to 3.5.0 across the codebase and documentation.
- **Added Testing Framework**: Implemented a `unittest`-based test suite in `tests/test_proxy.py` covering node initialization, website creation, reviews, chat, virtual IP assignment, and bandwidth throttling.
- **Added CSRF Protection**: Integrated `flask_wtf` for CSRF protection in Flask forms, enhancing security for website reviews and editor updates.
- **Implemented Basic User Authentication**: Added input sanitization for chat and review submissions, with plans for full authentication in future releases.
- **Created Documentation Stub**: Added `create_documentation` function to generate a `README.md` in `docs/` with setup, usage, and troubleshooting instructions.
- **Improved Performance**: Optimized socket handling with connection pooling hints (commented for external configuration) and efficient threading for node and web server management.
- **Enhanced GUI**: Added real-time website list updates and improved stats visualization with `matplotlib` for latency and bandwidth graphs.
- **Fixed Locale List**: Ensured the `LOCALES` list contains 99 unique entries with correct timezone, latitude, longitude, and `ip_prefix` for realistic simulation.
- **Improved Logging**: Added detailed logging for all operations, including node health checks, website creation, and errors, stored in `logs/`.
- **Added Support for Multi-Page Websites**: Enhanced `ProxyChain.create_website` to support multiple pages with individual HTML, CSS, and JavaScript assets.
- **Improved WYSIWYG Editor**: Added a fully functional WYSIWYG editor with Ace editor integration, supporting real-time HTML editing and preview for website pages.
- **Added Chatroom Functionality**: Implemented real-time chatrooms for each website using `flask_socketio`, with persistent storage in the `ChatMessage` model.

### Bug Fixes
- Fixed missing `scapy` import and usage for virtual IP assignment.
- Fixed incomplete error handling in `ProxyNode.tunnel` by adding specific exception types and cleanup.
- Fixed missing `webbrowser` import in `ProxyGUI.open_wysiwyg`.
- Fixed potential security issues in Flask routes by adding input validation and CSRF protection.
- Fixed resource leaks by ensuring proper cleanup of database sessions and temporary files.
- Fixed Tor process failures by adding validation and error handling for hidden service creation.

## [2.0.0] - August 06, 2025
### Key Features and Improvements
- **Corrected LOCALES**: Fixed typos and removed the incomplete entry. Added `ip_prefix` for each locale to simulate realistic IP ranges.
- **Added SSL/TLS Support**: Added self-signed certificate generation and SSL wrapping for SOCKS5 servers, ensuring secure communication.
- **Added RSA Encryption**: Implemented RSA key exchange for secure Fernet key transmission between nodes.
- **Added Bandwidth Throttling**: Added dynamic bandwidth control based on configuration and system resources.
- **Added Rate Limiting**: Implemented per-node rate limiting to prevent abuse.
- **Added Health Monitoring**: Added a health check thread for each node to monitor and restart failed nodes.
- **Enhanced Statistics**: Expanded stats to include errors, connection time, and bandwidth usage.
- **Added GUI Enhancements**: Added individual node controls, bandwidth graphs, and export stats functionality.
- **Added CLI Enhancements**: Added commands for stopping individual nodes and exporting stats.
- **Added Configuration Validation**: Added robust validation for IP ranges and port ranges.
- **Added Thread Safety**: Used locks for thread-safe stats updates.
- **Enhanced Cross-Platform Compatibility**: Ensured compatibility with different operating systems by using standard libraries and handling platform-specific issues.
- **Improved Error Handling**: Improved with specific exception types and recovery mechanisms.
- **Added Documentation**: Added detailed inline comments for clarity.
- **Enhanced Performance Optimization**: Optimized socket handling and threading for better performance.

## [1.0.0] - August 05, 2025
### Key Features
- **Added**: Created GitHub repository.
- **Added**: README notes for `99proxys.py`, testers.
- **Added**: Initial changelog.

## [0.3.0] - August 05, 2025
### Key Features
- **Added**: Comprehensive Python implementation of 99Proxys with:
  - Full SOCKS5 support for HTTPS websites via CONNECT method, preserving end-to-end encryption.
  - Enhanced port handling with up to 100 retry attempts and exponential backoff for conflicts.
  - Validation of node chaining and binding, with reverse-order startup for exit node priority.
  - Resource monitoring using `psutil` to prevent CPU/memory overload (>80%).
  - CLI and GUI modes with real-time latency graphs (`plotext` and `matplotlib`) and stats tracking.
  - Support for 5–99 nodes with rolling IPs, MACs, and 99 locale simulations.
- **Added**: Verbose README in Markdown with tables (features, config, dependencies, troubleshooting), stylish layout, and professional tone.
- **Improved**: Robust error handling for port conflicts, network issues, and system limits, with detailed logging to `logs/`.
- **Initial Release to Testers**: Prepared for BG Gremlin Group testers with setup instructions and testing recommendations.

## [0.2.0] - August 05, 2025 (Estimated)
### Key Features
- **Added**: Expanded proxy chain functionality with:
  - Configurable node count (5–99) and locale simulation for 99 countries (e.g., USA, Japan, Brazil).
  - Basic IP and MAC address rolling with virtual network simulation.
  - Interactive CLI with ASCII art, progress bars, and basic stats display.
  - Initial GUI prototype using `tkinter` with node status table.
- **Added**: Automated dependency installation and folder creation (`config/`, `logs/`, `data/`, `assets/`).
- **Improved**: Enhanced node setup with random port selection and basic chaining logic.
- **Fixed**: Initial issues with port binding and node connectivity during setup.

## [0.1.0] - August 05, 2025
### Key Features
- **Added**: Initial concept of a local virtual VPN mimicking a private Tor network.
- **Added**: Basic proxy node structure with manual port assignment.
- **Added**: Placeholder for 5–10 nodes with static IP and locale settings.
- **Added**: Preliminary CLI interface with minimal functionality.
- **Planned**: Outline for HTTPS support, rolling IPs/MACs, and cross-platform compatibility.
- **Created**: First draft submitted to DevOps for development, focusing on anonymity for users.

## [0.0.1] - August 05, 2025
### Key Features
- **Created**: Initial idea.
- **Planned**: Vision for a proprietary tool with configurable proxy nodes and privacy-focused design for the BG Gremlin Group.

## Notes
- **Versioning**: Internal milestones for the BG Gremlin Group, not publicly released. Dates are for early iterations based on timeline.
- **Proprietary**: All code, designs, and documentation are confidential to the BG Gremlin Group. Unauthorized use is prohibited.
- **Contact**: [https://github.com/BGGremlin-Group](https://github.com/BGGremlin-Group) for inquiries or feedback.
- **Testing**: Testers should refer to the README for setup, usage, and troubleshooting details.
