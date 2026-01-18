# 🚀 Houdini Render Copilot (AuraTech Dashboard)

A batch render manager designed for SideFX Houdini. Automate your rendering queue with style and real-time performance monitoring.

![Houdini Render Copilot UI](https://github.com/USER/REPO/raw/main/screenshot.png) *(Replace with your image URL)*

## ✨ Key Features

- **💎 AuraTech UI**: A premium, glassmorphic dark-themed dashboard built with PySide6.
- **📁 Multi-Project Support**: Load multiple `.hip` files simultaneously and scan for render nodes across all of them.
- **🖥️ Smart Node Selection**: Checkbox-based selection for ROP/LOP nodes (Supports Mantra, Redshift, Arnold, Karma, and USD Render).
- **🔄 Intelligent Resume**: Automatic detection of existing frames to skip redundant rendering (Full USD RenderProduct support).
- **📊 Performance Dashboard**: Real-time tracking of CPU, RAM, and NVIDIA GPU utilization during rendering.
- **🌐 Localization**: Full support for English and Simplified Chinese.

## 🛠️ Installation

### Prerequisites
- **Houdini**: SideFX Houdini (19.5, 20.0, or 20.5 recommended).
- **Python 3.9+**: If running from source (Conda environment recommended).

### From Standalone EXE (Recommend)
1. Download the latest `HoudiniRenderCopilot.exe` from the [Releases](https://github.com/USER/REPO/releases) page.
2. Run the EXE.
3. Open **Settings (⚙)** and set your `hython.exe` path.

### From Source
```bash
git clone https://github.com/USER/REPO.git
cd Houdini-Render-Copilot
pip install PySide6 psutil
python HoudiniRenderManager.py
```

## 📦 Deployment
To package the app into a standalone executable:
1. Open a Conda Prompt.
2. Run the provided build script:
```bash
package_app.bat
```

## 🤝 Contributing
Contributions are welcome! Please feel free to submi a Pull Request.

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
