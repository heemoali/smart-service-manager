# Smart Service Manager

A modern desktop application to safely manage Windows services and improve system performance and privacy.

![Python](https://img.shields.io/badge/Python-3.13-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Platform](https://img.shields.io/badge/Platform-Windows-blue)

## Features

- Modern dark and light theme with a clean interface
- 50 Windows services with descriptions
- Enable or disable services with a single toggle
- One-click "Apply Recommended" button to disable unnecessary services
- Real-time statistics dashboard
- Persistent user settings
- Administrator privilege detection and warnings
- Standalone executable (no Python installation required)

## Download

Get the latest standalone `.exe` from the [Releases page](https://github.com/heemoali/smart-service-manager/releases).

1. Download `SmartServiceManager.exe`
2. Right-click the file and choose **Run as administrator**
3. No installation required

## Run from Source

```bash
git clone https://github.com/heemoali/smart-service-manager.git
cd smart-service-manager
pip install -r requirements.txt
python main.py