# 🛠️ Postbox Scripts - Installation & Auto-Update Guide

This guide explains how to install and keep the Postbox Scripts for Cinema 4D up to date using Git. Ideal for artists working with V-Ray and C4D utilities.

---

## 🚀 Initial Setup (One-time)

### 🔧 Requirements
- Git installed
- Python 3.x installed
- Cinema 4D R20 or later

---

### 📥 Step 1: Clone the Repository

Open Terminal (macOS/Linux) or Command Prompt (Windows):

```bash
git clone https://github.com/ernyeizoli/postbox_scripts.git ~/postbox_scripts
cd ~/postbox_scripts
python c4d_installer.py
```

---

### 🔄 Step 2: Update the Scripts

To update the scripts to the latest version, run the following commands in Terminal (macOS/Linux) or Command Prompt (Windows):
(open a terminal in the folder of the scripts)

```bash
cd ~/postbox_scripts
git pull
python c4d_installer.py
```

This will fetch the latest changes from the repository and re-run the installer to apply updates.


