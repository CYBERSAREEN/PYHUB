# ⚡ PyHub v2.0
### Full-Throttle GitHub Deployment Tool — No CLI. No Commands. Just Push.

> **Author:** Vedant Sareen (CYBERSAREEN)  
> **Contact:** securecybernetics@gmail.com  
> **GitHub:** [github.com/CYBERSAREEN](https://github.com/CYBERSAREEN)

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![GUI](https://img.shields.io/badge/GUI-CustomTkinter-purple)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20MacOS-lightgrey)
![License](https://img.shields.io/badge/License-MIT-orange)
![Version](https://img.shields.io/badge/Version-2.0-00FF88)

---

## 🆕 What's New in v2.0

| Feature | v1.0 | v2.0 |
|---|---|---|
| Splash / Loading Screen | ❌ | ✅ Animated on every launch |
| Git Install Detection | ❌ | ✅ Auto-detects, guides install |
| Git Setup Wizard | ❌ | ✅ Name, email, PAT walkthrough |
| Auto-fill identity from system | ❌ | ✅ Reads `git config --global` |
| Push Conflict Resolver | ❌ | ✅ Merge / Rebase / Force dialog |
| Auth error handling | ❌ | ✅ Opens PAT page automatically |
| Repo-not-found handling | ❌ | ✅ Opens github.com/new |
| SSL / network error handling | ❌ | ✅ Guided tips |
| Large file rejection handling | ❌ | ✅ Clear message + fix tip |
| Hardcoded username | ⚠️ Manual edit needed | ✅ Auto-detected, fully generic |
| EXE-ready | ⚠️ Partial | ✅ PyInstaller compatible |
| Font size | Small | ✅ Larger, easier to read |
| Quick Actions | 3 buttons | ✅ 5 buttons incl. Git Wizard |
| Deploy steps | 7 | ✅ 8 (identity verification added) |

---

## 📥 Download

Just two files. That's it.

| File | Description |
|------|-------------|
| `pyhub.py` | The tool itself |
| `README.md` | This file |

---

## ⚙️ Requirements

```
Python 3.8+
customtkinter
```

Install the only external dependency:

```bash
pip install customtkinter
```

> Everything else — `subprocess`, `tkinter`, `threading`, `os` — is already built into Python.

---

## ▶️ Run It

```bash
python pyhub.py
```

**The splash screen appears → app boots → you're ready to deploy.**

> **v2.0 no longer requires you to manually edit the script.**  
> PyHub reads your Git identity automatically on launch. If nothing is configured, the Setup Wizard walks you through it step by step.

---

## 🔧 First Launch — Setup Wizard

When PyHub opens it checks your system automatically:

### If Git is NOT installed
A wizard opens with a one-click link to download Git for your OS. After installing, click **Re-check** inside the wizard — PyHub detects it instantly.

### If Git IS installed but identity is missing
The wizard prompts you to enter:
- Your full name (used in commit history)
- Your GitHub email

Click **Save Identity** — PyHub writes both to `git config --global`. Done forever.

### PAT (Personal Access Token)
The wizard includes a direct button to generate a GitHub PAT with the correct `repo` scope pre-selected. When Git asks for a password during push, paste your PAT.

> **To avoid re-entering your PAT on every push**, run this once in your terminal:
> ```bash
> git config --global credential.helper store
> ```

---

## 🚀 How to Deploy a Project

1. Click **Browse** → select your project folder
2. PyHub auto-fills the repo name from the folder name
3. Confirm your **GitHub Username** and **Repository Name**
4. Set your **Branch** (default: `main`)
5. Write your **Commit Message**
6. Check / uncheck files to include
7. Pick a `.gitignore` preset if needed
8. Click **🚀 DEPLOY TO GITHUB**
9. Confirm the dialog → watch the live terminal output

PyHub runs all 8 steps automatically:

```
Step 1/8  →  Write .gitignore (if enabled)
Step 2/8  →  Verify Git is installed
Step 3/8  →  git init (skipped if already initialised)
Step 4/8  →  Verify / set git identity
Step 5/8  →  git remote add origin https://github.com/YOU/REPO.git
Step 6/8  →  git add <your selected files>
Step 7/8  →  git commit -m "your message"
Step 8/8  →  git push -u origin <branch>  ← with smart conflict resolution
```

---

## ⚠️ Smart Conflict Resolution (v2.0)

When a push is rejected because the remote has commits your local copy doesn't have, PyHub opens an interactive dialog instead of just failing:

| Option | What it does |
|---|---|
| 🔄 Pull & Merge then Push | Fetches remote changes and merges. Safest — preserves both histories. |
| 📥 Pull with Rebase then Push | Reapplies your commits on top of remote. Clean linear history. |
| ♻️ Force Push | Your local files overwrite the remote. Remote commits will be lost. |

PyHub also auto-handles these common errors without you doing anything:

| Error | PyHub's Response |
|---|---|
| Auth failure (401/403) | Shows PAT instructions + opens GitHub token page |
| Repository not found | Shows tip + opens github.com/new in browser |
| SSL / network error | Displays proxy configuration instructions |
| Large file rejection | Identifies the issue and advises adding to `.gitignore` |
| No upstream branch | Sets `--set-upstream` automatically and retries |
| Nothing to commit | Skips commit step silently and attempts push anyway |

---

## 🛠️ Quick Actions (Inside the App)

| Button | What it runs |
|--------|-------------|
| `git status` | Shows current repo state |
| `git log` | Shows last 8 commits (oneline) |
| `git pull` | Pulls latest from remote |
| `🔧 Git Wizard` | Re-opens the Setup Wizard at any time |
| `🌐 Open GitHub` | Opens your repo page in the browser |

---

## 📄 .gitignore Presets

| Preset | Best For |
|--------|---------|
| **Python** | Python projects, venvs, build files |
| **Node.js** | JS/TS projects, node_modules |
| **Web** | HTML/CSS/JS static sites |
| **Kali/Security** | Pentest folders, pcaps, loot, logs, keys |
| **Java** | Maven/Gradle projects, .class files |
| **C/C++** | Object files, build dirs, binaries |
| **Go** | Vendor dirs, compiled binaries |
| **Rust** | Target dir, Cargo.lock |
| **Custom** | Blank — write your own rules |

---

## 📦 Build as EXE (Windows)

To distribute PyHub as a standalone `.exe` — no Python needed on the target machine:

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "PyHub" pyhub.py
```

With a custom icon:
```bash
pyinstaller --onefile --windowed --icon=icon.ico --name "PyHub" pyhub.py
```

Your EXE lands in the `dist/` folder. Share it with anyone.

---

## 📜 License

MIT License — free to use, modify, and distribute.

---

<p align="center">
  <b>⚡ PyHub v2.0 — because typing git commands manually is a crime.</b><br>
  <i>Built by CYBERSAREEN</i>
</p>
