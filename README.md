# ⚡ PyHub
### Full-Throttle GitHub Deployment Tool — No CLI. No Commands. Just Push.

> **Author:** Vedant Sareen (CYBERSAREEN)  
> **Contact:** securecybernetics@gmail.com  
> **GitHub:** [github.com/CYBERSAREEN](https://github.com/CYBERSAREEN)

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![GUI](https://img.shields.io/badge/GUI-CustomTkinter-purple)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20MacOS-lightgrey)
![License](https://img.shields.io/badge/License-MIT-orange)

---

## 📥 Download

Just two files. That's it.

| File | Description |
|------|-------------|
| `pyhub.py` | The tool itself |
| `README.md` | This file |

---

## ⚠️ BEFORE YOU RUN — Do This First

### Step 1 — Open `pyhub.py` in any text editor

Find this line **(around line 40)**:

```python
self.username = ctk.StringVar(value="ENTER YOUR PROFILE NAME")
```

**Change it to your actual GitHub username:**

```python
self.username = ctk.StringVar(value="YourGitHubUsername")
```

> That's the **only change** needed in the script. Save the file and you're good.

---

### Step 2 — Install the required module

Open your terminal or command prompt and run:

```bash
pip install customtkinter
```

> Everything else — `subprocess`, `tkinter`, `threading`, `os` — is already built into Python. No extra installs needed.

---

### Step 3 — Run it

```bash
python pyhub.py
```

**The GUI opens. You're ready to deploy.**

---

## 🚀 How to Deploy a Project

1. Click **Browse** → select your project folder
2. Enter your **Repository Name** (must already exist on github.com)
3. Set your **Branch** (default: `main`)
4. Write your **Commit Message**
5. Check / uncheck files you want to include
6. Pick a `.gitignore` preset if needed
7. Click **🚀 DEPLOY TO GITHUB**
8. Confirm the dialog → watch the live terminal

PyHub runs all 7 Git steps automatically:

```
Step 1/7  →  Write .gitignore (if enabled)
Step 2/7  →  git init
Step 3/7  →  git remote set-url origin https://github.com/YOU/REPO.git
Step 4/7  →  git add <your selected files>
Step 5/7  →  git commit -m "your message"
Step 6/7  →  git branch -M main
Step 7/7  →  git push -u origin main
```

---

## 🔐 First Push — Credentials

When PyHub pushes for the first time, Git will ask for login:

| Field | What to enter |
|-------|--------------|
| Username | Your GitHub username |
| Password | Your **Personal Access Token** ← NOT your GitHub password |

**To generate a Personal Access Token:**

```
GitHub → Settings → Developer Settings
→ Personal Access Tokens → Tokens (classic)
→ New Token → select "repo" scope → Generate
```

> **To avoid entering it every time**, run this once:
> ```bash
> git config --global credential.helper store
> ```

---

## 📦 Requirements

```
Python 3.8+
customtkinter
```

Install:
```bash
pip install customtkinter
```

---

## 🛠️ Quick Actions (Inside the App)

| Button | What it runs |
|--------|-------------|
| `git status` | Shows current repo state |
| `git log` | Shows last 5 commits |
| `git pull` | Pulls latest from remote |

---

## 📄 .gitignore Presets

| Preset | Best For |
|--------|---------|
| **Python** | Python projects, venvs, build files |
| **Node.js** | JS/TS projects, node_modules |
| **Web** | HTML/CSS/JS static sites |
| **Kali/Security** | Pentest folders, pcaps, loot, logs |
| **Custom** | Blank — write your own rules |

---

## 📜 License

MIT License — free to use, modify, and distribute.

---

<p align="center">
  <b>⚡ PyHub — because typing git commands manually is a crime.</b><br>
  <i>Built by CYBERSAREEN</i>
</p>
