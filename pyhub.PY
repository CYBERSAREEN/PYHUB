"""
╔══════════════════════════════════════════════════════════════╗
║          DeployPro  ·  GitHub + Vercel Deployment Suite      ║
║          v3.0  ·  By CYBERSAREEN                             ║
╚══════════════════════════════════════════════════════════════╝

Features:
  • Full environment health check (git, gh CLI, vercel CLI, node/npm)
  • GitHub: browse, file select, .gitignore, create repo via gh CLI,
            auto README.md, commit, push, merge/rebase/force conflict handling
  • Vercel: project creation, deployment, preview vs production mode
  • Professional dark UI — slate-black + electric-blue + violet palette

Requirements:
    pip install customtkinter pillow

Optional CLI tools (detected automatically):
    gh      — GitHub CLI  (https://cli.github.com)
    vercel  — Vercel CLI  (npm i -g vercel)
    node    — Node.js     (https://nodejs.org)

Build EXE:
    pyinstaller --onefile --windowed --icon=icon.ico deploy_pro.py
"""

import customtkinter as ctk
import subprocess, threading, os, sys, time, shutil, webbrowser, json, re
import urllib.request, zipfile, tarfile, tempfile
from tkinter import filedialog, messagebox
import tkinter as tk

# ═══════════════════════════════════════════════════════════════
#  PRIVATE LOCAL ENV CONFIGURATION & CLI ARGS
# ═══════════════════════════════════════════════════════════════
AUTO_INSTALL_CLI = "-y" in sys.argv or "--yes" in sys.argv or "--auto-install" in sys.argv

LOCAL_ENV_DIR = os.path.expanduser(os.path.join("~", ".deploypro", "env"))
LOCAL_NODE_DIR = os.path.join(LOCAL_ENV_DIR, "node")
LOCAL_GH_DIR = os.path.join(LOCAL_ENV_DIR, "gh")

# Prepend local paths so `cmd_available` and `run_cmd` use them
local_paths = []
if os.path.isdir(LOCAL_NODE_DIR):
    local_paths.append(LOCAL_NODE_DIR)
if os.path.isdir(os.path.join(LOCAL_GH_DIR, "bin")):
    local_paths.append(os.path.join(LOCAL_GH_DIR, "bin"))

if local_paths:
    os.environ["PATH"] = os.pathsep.join(local_paths) + os.pathsep + os.environ.get("PATH", "")


# ═══════════════════════════════════════════════════════════════
#  THEME  —  Slate-Black · Electric-Blue · Violet
# ═══════════════════════════════════════════════════════════════
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# Backgrounds
BG_VOID   = "#060810"   # deepest background
BG_BASE   = "#0A0D18"   # base surface
BG_CARD   = "#0F1220"   # card surface
BG_PANEL  = "#141828"   # panel / raised
BG_HOVER  = "#1A2035"   # hover / selected
BG_INPUT  = "#080B15"   # input fields

# Borders
BORDER_DIM  = "#1C2235"
BORDER_MID  = "#252B45"
BORDER_HI   = "#2E3755"

# Brand colours
BLUE        = "#3B82F6"   # primary blue
BLUE_HI     = "#60A5FA"   # lighter blue
BLUE_DIM    = "#1D4ED8"   # deeper blue
VIOLET      = "#7C3AED"   # primary violet
VIOLET_HI   = "#A78BFA"   # lighter violet
VIOLET_DIM  = "#5B21B6"   # deeper violet
CYAN        = "#06B6D4"   # accent cyan
GREEN       = "#10B981"   # success
GREEN_DIM   = "#059669"
RED         = "#EF4444"   # error
RED_DIM     = "#DC2626"
YELLOW      = "#F59E0B"   # warning
ORANGE      = "#F97316"

# Text
TEXT_HI     = "#EEF2FF"   # primary text
TEXT_MID    = "#94A3B8"   # secondary
TEXT_DIM    = "#475569"   # muted
TEXT_GHOST  = "#2D3755"   # ghost/placeholder

# Fonts
F_MONO      = ("JetBrains Mono", 13) if sys.platform == "win32" else ("Courier New", 13)
F_MONO_SM   = ("JetBrains Mono", 11) if sys.platform == "win32" else ("Courier New", 11)
F_MONO_LG   = ("JetBrains Mono", 15, "bold") if sys.platform == "win32" else ("Courier New", 15, "bold")
F_MONO_H    = ("JetBrains Mono", 22, "bold") if sys.platform == "win32" else ("Courier New", 22, "bold")
F_UI        = ("Segoe UI", 13) if sys.platform == "win32" else ("Helvetica Neue", 13)
F_UI_SM     = ("Segoe UI", 11) if sys.platform == "win32" else ("Helvetica Neue", 11)
F_UI_LG     = ("Segoe UI", 14, "bold") if sys.platform == "win32" else ("Helvetica Neue", 14, "bold")
F_LABEL     = F_MONO_SM
F_FIELD     = F_MONO

GITIGNORE_PRESETS = {
    "Python":        ["__pycache__/","*.pyc","*.pyo",".env","venv/",".venv/","dist/","build/","*.egg-info/","*.dist-info/","*.pytest_cache/",".mypy_cache/",".ruff_cache/"],
    "Node.js":       ["node_modules/",".env","dist/","build/",".DS_Store","*.log","package-lock.json",".next/",".nuxt/","out/","coverage/",".cache/"],
    "Next.js":       ["node_modules/",".next/","out/","dist/","build/",".env","*.log",".DS_Store",".vercel/","coverage/",".cache/"],
    "React":         ["node_modules/","dist/","build/",".env","*.log",".DS_Store","coverage/",".cache/"],
    "Web":           [".DS_Store","*.log",".env","dist/","build/","coverage/"],
    "Kali/Security": ["*.log","*.pcap","*.cap","credentials.txt","passwords.txt","*.key",".env","loot/","output/","*.hash","wordlists/"],
    "Java":          ["target/","*.class","*.jar","*.war",".gradle/","build/",".idea/","*.iml"],
    "C/C++":         ["*.o","*.obj","*.exe","*.out","*.a","*.so","build/","CMakeFiles/","cmake-build-*/"],
    "Go":            ["*.exe","vendor/","bin/","*.test","coverage.out"],
    "Rust":          ["target/","Cargo.lock","*.rs.bk"],
    "Flutter/Dart":  [".dart_tool/","build/",".flutter-plugins","*.g.dart","pubspec.lock"],
    "Custom":        [],
}

# ═══════════════════════════════════════════════════════════════
#  CORE HELPERS
# ═══════════════════════════════════════════════════════════════
def run_cmd(cmd, cwd=None, timeout=90):
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True,
                           text=True, shell=True, timeout=timeout)
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out."
    except Exception as e:
        return -1, "", str(e)

def cmd_available(name):
    local_bins = {
        "vercel": os.path.join(LOCAL_NODE_DIR, "vercel.cmd"),
        "gh":     os.path.join(LOCAL_GH_DIR, "bin", "gh.exe"),
        "node":   os.path.join(LOCAL_NODE_DIR, "node.exe"),
        "npm":    os.path.join(LOCAL_NODE_DIR, "npm.cmd")
    }
    if name in local_bins and os.path.exists(local_bins[name]):
        code, out, err = run_cmd(f'"{local_bins[name]}" --version')
        if code == 0:
            return True, (out or err).strip()
            
    code, out, err = run_cmd(f"{name} --version")
    return code == 0, (out or err).strip()

def git_global(key):
    _, out, _ = run_cmd(f"git config --global {key}")
    return out.strip()

def gh_logged_in():
    code, out, err = run_cmd("gh auth status")
    return code == 0

def vercel_logged_in():
    code, out, err = run_cmd("vercel whoami")
    return code == 0, out.strip()

def node_version():
    ok, out = cmd_available("node")
    return out if ok else None

def npm_version():
    ok, out = cmd_available("npm")
    return out if ok else None


# ═══════════════════════════════════════════════════════════════
#  SPLASH SCREEN
# ═══════════════════════════════════════════════════════════════
class SplashScreen(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.overrideredirect(True)
        self.configure(fg_color=BG_VOID)
        self.geometry("560x380")
        self._center()
        self.lift()
        self.attributes("-topmost", True)
        self._build()

    def _center(self):
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"560x380+{(sw-560)//2}+{(sh-380)//2}")

    def _build(self):
        # Top glow bar
        bar = ctk.CTkFrame(self, fg_color=BLUE, height=3, corner_radius=0)
        bar.pack(fill="x")

        ctk.CTkLabel(self, text="◈", font=("Segoe UI Emoji", 52),
                     text_color=VIOLET).pack(pady=(36, 4))
        ctk.CTkLabel(self, text="DeployPro",
                     font=F_MONO_H, text_color=TEXT_HI).pack()
        ctk.CTkLabel(self, text="GitHub  ·  Vercel  ·  Deployment Suite",
                     font=F_MONO_SM, text_color=TEXT_DIM).pack(pady=(4, 28))

        self.pb = ctk.CTkProgressBar(self, width=420, height=6,
                                      fg_color=BG_PANEL,
                                      progress_color=BLUE)
        self.pb.pack()
        self.pb.set(0)

        self.lbl = ctk.CTkLabel(self, text="Initialising…",
                                 font=F_MONO_SM, text_color=TEXT_DIM)
        self.lbl.pack(pady=(10, 0))

        ctk.CTkLabel(self, text="v3.0  ·  CYBERSAREEN",
                     font=F_MONO_SM, text_color=TEXT_GHOST
                     ).pack(side="bottom", pady=18)

    def set_progress(self, val, text=""):
        self.pb.set(val)
        if text:
            self.lbl.configure(text=text)
        self.update()


# ═══════════════════════════════════════════════════════════════
#  ENVIRONMENT CHECK PANEL (modal)
# ═══════════════════════════════════════════════════════════════
class EnvCheckDialog(ctk.CTkToplevel):
    def __init__(self, parent, env_data):
        super().__init__(parent)
        self.title("Environment Check — DeployPro")
        self.geometry("620x560")
        self.resizable(False, False)
        self.configure(fg_color=BG_VOID)
        self.grab_set()
        self._center()
        self._build(env_data)

    def _center(self):
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"620x560+{(sw-620)//2}+{(sh-560)//2}")

    def _build(self, env):
        # Header
        hdr = ctk.CTkFrame(self, fg_color=VIOLET_DIM, height=3, corner_radius=0)
        hdr.pack(fill="x")

        ctk.CTkLabel(self, text="⬡  Environment Health Check",
                     font=F_MONO_LG, text_color=VIOLET_HI).pack(pady=(20, 4))
        ctk.CTkLabel(self,
                     text="All tools detected on your system. Missing tools are optional\n"
                          "unless you plan to use their feature.",
                     font=F_UI_SM, text_color=TEXT_MID, justify="center"
                     ).pack(pady=(0, 16))

        scroll = ctk.CTkScrollableFrame(self, fg_color=BG_CARD,
                                         corner_radius=10,
                                         border_color=BORDER_MID, border_width=1)
        scroll.pack(fill="both", expand=True, padx=24, pady=(0, 16))

        checks = [
            ("git",             "Git VCS",          env.get("git"),    "Required for all deployment",  "https://git-scm.com/downloads"),
            ("gh",              "GitHub CLI",        env.get("gh"),     "Create repos, manage GitHub",  "https://cli.github.com"),
            ("vercel",          "Vercel CLI",        env.get("vercel"), "Deploy to Vercel",             "https://vercel.com/docs/cli"),
            ("node",            "Node.js",           env.get("node"),   "Required for Next.js/React",   "https://nodejs.org"),
            ("npm",             "npm",               env.get("npm"),    "Package manager",              "https://nodejs.org"),
            ("git_user",        "Git Name",          env.get("git_name"), "Commit identity",            None),
            ("git_email",       "Git Email",         env.get("git_email"), "Commit identity",           None),
            ("gh_auth",         "GitHub Auth",       env.get("gh_auth"), "Logged in to GitHub CLI",     "https://cli.github.com/manual/gh_auth_login"),
            ("vercel_auth",     "Vercel Auth",       env.get("vercel_auth"), "Logged in to Vercel CLI", "https://vercel.com/docs/cli#commands/login"),
        ]

        for key, label, val, desc, url in checks:
            row = ctk.CTkFrame(scroll, fg_color=BG_PANEL,
                               corner_radius=8, border_color=BORDER_DIM, border_width=1)
            row.pack(fill="x", pady=3, padx=6)

            # Status dot
            ok = bool(val)
            dot_color = GREEN if ok else RED
            dot = ctk.CTkLabel(row, text="●", font=("Segoe UI", 14),
                               text_color=dot_color, width=24)
            dot.pack(side="left", padx=(12, 4), pady=10)

            # Label + desc
            info = ctk.CTkFrame(row, fg_color="transparent")
            info.pack(side="left", fill="x", expand=True, pady=6)
            ctk.CTkLabel(info, text=label, font=F_MONO,
                         text_color=TEXT_HI, anchor="w").pack(anchor="w")
            ver_text = str(val) if ok else "Not found / Not configured"
            ver_col  = TEXT_MID if ok else TEXT_DIM
            ctk.CTkLabel(info, text=ver_text[:60], font=F_MONO_SM,
                         text_color=ver_col, anchor="w").pack(anchor="w")

            # Install link
            if url and not ok:
                ctk.CTkButton(row, text="Install →", width=80, height=28,
                              font=F_MONO_SM, fg_color=BG_HOVER,
                              hover_color=BORDER_HI, text_color=BLUE,
                              border_color=BLUE, border_width=1,
                              command=lambda u=url: webbrowser.open(u)
                              ).pack(side="right", padx=12)

        # Recheck + Close
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=24, pady=(0, 20))
        ctk.CTkButton(btn_row, text="↻  Re-check", height=40, font=F_MONO,
                      fg_color=BG_PANEL, hover_color=BG_HOVER,
                      text_color=VIOLET_HI, border_color=VIOLET, border_width=1,
                      command=lambda: self._recheck(scroll, env)
                      ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btn_row, text="✓  Close", height=40, font=F_MONO,
                      fg_color=VIOLET_DIM, hover_color=VIOLET,
                      text_color=TEXT_HI,
                      command=self._close).pack(side="right")

    def _recheck(self, scroll, env):
        self.grab_release()
        self.destroy()

    def _close(self):
        self.grab_release()
        self.destroy()


# ═══════════════════════════════════════════════════════════════
#  CONFLICT RESOLUTION DIALOG
# ═══════════════════════════════════════════════════════════════
class ConflictDialog(ctk.CTkToplevel):
    def __init__(self, parent, url, branch):
        super().__init__(parent)
        self.title("Push Conflict — Resolve")
        self.geometry("540x420")
        self.resizable(False, False)
        self.configure(fg_color=BG_VOID)
        self.grab_set()
        self.choice = None
        self._center()
        self._build(url, branch)

    def _center(self):
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"540x420+{(sw-540)//2}+{(sh-420)//2}")

    def _build(self, url, branch):
        bar = ctk.CTkFrame(self, fg_color=YELLOW, height=3, corner_radius=0)
        bar.pack(fill="x")

        ctk.CTkLabel(self, text="⚠  Push Rejected",
                     font=F_MONO_LG, text_color=YELLOW).pack(pady=(20, 6))
        ctk.CTkLabel(self,
                     text=f"Remote has commits your local copy doesn't have.\n"
                          f"Branch: {branch}  ·  {url}",
                     font=F_UI_SM, text_color=TEXT_MID,
                     justify="center", wraplength=480).pack(pady=(0, 18))

        opts = [
            ("↙  Pull & Merge then Push",
             "Fetches remote changes and merges. Safe — preserves all history.",
             BLUE, "merge"),
            ("⊛  Pull with Rebase then Push",
             "Replays your commits on top of remote. Clean linear history.",
             VIOLET_HI, "rebase"),
            ("⚡  Force Push (overwrite remote)",
             "YOUR local files replace remote. WARNING: remote commits lost.",
             ORANGE, "force"),
        ]
        for label, desc, col, key in opts:
            card = ctk.CTkFrame(self, fg_color=BG_CARD,
                                corner_radius=8, border_color=BORDER_MID, border_width=1)
            card.pack(fill="x", padx=24, pady=4)
            ctk.CTkButton(card, text=label, height=44, font=F_MONO,
                          fg_color=BG_HOVER, hover_color=BORDER_HI,
                          text_color=col, border_color=col, border_width=1,
                          anchor="w",
                          command=lambda k=key: self._pick(k)
                          ).pack(fill="x", padx=10, pady=(10, 4))
            ctk.CTkLabel(card, text=f"  {desc}", font=F_UI_SM,
                         text_color=TEXT_DIM, justify="left",
                         anchor="w").pack(anchor="w", padx=14, pady=(0, 10))

        ctk.CTkButton(self, text="✕  Cancel", height=36, font=F_MONO,
                      fg_color="transparent", hover_color=BG_HOVER,
                      text_color=RED, border_color=RED, border_width=1,
                      command=lambda: self._pick(None)).pack(pady=(8, 16))

    def _pick(self, choice):
        self.choice = choice
        self.grab_release()
        self.destroy()


# ═══════════════════════════════════════════════════════════════
#  GIT SETUP WIZARD
# ═══════════════════════════════════════════════════════════════
class GitSetupWizard(ctk.CTkToplevel):
    def __init__(self, parent, git_missing, cur_name="", cur_email="", on_done=None):
        super().__init__(parent)
        self.title("Git Setup Wizard — DeployPro")
        self.geometry("600x580")
        self.resizable(False, False)
        self.configure(fg_color=BG_VOID)
        self.grab_set()
        self.on_done = on_done
        self.git_missing = git_missing
        self._center()
        self._build(cur_name, cur_email)

    def _center(self):
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"600x580+{(sw-600)//2}+{(sh-580)//2}")

    def _build(self, cur_name, cur_email):
        bar = ctk.CTkFrame(self, fg_color=BLUE, height=3, corner_radius=0)
        bar.pack(fill="x")

        ctk.CTkLabel(self, text="⚙  Git Setup Wizard",
                     font=F_MONO_LG, text_color=BLUE_HI).pack(pady=(20, 4))

        if self.git_missing:
            msg = "Git is NOT installed. Download and install it, then click Re-check."
        else:
            msg = "Git installed ✓  —  Complete your global identity below."

        ctk.CTkLabel(self, text=msg, font=F_UI_SM, text_color=TEXT_MID,
                     wraplength=500, justify="center").pack(pady=(2, 14))

        scr = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scr.pack(fill="both", expand=True, padx=0)

        # Install Git
        if self.git_missing:
            self._card(scr, "Step 1 — Install Git", [
                ("", "Download Git from git-scm.com and run the installer."),
            ])
            brow = ctk.CTkFrame(scr, fg_color="transparent")
            brow.pack(fill="x", padx=28, pady=(0, 12))
            ctk.CTkButton(brow, text="⬇  git-scm.com", width=180, height=36,
                          font=F_MONO, fg_color=BLUE_DIM, hover_color=BLUE,
                          text_color=TEXT_HI,
                          command=lambda: webbrowser.open("https://git-scm.com/download")
                          ).pack(side="left", padx=(0, 8))
            ctk.CTkButton(brow, text="↻  Re-check", width=110, height=36,
                          font=F_MONO, fg_color=BG_PANEL,
                          hover_color=BG_HOVER, text_color=CYAN,
                          border_color=CYAN, border_width=1,
                          command=self._recheck).pack(side="left")

        # Identity
        step = "Step 2" if self.git_missing else "Step 1"
        id_card = ctk.CTkFrame(scr, fg_color=BG_CARD, corner_radius=10,
                                border_color=BORDER_MID, border_width=1)
        id_card.pack(fill="x", padx=24, pady=(0, 12))
        ctk.CTkLabel(id_card, text=f"{step} — Git Global Identity",
                     font=F_UI_LG, text_color=TEXT_HI).pack(anchor="w", padx=18, pady=(14, 6))

        self.name_var  = ctk.StringVar(value=cur_name)
        self.email_var = ctk.StringVar(value=cur_email)
        self._wiz_field(id_card, "Full Name", self.name_var, "e.g.  Jane Doe")
        self._wiz_field(id_card, "Email",     self.email_var,"e.g.  jane@github.com")

        ctk.CTkButton(id_card, text="💾  Save Identity", height=38, font=F_MONO,
                      fg_color=BLUE_DIM, hover_color=BLUE, text_color=TEXT_HI,
                      command=self._save_id).pack(fill="x", padx=18, pady=(8, 14))

        # PAT
        step2 = "Step 3" if self.git_missing else "Step 2"
        self._card(scr, f"{step2} — Personal Access Token (PAT)", [
            ("", "GitHub needs a PAT instead of your password."),
            ("", "GitHub → Settings → Developer Settings → Tokens (classic)"),
            ("", "Scopes required: repo, workflow"),
        ])
        ctk.CTkButton(scr, text="⬡  Open GitHub Token Page", height=34, font=F_MONO,
                      fg_color=BG_PANEL, hover_color=BG_HOVER,
                      text_color=VIOLET_HI, border_color=VIOLET, border_width=1,
                      command=lambda: webbrowser.open(
                          "https://github.com/settings/tokens/new?scopes=repo,workflow&description=DeployPro")
                      ).pack(fill="x", padx=28, pady=(0, 16))

        # gh CLI hint
        step3 = "Step 4" if self.git_missing else "Step 3"
        self._card(scr, f"{step3} — GitHub CLI (optional but recommended)", [
            ("", "Enables repo creation directly from DeployPro."),
            ("", "Run: gh auth login   after installing."),
        ])
        ctk.CTkButton(scr, text="⬇  cli.github.com", height=34, font=F_MONO,
                      fg_color=BG_PANEL, hover_color=BG_HOVER,
                      text_color=BLUE_HI, border_color=BLUE, border_width=1,
                      command=lambda: webbrowser.open("https://cli.github.com")
                      ).pack(fill="x", padx=28, pady=(0, 16))

        ctk.CTkButton(scr, text="✓  Done — Close Wizard", height=44, font=F_MONO_LG,
                      fg_color=VIOLET_DIM, hover_color=VIOLET, text_color=TEXT_HI,
                      corner_radius=8,
                      command=self._finish).pack(fill="x", padx=24, pady=(4, 20))

    def _card(self, parent, title, items):
        card = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=10,
                             border_color=BORDER_DIM, border_width=1)
        card.pack(fill="x", padx=24, pady=(0, 10))
        ctk.CTkLabel(card, text=title, font=F_UI_LG,
                     text_color=TEXT_HI).pack(anchor="w", padx=18, pady=(12, 4))
        for _, text in items:
            ctk.CTkLabel(card, text=f"  {text}", font=F_UI_SM,
                         text_color=TEXT_MID, justify="left",
                         anchor="w").pack(anchor="w", padx=18, pady=2)
        ctk.CTkFrame(card, fg_color="transparent", height=8).pack()
        return card

    def _wiz_field(self, parent, label, var, placeholder):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=18, pady=3)
        ctk.CTkLabel(row, text=label, font=F_LABEL,
                     text_color=TEXT_DIM, width=80, anchor="w").pack(side="left")
        ctk.CTkEntry(row, textvariable=var, placeholder_text=placeholder,
                     font=F_FIELD, height=34,
                     fg_color=BG_INPUT, border_color=BORDER_MID,
                     text_color=TEXT_HI).pack(side="left", fill="x", expand=True)

    def _save_id(self):
        name  = self.name_var.get().strip()
        email = self.email_var.get().strip()
        if not name or not email:
            messagebox.showerror("Missing", "Both name and email required."); return
        run_cmd(f'git config --global user.name "{name}"')
        run_cmd(f'git config --global user.email "{email}"')
        messagebox.showinfo("Saved ✓", f"Name : {name}\nEmail: {email}")

    def _recheck(self):
        ok, _ = cmd_available("git")
        if ok:
            messagebox.showinfo("Git Found ✓", "Git is installed! Restart DeployPro.")
        else:
            messagebox.showwarning("Not Found", "Git still not detected.")

    def _finish(self):
        self.grab_release()
        self.destroy()
        if self.on_done:
            self.on_done()


# ═══════════════════════════════════════════════════════════════
#  AUTO SETUP WIZARD (Downloads Environment & Configures CLI)
# ═══════════════════════════════════════════════════════════════
class AutoSetupWizard(ctk.CTkToplevel):
    def __init__(self, parent, missing=None, on_done=None):
        super().__init__(parent)
        self.title("Auto-Setup Environment — DeployPro")
        self.geometry("620x520")
        self.resizable(False, False)
        self.configure(fg_color=BG_VOID)
        self.grab_set()
        self.on_done = on_done
        self.missing = missing or {"node": True, "gh": True, "vercel": True}
        self._center()
        self._build()
        if AUTO_INSTALL_CLI:
            self.after(500, self._start_install)

    def _center(self):
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"620x520+{(sw-620)//2}+{(sh-520)//2}")

    def _build(self):
        bar = ctk.CTkFrame(self, fg_color=CYAN, height=3, corner_radius=0)
        bar.pack(fill="x")

        ctk.CTkLabel(self, text="⚡ Environment Auto-Installer",
                     font=F_MONO_LG, text_color=CYAN).pack(pady=(20, 6))
        ctk.CTkLabel(self, text="DeployPro will automatically download and configure missing tools\n"
                                "(Node.js, GitHub CLI, Vercel) in a fully isolated local folder.",
                     font=F_UI_SM, text_color=TEXT_MID, justify="center").pack(pady=(0, 20))

        self.progress_bar = ctk.CTkProgressBar(self, width=460, height=8,
                                               fg_color=BG_PANEL, progress_color=CYAN)
        self.progress_bar.pack(pady=10)
        self.progress_bar.set(0)

        self.lbl_status = ctk.CTkLabel(self, text="Waiting to start...",
                                       font=F_MONO_SM, text_color=TEXT_HI)
        self.lbl_status.pack(pady=5)

        self.txt_log = ctk.CTkTextbox(self, width=500, height=200,
                                      fg_color=BG_INPUT, text_color=TEXT_DIM,
                                      font=("Courier New", 11), state="disabled", corner_radius=8)
        self.txt_log.pack(pady=10, padx=20, fill="both", expand=True)

        self.btn_action = ctk.CTkButton(self, text="Start Auto-Install", height=40, font=F_MONO_LG,
                                        fg_color=BLUE_DIM, hover_color=BLUE, text_color=TEXT_HI,
                                        command=self._start_install)
        self.btn_action.pack(pady=15)

    def _log(self, msg, is_status=True):
        if is_status:
            self.lbl_status.configure(text=msg)
        self.txt_log.configure(state="normal")
        self.txt_log.insert("end", f"> {msg}\n")
        self.txt_log.see("end")
        self.txt_log.configure(state="disabled")
        self.update()

    def _start_install(self):
        self.btn_action.configure(state="disabled", text="Installing...")
        threading.Thread(target=self._run_install, daemon=True).start()

    def _run_install(self):
        os.makedirs(LOCAL_ENV_DIR, exist_ok=True)
        try:
            if self.missing.get("node") or self.missing.get("vercel"):
                self._install_node()
            self.progress_bar.set(0.33)
            
            if self.missing.get("gh"):
                self._install_gh()
            self.progress_bar.set(0.66)
            
            if self.missing.get("vercel"):
                self._install_vercel()
            self.progress_bar.set(0.95)

            # Re-eval paths internally
            global local_paths
            local_paths = []
            if os.path.exists(LOCAL_NODE_DIR): local_paths.append(LOCAL_NODE_DIR)
            if os.path.exists(os.path.join(LOCAL_GH_DIR, "bin")): local_paths.append(os.path.join(LOCAL_GH_DIR, "bin"))
            os.environ["PATH"] = os.pathsep.join(local_paths) + os.pathsep + os.environ.get("PATH", "")

            self._log("Installation Complete!", is_status=True)
            self.progress_bar.set(1.0)
            self.btn_action.configure(state="normal", text="Close & Continue", command=self._finish, fg_color=GREEN_DIM, hover_color=GREEN)
            
            if AUTO_INSTALL_CLI:
                self.after(1000, self._finish)
                
        except Exception as e:
            self._log(f"Error: {e}")
            self.btn_action.configure(state="normal", text="Retry", command=self._start_install, fg_color=RED_DIM, hover_color=RED)

    def _download_and_extract(self, url, extract_to, strip_first_folder=True):
        self._log(f"Downloading {url.split('/')[-1]}...")
        with urllib.request.urlopen(url) as response:
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                shutil.copyfileobj(response, tmp_file)
                tmp_path = tmp_file.name
        
        self._log(f"Extracting to {extract_to}...")
        with zipfile.ZipFile(tmp_path, 'r') as zip_ref:
            if strip_first_folder:
                for member in zip_ref.namelist():
                    parts = member.split('/')
                    if len(parts) > 1:
                        target = os.path.join(extract_to, *parts[1:])
                        if member.endswith('/'):
                            os.makedirs(target, exist_ok=True)
                        else:
                            os.makedirs(os.path.dirname(target), exist_ok=True)
                            with zip_ref.open(member) as source, open(target, "wb") as file:
                                shutil.copyfileobj(source, file)
            else:
                zip_ref.extractall(extract_to)
        os.remove(tmp_path)

    def _install_node(self):
        self._log("Starting Node.js installation...")
        if os.path.exists(LOCAL_NODE_DIR):
            try: shutil.rmtree(LOCAL_NODE_DIR, ignore_errors=True)
            except: pass
        url = "https://nodejs.org/dist/v20.11.1/node-v20.11.1-win-x64.zip"
        self._download_and_extract(url, LOCAL_NODE_DIR)
        self._log("Node.js installed locally.")

    def _install_gh(self):
        self._log("Starting GitHub CLI installation...")
        if os.path.exists(LOCAL_GH_DIR):
            try: shutil.rmtree(LOCAL_GH_DIR, ignore_errors=True)
            except: pass
        url = "https://github.com/cli/cli/releases/download/v2.46.0/gh_2.46.0_windows_amd64.zip"
        self._download_and_extract(url, LOCAL_GH_DIR, strip_first_folder=False)
        self._log("GitHub CLI installed locally.")

    def _install_vercel(self):
        self._log("Installing Vercel CLI via local npm...")
        npm_path = os.path.join(LOCAL_NODE_DIR, "npm.cmd")
        if not os.path.exists(npm_path):
            self._log("npm missing, skipping Vercel.")
            return
        
        install_cmd = f'"{npm_path}" install --global vercel --prefix "{LOCAL_NODE_DIR}" --cache "{LOCAL_ENV_DIR}/npm_cache"'
        self._log(f"Running npm install...")
        proc = subprocess.Popen(install_cmd, shell=True, cwd=LOCAL_NODE_DIR, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in proc.stdout:
            self._log(line.strip(), is_status=False)
        proc.wait()
        if proc.returncode == 0:
            self._log("Vercel CLI installed successfully.")
        else:
            self._log("Vercel CLI installation failed.", is_status=False)

    def _finish(self):
        self.grab_release()
        self.destroy()
        if self.on_done:
            self.on_done()


# ═══════════════════════════════════════════════════════════════
#  REPO CREATE DIALOG  (via gh CLI)
# ═══════════════════════════════════════════════════════════════
class CreateRepoDialog(ctk.CTkToplevel):
    def __init__(self, parent, suggested_name, on_created=None):
        super().__init__(parent)
        self.title("Create GitHub Repo — DeployPro")
        self.geometry("520x440")
        self.resizable(False, False)
        self.configure(fg_color=BG_VOID)
        self.grab_set()
        self.on_created = on_created
        self._center()
        self._build(suggested_name)

    def _center(self):
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"520x440+{(sw-520)//2}+{(sh-440)//2}")

    def _build(self, name):
        bar = ctk.CTkFrame(self, fg_color=GREEN, height=3, corner_radius=0)
        bar.pack(fill="x")

        ctk.CTkLabel(self, text="⊕  Create GitHub Repository",
                     font=F_MONO_LG, text_color=GREEN).pack(pady=(20, 4))
        ctk.CTkLabel(self, text="Creates the repo on GitHub via the gh CLI.",
                     font=F_UI_SM, text_color=TEXT_MID).pack(pady=(0, 16))

        frm = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=10,
                            border_color=BORDER_MID, border_width=1)
        frm.pack(fill="x", padx=24, pady=(0, 12))

        self.repo_var  = ctk.StringVar(value=name)
        self.desc_var  = ctk.StringVar()
        self.priv_var  = ctk.BooleanVar(value=False)

        for lbl, var, ph in [
            ("Repo Name",   self.repo_var,  "my-awesome-project"),
            ("Description", self.desc_var,  "Short description (optional)"),
        ]:
            row = ctk.CTkFrame(frm, fg_color="transparent")
            row.pack(fill="x", padx=18, pady=4)
            ctk.CTkLabel(row, text=lbl, font=F_LABEL,
                         text_color=TEXT_DIM, width=100, anchor="w").pack(side="left")
            ctk.CTkEntry(row, textvariable=var, placeholder_text=ph,
                         font=F_FIELD, height=34,
                         fg_color=BG_INPUT, border_color=BORDER_MID,
                         text_color=TEXT_HI).pack(side="left", fill="x", expand=True)

        vis_row = ctk.CTkFrame(frm, fg_color="transparent")
        vis_row.pack(fill="x", padx=18, pady=(6, 14))
        ctk.CTkLabel(vis_row, text="Private", font=F_LABEL,
                     text_color=TEXT_DIM).pack(side="left")
        ctk.CTkSwitch(vis_row, text="", variable=self.priv_var,
                      button_color=VIOLET, progress_color=VIOLET_DIM,
                      fg_color=BG_PANEL).pack(side="left", padx=10)
        ctk.CTkLabel(vis_row, text="(Public by default)",
                     font=F_MONO_SM, text_color=TEXT_GHOST).pack(side="left")

        # Warnings
        warn = ctk.CTkFrame(self, fg_color=BG_PANEL, corner_radius=8)
        warn.pack(fill="x", padx=24, pady=(0, 12))
        ctk.CTkLabel(warn,
                     text="⚠  gh CLI must be authenticated.\n"
                          "    Run:  gh auth login  if not done.",
                     font=F_MONO_SM, text_color=YELLOW, justify="left"
                     ).pack(anchor="w", padx=14, pady=10)

        ctk.CTkButton(self, text="⊕  Create Repository", height=46, font=F_MONO_LG,
                      fg_color=GREEN_DIM, hover_color=GREEN, text_color=BG_VOID,
                      corner_radius=8,
                      command=self._create).pack(fill="x", padx=24, pady=(0, 8))
        ctk.CTkButton(self, text="✕  Cancel", height=34, font=F_MONO,
                      fg_color="transparent", hover_color=BG_HOVER,
                      text_color=RED, border_color=RED, border_width=1,
                      command=self._cancel).pack(fill="x", padx=24)

    def _create(self):
        name = self.repo_var.get().strip()
        desc = self.desc_var.get().strip()
        priv = self.priv_var.get()

        if not name:
            messagebox.showerror("Required", "Repository name is required."); return

        visibility = "--private" if priv else "--public"
        desc_flag  = f'--description "{desc}"' if desc else ""
        cmd = f'gh repo create {name} {visibility} {desc_flag}'

        code, out, err = run_cmd(cmd)
        if code == 0:
            messagebox.showinfo("Created ✓", f"Repository created:\n{out}")
            if self.on_created:
                self.on_created(name)
            self.grab_release()
            self.destroy()
        else:
            messagebox.showerror("Failed",
                                 f"Could not create repo:\n{err}\n\n"
                                 f"Make sure 'gh auth login' has been run.")

    def _cancel(self):
        self.grab_release()
        self.destroy()


# ═══════════════════════════════════════════════════════════════
#  TERMINAL WIDGET
# ═══════════════════════════════════════════════════════════════
class TerminalBox(ctk.CTkTextbox):
    def __init__(self, master, **kw):
        super().__init__(master, **kw)
        self.configure(state="disabled",
                       font=("Courier New", 12),
                       text_color=CYAN,
                       fg_color=BG_VOID,
                       border_color=BORDER_DIM,
                       border_width=1)
        self._setup_tags()

    def _setup_tags(self):
        self._widget = self._textbox if hasattr(self, "_textbox") else None

    def log(self, msg, color=None):
        self.configure(state="normal")
        self.insert("end", msg + "\n")
        self.configure(state="disabled")
        self.see("end")

    def clear(self):
        self.configure(state="normal")
        self.delete("1.0", "end")
        self.configure(state="disabled")


# ═══════════════════════════════════════════════════════════════
#  FILE LIST  (scrollable checkboxes)
# ═══════════════════════════════════════════════════════════════
class FileListFrame(ctk.CTkScrollableFrame):
    SKIP_DIRS = {'.git','__pycache__','node_modules','.venv','venv',
                 'dist','build','.idea','.vs','target','.next',
                 'out','.vercel','.cache','coverage'}

    def __init__(self, master, **kw):
        super().__init__(master, **kw)
        self.file_vars = {}

    def populate(self, path):
        for w in self.winfo_children():
            w.destroy()
        self.file_vars.clear()
        if not path or not os.path.isdir(path):
            return
        all_files = []
        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if d not in self.SKIP_DIRS]
            for f in files:
                rel = os.path.relpath(os.path.join(root, f), path)
                all_files.append(rel)
        for f in sorted(all_files):
            var = ctk.BooleanVar(value=True)
            row = ctk.CTkFrame(self, fg_color="transparent")
            row.pack(fill="x", pady=1)
            ext = os.path.splitext(f)[1].lower()
            col = VIOLET_HI if ext in {'.py','.js','.ts','.jsx','.tsx'} else \
                  BLUE_HI   if ext in {'.json','.yaml','.yml','.toml','.env'} else \
                  GREEN      if ext in {'.md','.txt','.rst'} else TEXT_MID
            ctk.CTkCheckBox(row, text=f, variable=var,
                            font=("Courier New", 11), text_color=col,
                            fg_color=BLUE_DIM, hover_color=BLUE,
                            checkmark_color=TEXT_HI, border_color=BORDER_MID,
                            ).pack(anchor="w", padx=8)
            self.file_vars[f] = var

    def get_selected(self):
        return [f for f, v in self.file_vars.items() if v.get()]

    def select_all(self):
        for v in self.file_vars.values(): v.set(True)

    def deselect_all(self):
        for v in self.file_vars.values(): v.set(False)

    def filter_by_ext(self, exts):
        """Select only files matching given extensions (e.g. {'.py', '.md'})"""
        for f, v in self.file_vars.items():
            ext = os.path.splitext(f)[1].lower()
            v.set(ext in exts)


# ═══════════════════════════════════════════════════════════════
#  STATUS INDICATOR ROW
# ═══════════════════════════════════════════════════════════════
class StatusBar(ctk.CTkFrame):
    def __init__(self, master, **kw):
        super().__init__(master, fg_color=BG_CARD, height=34,
                         corner_radius=0, **kw)
        self.pack_propagate(False)
        self._dots = {}
        self._labels = {}
        items = [
            ("git",    "git"),
            ("gh",     "gh"),
            ("vercel", "vercel"),
            ("node",   "node"),
            ("auth",   "gh-auth"),
        ]
        ctk.CTkLabel(self, text="ENV:", font=F_MONO_SM,
                     text_color=TEXT_DIM).pack(side="left", padx=(12, 4))
        for key, name in items:
            dot = ctk.CTkLabel(self, text="●", font=("Segoe UI", 11),
                               text_color=TEXT_GHOST)
            dot.pack(side="left", padx=(0, 2))
            lbl = ctk.CTkLabel(self, text=name, font=F_MONO_SM,
                               text_color=TEXT_DIM)
            lbl.pack(side="left", padx=(0, 10))
            self._dots[key]   = dot
            self._labels[key] = lbl

    def update_env(self, env):
        mapping = {
            "git":    bool(env.get("git")),
            "gh":     bool(env.get("gh")),
            "vercel": bool(env.get("vercel")),
            "node":   bool(env.get("node")),
            "auth":   bool(env.get("gh_auth")),
        }
        for key, ok in mapping.items():
            self._dots[key].configure(text_color=GREEN if ok else RED)


# ═══════════════════════════════════════════════════════════════
#  MAIN APPLICATION
# ═══════════════════════════════════════════════════════════════
class DeployPro(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.withdraw()

        self.title("◈  DeployPro")
        self.geometry("1340x900")
        self.minsize(1100, 740)
        self.configure(fg_color=BG_VOID)

        # State
        self.project_path      = ctk.StringVar()
        self.repo_name         = ctk.StringVar()
        self.git_username      = ctk.StringVar()
        self.git_email         = ctk.StringVar()
        self.gh_username       = ctk.StringVar()
        self.branch            = ctk.StringVar(value="main")
        self.commit_msg        = ctk.StringVar(value="Initial commit")
        self.gitignore_preset  = ctk.StringVar(value="Node.js")
        self.create_gitignore  = ctk.BooleanVar(value=True)
        self.create_readme     = ctk.BooleanVar(value=True)

        # Vercel state
        self.vercel_proj_name  = ctk.StringVar()
        self.vercel_framework  = ctk.StringVar(value="Auto-detect")
        self.vercel_prod       = ctk.BooleanVar(value=False)

        self._env = {}

        # Splash
        self.splash = SplashScreen(self)
        threading.Thread(target=self._boot, daemon=True).start()

    # ── Boot ──────────────────────────────────────────────────
    def _boot(self):
        sp = self.splash
        sp.set_progress(0.10, "Checking environment…")
        self._env = self._detect_env()

        sp.set_progress(0.40, "Reading git identity…")
        name  = git_global("user.name")
        email = git_global("user.email")
        self.git_username.set(name)
        self.git_email.set(email)
        if email and not self.gh_username.get():
            self.gh_username.set(email.split("@")[0])

        sp.set_progress(0.65, "Building interface…")
        time.sleep(0.2)
        self.after(0, self._build_ui)

        sp.set_progress(0.90, "Finalising…")
        time.sleep(0.4)
        sp.set_progress(1.0, "Ready.")
        time.sleep(0.5)
        self.after(0, self._finish_boot, name, email)

    def _detect_env(self):
        git_ok, git_v  = cmd_available("git")
        gh_ok,  gh_v   = cmd_available("gh")
        vcl_ok, vcl_v  = cmd_available("vercel")
        node_ok, node_v = cmd_available("node")
        npm_ok, npm_v  = cmd_available("npm")
        gh_auth         = gh_logged_in() if gh_ok else False
        vcl_auth, vcl_user = vercel_logged_in() if vcl_ok else (False, "")
        name  = git_global("user.name")
        email = git_global("user.email")
        return {
            "git":         git_v  if git_ok  else None,
            "gh":          gh_v   if gh_ok   else None,
            "vercel":      vcl_v  if vcl_ok  else None,
            "node":        node_v if node_ok  else None,
            "npm":         npm_v  if npm_ok  else None,
            "gh_auth":     gh_auth,
            "vercel_auth": vcl_user if vcl_auth else None,
            "git_name":    name  or None,
            "git_email":   email or None,
        }

    def _finish_boot(self, name, email):
        self.splash.destroy()
        self.deiconify()
        self._center()
        self.status_bar.update_env(self._env)

        missing_env = {"node": not self._env.get("node"), 
                       "gh": not self._env.get("gh"), 
                       "vercel": not self._env.get("vercel")}
        
        needs_setup = any(missing_env.values()) and (sys.platform == "win32")
        
        if needs_setup and (AUTO_INSTALL_CLI or messagebox.askyesno("Setup Environment", "Missing required tools (Node/npm, GitHub CLI, Vercel).\n\nDownload and install them automatically? (Fully isolated setup)")):
            self.terminal.log("◈  Starting AutoSetupWizard...", CYAN)
            self.after(400, lambda: AutoSetupWizard(self, missing=missing_env, on_done=lambda: self._boot_step_2(name, email)))
            return
            
        self._boot_step_2(name, email)

    def _boot_step_2(self, name, email):
        self._env = self._detect_env()
        self.status_bar.update_env(self._env)
        
        if self._env.get("gh") and not self._env.get("gh_auth"):
            self.terminal.log("\n⚠  GitHub CLI not authenticated. Opening prompt...", YELLOW)
            subprocess.run("start cmd /k gh auth login", shell=True)
            self._env["gh_auth"] = True
            self.status_bar.update_env(self._env)
            
        if self._env.get("vercel") and not self._env.get("vercel_auth"):
            self.terminal.log("\n⚠  Vercel CLI not authenticated. Opening prompt...", YELLOW)
            subprocess.run("start cmd /k vercel login", shell=True)

        name = git_global("user.name") or name
        email = git_global("user.email") or email

        if not self._env.get("git"):
            self.terminal.log("⚠  Git not found. Opening setup wizard…", YELLOW)
            self.after(400, lambda: GitSetupWizard(
                self, True, name, email, on_done=self._post_wizard))
        elif not name or not email:
            self.terminal.log("⚠  Git identity not configured. Opening wizard…", YELLOW)
            self.after(400, lambda: GitSetupWizard(
                self, False, name, email, on_done=self._post_wizard))
        else:
            self._boot_ready()

    def _post_wizard(self):
        name  = git_global("user.name")
        email = git_global("user.email")
        self.git_username.set(name)
        self.git_email.set(email)
        self.terminal.log(f"✓  Identity: {name} <{email}>", GREEN)
        self._boot_ready()

    def _boot_ready(self):
        self.terminal.log("◈  DeployPro ready.", CYAN)
        self.terminal.log(f"   git  : {self._env.get('git','—')}", TEXT_DIM)
        self.terminal.log(f"   gh   : {'✓ authed' if self._env.get('gh_auth') else '✗ not authed'}", TEXT_DIM)
        self.terminal.log(f"   vercel: {'✓ ' + str(self._env.get('vercel_auth')) if self._env.get('vercel_auth') else '✗ not logged in'}", TEXT_DIM)
        self.terminal.log(f"   node : {self._env.get('node','not found')}", TEXT_DIM)
        self.terminal.log("\n📂  Select a project folder to begin.", TEXT_MID)

    def _center(self):
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"1340x900+{(sw-1340)//2}+{(sh-900)//2}")

    # ── UI Build ──────────────────────────────────────────────
    def _build_ui(self):
        # Top accent bar
        bar = ctk.CTkFrame(self, fg_color=BG_CARD, height=3, corner_radius=0)
        bar.pack(fill="x")

        # ── Header ──
        hdr = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=0, height=64)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        ctk.CTkLabel(hdr, text="◈", font=("Segoe UI", 26),
                     text_color=VIOLET).pack(side="left", padx=(20, 6))
        ctk.CTkLabel(hdr, text="DeployPro",
                     font=("Courier New", 20, "bold"),
                     text_color=TEXT_HI).pack(side="left")
        ctk.CTkLabel(hdr, text="  GitHub · Vercel Suite",
                     font=F_MONO_SM, text_color=TEXT_DIM).pack(side="left")

        # Header right buttons
        for txt, cmd, col in [
            ("⬡  Env Check",  self._show_env,    VIOLET_HI),
            ("⚙  Git Wizard", self._open_wizard,  BLUE_HI),
            ("⬡  GitHub",     self._open_github,  CYAN),
        ]:
            ctk.CTkButton(hdr, text=txt, width=120, height=32, font=F_MONO_SM,
                          fg_color=BG_PANEL, hover_color=BG_HOVER,
                          text_color=col, border_color=BORDER_MID, border_width=1,
                          command=cmd).pack(side="right", padx=4)

        # Status bar
        self.status_bar = StatusBar(self)
        self.status_bar.pack(fill="x")

        # Divider
        ctk.CTkFrame(self, fg_color=BORDER_DIM, height=1,
                     corner_radius=0).pack(fill="x")

        # ── Tab bar ──
        self.tab_bar = ctk.CTkFrame(self, fg_color=BG_BASE, corner_radius=0, height=44)
        self.tab_bar.pack(fill="x")
        self.tab_bar.pack_propagate(False)

        self._active_tab = ctk.StringVar(value="github")
        self._tab_btns   = {}
        for key, label in [("github", "  ⊙  GitHub Deploy  "), ("vercel", "  ◈  Vercel Deploy  ")]:
            btn = ctk.CTkButton(self.tab_bar, text=label, height=44,
                                font=F_MONO, corner_radius=0,
                                fg_color=BG_CARD if key == "github" else "transparent",
                                hover_color=BG_HOVER,
                                text_color=BLUE_HI if key == "github" else TEXT_DIM,
                                border_width=0,
                                command=lambda k=key: self._switch_tab(k))
            btn.pack(side="left", padx=0)
            self._tab_btns[key] = btn

        # ── Body container ──
        self.body_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.body_frame.pack(fill="both", expand=True, padx=12, pady=8)

        self._github_frame = ctk.CTkFrame(self.body_frame, fg_color="transparent")
        self._vercel_frame = ctk.CTkFrame(self.body_frame, fg_color="transparent")

        self._build_github_tab(self._github_frame)
        self._build_vercel_tab(self._vercel_frame)

        # Show github tab by default
        self._github_frame.pack(fill="both", expand=True)

    def _switch_tab(self, key):
        self._active_tab.set(key)
        for k, btn in self._tab_btns.items():
            if k == key:
                btn.configure(fg_color=BG_CARD,
                              text_color=BLUE_HI if k == "github" else VIOLET_HI)
            else:
                btn.configure(fg_color="transparent", text_color=TEXT_DIM)

        if key == "github":
            self._vercel_frame.pack_forget()
            self._github_frame.pack(fill="both", expand=True)
        else:
            self._github_frame.pack_forget()
            self._vercel_frame.pack(fill="both", expand=True)

    # ════════════════════════════════════════════════════════════
    #  GITHUB TAB
    # ════════════════════════════════════════════════════════════
    def _build_github_tab(self, parent):
        parent.columnconfigure(0, weight=36)
        parent.columnconfigure(1, weight=64)
        parent.rowconfigure(0, weight=1)

        self._build_gh_left(parent)
        self._build_gh_right(parent)

    # ── Left panel ────────────────────────────────────────────
    def _build_gh_left(self, parent):
        left = ctk.CTkScrollableFrame(parent, fg_color=BG_CARD,
                                       corner_radius=12,
                                       border_color=BORDER_MID, border_width=1)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        # ── Project ──
        self._sec(left, "⊙", "PROJECT FOLDER", BLUE_HI)
        pr = ctk.CTkFrame(left, fg_color="transparent")
        pr.pack(fill="x", padx=14, pady=(0, 10))
        ctk.CTkEntry(pr, textvariable=self.project_path,
                     placeholder_text="Click Browse to select your project…",
                     font=F_FIELD, height=36,
                     fg_color=BG_INPUT, border_color=BORDER_MID,
                     text_color=TEXT_HI).pack(side="left", fill="x", expand=True, padx=(0, 6))
        ctk.CTkButton(pr, text="Browse", width=80, height=36, font=F_MONO,
                      fg_color=BLUE_DIM, hover_color=BLUE, text_color=TEXT_HI,
                      command=self._browse).pack(side="right")

        # ── Identity ──
        self._sec(left, "◎", "GIT IDENTITY", VIOLET_HI)
        self._field(left, "Name",  self.git_username, "Your commit name")
        self._field(left, "Email", self.git_email,    "GitHub-linked email")
        ctk.CTkButton(left, text="💾  Save Identity", height=32, font=F_MONO,
                      fg_color=BG_PANEL, hover_color=BG_HOVER,
                      text_color=VIOLET_HI, border_color=VIOLET, border_width=1,
                      command=self._save_identity).pack(fill="x", padx=14, pady=(2, 8))

        # ── GitHub Config ──
        self._sec(left, "⊡", "GITHUB CONFIG", CYAN)
        self._field(left, "GH User", self.gh_username, "GitHub account name")
        self._field(left, "Repo",    self.repo_name,   "Repository name (must exist or create)")
        self._field(left, "Branch",  self.branch,      "main / master / dev")
        self._field(left, "Message", self.commit_msg,  "Commit message")

        # Create repo button
        ctk.CTkButton(left, text="⊕  Create Repo on GitHub", height=34, font=F_MONO,
                      fg_color=GREEN_DIM, hover_color=GREEN, text_color=BG_VOID,
                      command=self._create_repo).pack(fill="x", padx=14, pady=(4, 8))

        # ── Options ──
        self._sec(left, "⊞", "OPTIONS", TEXT_MID)
        opt = ctk.CTkFrame(left, fg_color=BG_PANEL, corner_radius=8)
        opt.pack(fill="x", padx=14, pady=(0, 8))

        row1 = ctk.CTkFrame(opt, fg_color="transparent")
        row1.pack(fill="x", padx=12, pady=(10, 4))
        ctk.CTkCheckBox(row1, text="Auto .gitignore", variable=self.create_gitignore,
                        font=F_LABEL, text_color=TEXT_MID,
                        fg_color=BLUE_DIM, hover_color=BLUE,
                        checkmark_color=TEXT_HI, border_color=BORDER_MID,
                        command=self._toggle_preset).pack(side="left")

        row2 = ctk.CTkFrame(opt, fg_color="transparent")
        row2.pack(fill="x", padx=12, pady=4)
        ctk.CTkLabel(row2, text="Preset:", font=F_LABEL,
                     text_color=TEXT_DIM).pack(side="left")
        self.preset_menu = ctk.CTkOptionMenu(
            row2, variable=self.gitignore_preset,
            values=list(GITIGNORE_PRESETS.keys()),
            font=F_LABEL, height=30,
            fg_color=BG_INPUT, button_color=BG_HOVER,
            button_hover_color=BORDER_HI, text_color=CYAN,
            dropdown_fg_color=BG_PANEL)
        self.preset_menu.pack(side="left", padx=8)

        row3 = ctk.CTkFrame(opt, fg_color="transparent")
        row3.pack(fill="x", padx=12, pady=(4, 12))
        ctk.CTkCheckBox(row3, text="Auto README.md", variable=self.create_readme,
                        font=F_LABEL, text_color=TEXT_MID,
                        fg_color=VIOLET_DIM, hover_color=VIOLET,
                        checkmark_color=TEXT_HI, border_color=BORDER_MID,
                        ).pack(side="left")

        # ── Deploy ──
        self._deploy_btn = ctk.CTkButton(
            left, text="  ⊙  DEPLOY TO GITHUB  ",
            font=("Courier New", 15, "bold"), height=56,
            fg_color=BLUE_DIM, hover_color=BLUE,
            text_color=TEXT_HI, corner_radius=10,
            command=self._confirm_deploy)
        self._deploy_btn.pack(fill="x", padx=14, pady=(12, 6))

        # ── Quick Actions ──
        self._sec(left, "⚡", "QUICK ACTIONS", YELLOW)
        qa = ctk.CTkFrame(left, fg_color="transparent")
        qa.pack(fill="x", padx=14, pady=(0, 4))
        for txt, cmd in [("status", self._status),
                         ("log",    self._git_log),
                         ("pull",   self._pull)]:
            ctk.CTkButton(qa, text=txt, height=32, font=F_MONO_SM,
                          fg_color=BG_PANEL, hover_color=BG_HOVER,
                          text_color=YELLOW, border_color=BORDER_MID, border_width=1,
                          command=cmd).pack(side="left", expand=True, padx=2)

        qa2 = ctk.CTkFrame(left, fg_color="transparent")
        qa2.pack(fill="x", padx=14, pady=(4, 12))
        ctk.CTkButton(qa2, text="stash",  height=32, font=F_MONO_SM,
                      fg_color=BG_PANEL, hover_color=BG_HOVER,
                      text_color=TEXT_MID, border_color=BORDER_DIM, border_width=1,
                      command=self._stash).pack(side="left", expand=True, padx=2)
        ctk.CTkButton(qa2, text="diff",   height=32, font=F_MONO_SM,
                      fg_color=BG_PANEL, hover_color=BG_HOVER,
                      text_color=TEXT_MID, border_color=BORDER_DIM, border_width=1,
                      command=self._diff).pack(side="left", expand=True, padx=2)
        ctk.CTkButton(qa2, text="reset ↩", height=32, font=F_MONO_SM,
                      fg_color=BG_PANEL, hover_color=BG_HOVER,
                      text_color=RED, border_color=BORDER_DIM, border_width=1,
                      command=self._soft_reset).pack(side="left", expand=True, padx=2)

    # ── Right panel ───────────────────────────────────────────
    def _build_gh_right(self, parent):
        right = ctk.CTkFrame(parent, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew")
        right.rowconfigure(0, weight=5)
        right.rowconfigure(1, weight=4)
        right.columnconfigure(0, weight=1)

        # ── File list ──
        fl = ctk.CTkFrame(right, fg_color=BG_CARD, corner_radius=12,
                           border_color=BORDER_MID, border_width=1)
        fl.grid(row=0, column=0, sticky="nsew", pady=(0, 8))
        fl.rowconfigure(1, weight=1)
        fl.columnconfigure(0, weight=1)

        fhr = ctk.CTkFrame(fl, fg_color="transparent")
        fhr.grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 4))
        ctk.CTkLabel(fhr, text="⊟  FILES TO COMMIT",
                     font=F_MONO, text_color=BLUE_HI).pack(side="left")

        for txt, cmd, col in [
            ("✗ None",     lambda: self.file_list.deselect_all(), TEXT_DIM),
            ("✓ All",      lambda: self.file_list.select_all(),   GREEN),
            ("↻ Refresh",  self._refresh_files,                    CYAN),
        ]:
            ctk.CTkButton(fhr, text=txt, width=84, height=28, font=F_MONO_SM,
                          fg_color=BG_PANEL, hover_color=BG_HOVER,
                          text_color=col, border_color=BORDER_DIM, border_width=1,
                          command=cmd).pack(side="right", padx=2)

        # Filter row
        filt = ctk.CTkFrame(fl, fg_color=BG_PANEL, corner_radius=6)
        filt.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 4))
        ctk.CTkLabel(filt, text="Quick filter:", font=F_MONO_SM,
                     text_color=TEXT_DIM).pack(side="left", padx=8)
        for label, exts in [
            ("JS/TS",  {'.js','.ts','.jsx','.tsx'}),
            ("Python", {'.py'}),
            ("Config", {'.json','.yaml','.yml','.toml','.env'}),
            ("Docs",   {'.md','.txt','.rst'}),
        ]:
            ctk.CTkButton(filt, text=label, width=60, height=24, font=F_MONO_SM,
                          fg_color="transparent", hover_color=BG_HOVER,
                          text_color=VIOLET_HI, border_color=BORDER_DIM, border_width=1,
                          command=lambda e=exts: self.file_list.filter_by_ext(e)
                          ).pack(side="left", padx=2, pady=4)

        self.file_list = FileListFrame(fl, fg_color=BG_INPUT,
                                       corner_radius=6,
                                       border_color=BORDER_DIM, border_width=1)
        self.file_list.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))
        fl.rowconfigure(2, weight=1)

        # ── Terminal ──
        term = ctk.CTkFrame(right, fg_color=BG_CARD, corner_radius=12,
                             border_color=BORDER_MID, border_width=1)
        term.grid(row=1, column=0, sticky="nsew")
        term.rowconfigure(1, weight=1)
        term.columnconfigure(0, weight=1)

        tr = ctk.CTkFrame(term, fg_color="transparent")
        tr.grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 4))
        ctk.CTkLabel(tr, text="⬛  TERMINAL",
                     font=F_MONO, text_color=CYAN).pack(side="left")
        ctk.CTkButton(tr, text="Clear", width=60, height=26, font=F_MONO_SM,
                      fg_color=BG_PANEL, hover_color=BG_HOVER,
                      text_color=TEXT_DIM, border_color=BORDER_DIM, border_width=1,
                      command=lambda: self.terminal.clear()).pack(side="right")

        self.terminal = TerminalBox(term)
        self.terminal.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

    # ════════════════════════════════════════════════════════════
    #  VERCEL TAB
    # ════════════════════════════════════════════════════════════
    def _build_vercel_tab(self, parent):
        parent.columnconfigure(0, weight=38)
        parent.columnconfigure(1, weight=62)
        parent.rowconfigure(0, weight=1)

        # ── Left ──
        vleft = ctk.CTkScrollableFrame(parent, fg_color=BG_CARD,
                                        corner_radius=12,
                                        border_color=BORDER_MID, border_width=1)
        vleft.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        self._sec(vleft, "◈", "VERCEL DEPLOYMENT", VIOLET_HI)

        # Vercel status
        auth = self._env.get("vercel_auth")
        v_ok = bool(self._env.get("vercel"))
        status_col = GREEN if (v_ok and auth) else YELLOW if v_ok else RED
        status_txt = f"Logged in as {auth}" if auth else \
                     ("Vercel CLI found, not logged in" if v_ok else "Vercel CLI not found")
        vstatus = ctk.CTkFrame(vleft, fg_color=BG_PANEL, corner_radius=8)
        vstatus.pack(fill="x", padx=14, pady=(0, 10))
        ctk.CTkLabel(vstatus, text="●", font=("Segoe UI", 13),
                     text_color=status_col).pack(side="left", padx=(12, 4), pady=8)
        ctk.CTkLabel(vstatus, text=status_txt, font=F_MONO_SM,
                     text_color=TEXT_MID).pack(side="left")

        # Vercel config fields
        self._sec(vleft, "⊡", "PROJECT CONFIG", CYAN)
        self._vfield(vleft, "Project Name", self.vercel_proj_name, "auto-detected from folder")

        row_fw = ctk.CTkFrame(vleft, fg_color="transparent")
        row_fw.pack(fill="x", padx=14, pady=3)
        ctk.CTkLabel(row_fw, text="Framework", font=F_LABEL,
                     text_color=TEXT_DIM, width=110, anchor="w").pack(side="left")
        fw_menu = ctk.CTkOptionMenu(
            row_fw, variable=self.vercel_framework,
            values=["Auto-detect","Next.js","Vite","Create React App","Vue",
                    "Nuxt","SvelteKit","Astro","Remix","Gatsby","Other"],
            font=F_LABEL, height=32,
            fg_color=BG_INPUT, button_color=BG_HOVER,
            button_hover_color=BORDER_HI, text_color=VIOLET_HI,
            dropdown_fg_color=BG_PANEL)
        fw_menu.pack(side="left", fill="x", expand=True)

        prod_row = ctk.CTkFrame(vleft, fg_color=BG_PANEL, corner_radius=8)
        prod_row.pack(fill="x", padx=14, pady=8)
        ctk.CTkLabel(prod_row, text="Production deployment",
                     font=F_LABEL, text_color=TEXT_MID).pack(side="left", padx=12, pady=10)
        ctk.CTkSwitch(prod_row, text="", variable=self.vercel_prod,
                      button_color=VIOLET, progress_color=VIOLET_DIM,
                      fg_color=BG_INPUT).pack(side="right", padx=12)

        # Vercel deploy button
        ctk.CTkButton(vleft,
                      text="  ◈  DEPLOY TO VERCEL  ",
                      font=("Courier New", 15, "bold"), height=56,
                      fg_color=VIOLET_DIM, hover_color=VIOLET,
                      text_color=TEXT_HI, corner_radius=10,
                      command=self._vercel_deploy
                      ).pack(fill="x", padx=14, pady=(12, 6))

        # Install Vercel CLI btn
        if not v_ok:
            ctk.CTkButton(vleft, text="⬇  Install Vercel CLI", height=36, font=F_MONO,
                          fg_color=BG_PANEL, hover_color=BG_HOVER,
                          text_color=YELLOW, border_color=YELLOW, border_width=1,
                          command=lambda: webbrowser.open("https://vercel.com/docs/cli")
                          ).pack(fill="x", padx=14, pady=(0, 8))

        # Login button
        self._sec(vleft, "⚡", "QUICK ACTIONS", YELLOW)
        qa_v = ctk.CTkFrame(vleft, fg_color="transparent")
        qa_v.pack(fill="x", padx=14, pady=(0, 6))
        for txt, cmd in [
            ("vercel login",  self._vercel_login),
            ("vercel ls",     self._vercel_ls),
            ("vercel logs",   self._vercel_logs),
        ]:
            ctk.CTkButton(qa_v, text=txt, height=32, font=F_MONO_SM,
                          fg_color=BG_PANEL, hover_color=BG_HOVER,
                          text_color=VIOLET_HI, border_color=BORDER_DIM, border_width=1,
                          command=cmd).pack(side="left", expand=True, padx=2)

        # Docs
        ctk.CTkButton(vleft, text="⬡  Open Vercel Dashboard", height=34, font=F_MONO,
                      fg_color=BG_PANEL, hover_color=BG_HOVER,
                      text_color=CYAN, border_color=BORDER_DIM, border_width=1,
                      command=lambda: webbrowser.open("https://vercel.com/dashboard")
                      ).pack(fill="x", padx=14, pady=(4, 12))

        # ── Right: shared terminal + file list ──
        vright = ctk.CTkFrame(parent, fg_color="transparent")
        vright.grid(row=0, column=1, sticky="nsew")
        vright.rowconfigure(0, weight=3)
        vright.rowconfigure(1, weight=5)
        vright.columnconfigure(0, weight=1)

        # Vercel info card
        info = ctk.CTkFrame(vright, fg_color=BG_CARD, corner_radius=12,
                             border_color=BORDER_MID, border_width=1)
        info.grid(row=0, column=0, sticky="nsew", pady=(0, 8))
        ctk.CTkLabel(info,
                     text="◈  How Vercel Deployment Works",
                     font=F_MONO, text_color=VIOLET_HI).pack(anchor="w", padx=16, pady=(14, 8))

        steps = [
            ("1", "Select your project folder in the GitHub tab first."),
            ("2", "DeployPro runs  vercel --confirm  (or  vercel --prod  for production)."),
            ("3", "The CLI auto-detects your framework (Next.js, Vite, CRA, etc.)."),
            ("4", "A preview URL is returned. Switch on Production for a live deploy."),
            ("5", "On re-deploy, Vercel links the project automatically via .vercel/ config."),
        ]
        for num, text in steps:
            srow = ctk.CTkFrame(info, fg_color=BG_PANEL, corner_radius=6)
            srow.pack(fill="x", padx=16, pady=3)
            ctk.CTkLabel(srow, text=num, font=F_MONO,
                         text_color=VIOLET_HI, width=24).pack(side="left", padx=(10, 4), pady=8)
            ctk.CTkLabel(srow, text=text, font=F_UI_SM,
                         text_color=TEXT_MID, anchor="w").pack(side="left", padx=(0, 10))
        ctk.CTkFrame(info, fg_color="transparent", height=10).pack()

        # Vercel terminal
        vterm_f = ctk.CTkFrame(vright, fg_color=BG_CARD, corner_radius=12,
                                border_color=BORDER_MID, border_width=1)
        vterm_f.grid(row=1, column=0, sticky="nsew")
        vterm_f.rowconfigure(1, weight=1)
        vterm_f.columnconfigure(0, weight=1)

        vtr = ctk.CTkFrame(vterm_f, fg_color="transparent")
        vtr.grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 4))
        ctk.CTkLabel(vtr, text="⬛  VERCEL TERMINAL",
                     font=F_MONO, text_color=VIOLET_HI).pack(side="left")
        ctk.CTkButton(vtr, text="Clear", width=60, height=26, font=F_MONO_SM,
                      fg_color=BG_PANEL, hover_color=BG_HOVER,
                      text_color=TEXT_DIM, border_color=BORDER_DIM, border_width=1,
                      command=lambda: self.vercel_terminal.clear()
                      ).pack(side="right")

        self.vercel_terminal = TerminalBox(vterm_f)
        self.vercel_terminal.configure(text_color=VIOLET_HI)
        self.vercel_terminal.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

    # ── UI helpers ────────────────────────────────────────────
    def _sec(self, parent, icon, title, col=TEXT_MID):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=(12, 4))
        ctk.CTkLabel(row, text=icon, font=F_MONO_SM,
                     text_color=col).pack(side="left", padx=(0, 6))
        ctk.CTkLabel(row, text=title, font=("Courier New", 11, "bold"),
                     text_color=col).pack(side="left")
        ctk.CTkFrame(row, fg_color=BORDER_DIM, height=1
                     ).pack(side="left", fill="x", expand=True, padx=(8, 0))

    def _field(self, parent, label, var, placeholder=""):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=2)
        ctk.CTkLabel(row, text=label, font=F_LABEL, text_color=TEXT_DIM,
                     width=70, anchor="w").pack(side="left")
        ctk.CTkEntry(row, textvariable=var, placeholder_text=placeholder,
                     font=F_FIELD, height=32,
                     fg_color=BG_INPUT, border_color=BORDER_MID,
                     text_color=TEXT_HI).pack(side="left", fill="x", expand=True)

    def _vfield(self, parent, label, var, placeholder=""):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=2)
        ctk.CTkLabel(row, text=label, font=F_LABEL, text_color=TEXT_DIM,
                     width=110, anchor="w").pack(side="left")
        ctk.CTkEntry(row, textvariable=var, placeholder_text=placeholder,
                     font=F_FIELD, height=32,
                     fg_color=BG_INPUT, border_color=BORDER_MID,
                     text_color=TEXT_HI).pack(side="left", fill="x", expand=True)

    def _toggle_preset(self):
        state = "normal" if self.create_gitignore.get() else "disabled"
        self.preset_menu.configure(state=state)

    # ── Environment ───────────────────────────────────────────
    def _show_env(self):
        self._env = self._detect_env()
        self.status_bar.update_env(self._env)
        EnvCheckDialog(self, self._env)

    # ── Browse ────────────────────────────────────────────────
    def _browse(self):
        path = filedialog.askdirectory(title="Select Your Project Folder")
        if not path:
            return
        self.project_path.set(path)
        base = os.path.basename(path)
        if not self.repo_name.get():
            self.repo_name.set(base)
        if not self.vercel_proj_name.get():
            self.vercel_proj_name.set(base.lower().replace("_", "-").replace(" ", "-"))
        self._refresh_files()
        self.terminal.log(f"\n⊙  Project: {path}", BLUE_HI)

    def _refresh_files(self):
        self.file_list.populate(self.project_path.get())
        n = len(self.file_list.file_vars)
        self.terminal.log(f"↻  {n} files found", TEXT_DIM)

    # ── Identity ──────────────────────────────────────────────
    def _save_identity(self):
        name  = self.git_username.get().strip()
        email = self.git_email.get().strip()
        if not name or not email:
            messagebox.showerror("Missing", "Both name and email required."); return
        run_cmd(f'git config --global user.name "{name}"')
        run_cmd(f'git config --global user.email "{email}"')
        self.terminal.log(f"💾  Identity saved: {name} <{email}>", GREEN)

    def _open_wizard(self):
        ok, _ = cmd_available("git")
        GitSetupWizard(self, not ok,
                       self.git_username.get(),
                       self.git_email.get(),
                       on_done=self._post_wizard)

    def _open_github(self):
        user = self.gh_username.get().strip()
        repo = self.repo_name.get().strip()
        url  = f"https://github.com/{user}/{repo}" if user and repo else "https://github.com"
        webbrowser.open(url)

    # ── Create Repo ───────────────────────────────────────────
    def _create_repo(self):
        if not self._env.get("gh"):
            messagebox.showwarning("gh CLI not found",
                                   "Install GitHub CLI (cli.github.com) and run 'gh auth login'.")
            return
        if not self._env.get("gh_auth"):
            messagebox.showwarning("Not Authenticated",
                                   "Run 'gh auth login' in a terminal first.")
            return
        suggested = self.repo_name.get().strip() or \
                    os.path.basename(self.project_path.get()) or "my-project"

        def on_created(name):
            self.repo_name.set(name)
            self.terminal.log(f"⊕  Repo created: {name}", GREEN)

        CreateRepoDialog(self, suggested, on_created=on_created)

    # ── Run helper ────────────────────────────────────────────
    def _run(self, cmd, cwd=None, term=None):
        term = term or self.terminal
        path = cwd or self.project_path.get()
        code, out, err = run_cmd(cmd, cwd=path)
        if out: term.log(out, TEXT_MID)
        if err:
            col = RED if code != 0 else TEXT_DIM
            term.log(err, col)
        return code == 0, out, err

    # ── Quick actions ─────────────────────────────────────────
    def _check_path(self):
        if not self.project_path.get():
            self.terminal.log("⚠  No project folder selected.", YELLOW)
            return False
        return True

    def _status(self):
        if not self._check_path(): return
        self.terminal.log("\n── git status ──", CYAN)
        self._run("git status")

    def _git_log(self):
        if not self._check_path(): return
        self.terminal.log("\n── git log (10) ──", CYAN)
        self._run("git log --oneline --graph -10")

    def _pull(self):
        if not self._check_path(): return
        self.terminal.log("\n── git pull ──", CYAN)
        self._run("git pull")

    def _stash(self):
        if not self._check_path(): return
        self.terminal.log("\n── git stash ──", CYAN)
        self._run("git stash")

    def _diff(self):
        if not self._check_path(): return
        self.terminal.log("\n── git diff --stat ──", CYAN)
        self._run("git diff --stat")

    def _soft_reset(self):
        if not self._check_path(): return
        if messagebox.askyesno("Soft Reset",
                               "Undo last commit? (Files stay, commit removed)"):
            self.terminal.log("\n── git reset --soft HEAD~1 ──", YELLOW)
            self._run("git reset --soft HEAD~1")

    # ── .gitignore ────────────────────────────────────────────
    def _write_gitignore(self, path):
        preset   = self.gitignore_preset.get()
        rules    = GITIGNORE_PRESETS.get(preset, [])
        defaults = [".DS_Store", "Thumbs.db", "*.log", ".env", ".env.*",
                    "*.swp", "*.swo", ".vercel/"]
        final    = list(dict.fromkeys(defaults + rules))
        gi_path  = os.path.join(path, ".gitignore")
        with open(gi_path, "w") as f:
            f.write(f"# Generated by DeployPro — preset: {preset}\n\n")
            for line in final:
                f.write(line + "\n")
        self.terminal.log(f"✓  .gitignore ({preset}, {len(final)} rules)", GREEN)

    def _write_readme(self, path):
        repo = self.repo_name.get().strip() or os.path.basename(path)
        rd_path = os.path.join(path, "README.md")
        if os.path.exists(rd_path):
            self.terminal.log("  README.md already exists — skipped.", TEXT_DIM)
            return
        with open(rd_path, "w") as f:
            f.write(f"# {repo}\n\n")
            f.write("<!-- Add your project description here -->\n")
        self.terminal.log("✓  README.md created.", GREEN)

    # ── Validate + confirm deploy ─────────────────────────────
    def _confirm_deploy(self):
        ok, _ = cmd_available("git")
        if not ok:
            messagebox.showerror("Git Not Found",
                                 "Git is not installed.\nOpen Git Wizard from the header."); return

        path   = self.project_path.get()
        repo   = self.repo_name.get().strip()
        user   = self.gh_username.get().strip()
        branch = self.branch.get().strip()
        msg    = self.commit_msg.get().strip()

        errors = []
        if not path:   errors.append("• Project folder not selected")
        if not user:   errors.append("• GitHub Username is empty")
        if not repo:   errors.append("• Repository Name is empty")
        if not branch: errors.append("• Branch is empty")
        if not msg:    errors.append("• Commit message is empty")
        if errors:
            messagebox.showerror("Missing Fields", "\n".join(errors)); return

        selected = self.file_list.get_selected()
        if not selected:
            messagebox.showerror("No Files", "No files selected to commit."); return

        url = f"https://github.com/{user}/{repo}.git"
        gi  = f"\n  .gitignore  : {self.gitignore_preset.get()}" if self.create_gitignore.get() else ""
        rd  = "\n  README.md   : will be created" if self.create_readme.get() else ""

        if messagebox.askyesno("Confirm Deploy",
                               f"⊙  Deploy to GitHub?\n\n"
                               f"  Project     : {os.path.basename(path)}\n"
                               f"  Remote      : {url}\n"
                               f"  Branch      : {branch}\n"
                               f"  Files       : {len(selected)} selected\n"
                               f"  Commit msg  : {msg}"
                               f"{gi}{rd}\n\nProceed?"):
            threading.Thread(target=self._deploy, daemon=True).start()

    # ═══════════════════════════════════════════════════════════
    #  CORE DEPLOY PIPELINE
    # ═══════════════════════════════════════════════════════════
    def _deploy(self):
        path   = self.project_path.get()
        repo   = self.repo_name.get().strip()
        user   = self.gh_username.get().strip()
        branch = self.branch.get().strip()
        msg    = self.commit_msg.get().strip()
        url    = f"https://github.com/{user}/{repo}.git"
        div    = "─" * 56

        def log(m, c=CYAN): self.terminal.log(m, c)

        log(f"\n{div}")
        log(f"⊙  DEPLOY  →  {url}")
        log(f"{div}\n")

        # ── 1  README ──
        log("[ 1/9 ]  README.md…", YELLOW)
        if self.create_readme.get():
            self._write_readme(path)
        else:
            log("  skipped", TEXT_DIM)

        # ── 2  .gitignore ──
        log("\n[ 2/9 ]  .gitignore…", YELLOW)
        if self.create_gitignore.get():
            self._write_gitignore(path)
            self._refresh_files()
        else:
            log("  skipped", TEXT_DIM)

        # ── 3  git available ──
        log("\n[ 3/9 ]  Git check…", YELLOW)
        ok, _ = cmd_available("git")
        if not ok:
            log("✗  Git not found.", RED); return

        # ── 4  git init ──
        log("\n[ 4/9 ]  git init…", YELLOW)
        git_dir = os.path.join(path, ".git")
        if not os.path.isdir(git_dir):
            ok, _, err = self._run("git init", path)
            if not ok: log(f"✗  git init: {err}", RED); return
            log("  ✓  Initialised.", GREEN)
        else:
            log("  ✓  Already a repo.", TEXT_DIM)

        # ── 5  Identity ──
        log("\n[ 5/9 ]  Git identity…", YELLOW)
        name  = git_global("user.name")
        email = git_global("user.email")
        if not name or not email:
            name  = self.git_username.get().strip()
            email = self.git_email.get().strip()
            if name and email:
                run_cmd(f'git config --global user.name "{name}"')
                run_cmd(f'git config --global user.email "{email}"')
                log(f"  ✓  Set: {name} <{email}>", GREEN)
            else:
                log("✗  No identity. Fill Name/Email fields.", RED); return
        else:
            log(f"  ✓  {name} <{email}>", TEXT_DIM)

        # ── 6  Remote ──
        log("\n[ 6/9 ]  Remote origin…", YELLOW)
        self._run("git remote remove origin", path)
        ok, _, err = self._run(f"git remote add origin {url}", path)
        if not ok:
            self._run(f"git remote set-url origin {url}", path)
        log(f"  origin → {url}", TEXT_MID)

        # ── 7  Stage ──
        log("\n[ 7/9 ]  Staging files…", YELLOW)
        selected = self.file_list.get_selected()
        fail_stage = []
        for f in selected:
            ok2, _, _ = self._run(f'git add "{f}"', path)
            if not ok2:
                fail_stage.append(f)
        if fail_stage:
            log(f"  ⚠  {len(fail_stage)} file(s) failed to stage.", YELLOW)
        log(f"  ✓  {len(selected) - len(fail_stage)} files staged.", GREEN)

        # ── 8  Commit ──
        log(f"\n[ 8/9 ]  Commit: \"{msg}\"", YELLOW)
        ok3, out3, err3 = self._run(f'git commit -m "{msg}"', path)
        if not ok3:
            combined = (out3 + err3).lower()
            if "nothing to commit" in combined:
                log("  ℹ  Nothing new to commit — pushing existing.", TEXT_DIM)
            else:
                log(f"  ⚠  Commit note: {err3}", YELLOW)

        # Branch rename
        self._run(f"git branch -M {branch}", path)

        # ── 9  Push ──
        log(f"\n[ 9/9 ]  Push to GitHub…", YELLOW)
        self._smart_push(path, url, branch)

    # ── Smart push with conflict handling ────────────────────
    def _smart_push(self, path, url, branch, attempt=1):
        ok, out, err = self._run(f"git push -u origin {branch}", path)
        combined = (out + err).lower()

        if ok:
            self._deploy_success(url); return

        if any(k in combined for k in ["rejected","fetch first","non-fast-forward"]):
            self.terminal.log("\n⚠  Push rejected — remote has newer commits.", YELLOW)
            if attempt > 2:
                self.terminal.log("✗  Too many retries. Resolve manually.", RED)
                self._deploy_fail(); return
            self.after(0, lambda: self._ask_conflict(path, url, branch, attempt)); return

        if any(k in combined for k in ["authentication","403","401","bad credentials",
                                        "could not read username","permission denied"]):
            self.terminal.log("\n✗  Authentication failed.", RED)
            self.terminal.log("  Use a GitHub PAT (Personal Access Token) as your password.", YELLOW)
            webbrowser.open("https://github.com/settings/tokens/new?scopes=repo")
            self._deploy_fail(); return

        if any(k in combined for k in ["repository not found","does not exist","not found"]):
            self.terminal.log("\n✗  Repository not found on GitHub.", RED)
            self.terminal.log("  Create it at github.com/new  OR use  ⊕ Create Repo.", YELLOW)
            webbrowser.open("https://github.com/new")
            self._deploy_fail(); return

        if "no upstream branch" in combined or "set-upstream" in combined:
            log2 = self.terminal.log
            log2("  ↪  Setting upstream…", TEXT_DIM)
            ok2, _, _ = self._run(f"git push --set-upstream origin {branch}", path)
            if ok2: self._deploy_success(url); return
            self._deploy_fail(); return

        if any(k in combined for k in ["ssl","tls","network","timeout",
                                        "could not resolve","connection refused"]):
            self.terminal.log("\n✗  Network/SSL error.", RED)
            self.terminal.log("  Check internet connection or proxy settings.", YELLOW)
            self._deploy_fail(); return

        if "large files" in combined or "file exceeds" in combined:
            self.terminal.log("\n✗  Large files rejected.", RED)
            self.terminal.log("  Add large files to .gitignore and re-stage.", YELLOW)
            self._deploy_fail(); return

        self.terminal.log(f"\n✗  Push failed: {out or err}", RED)
        self._deploy_fail()

    def _ask_conflict(self, path, url, branch, attempt):
        dlg = ConflictDialog(self, url, branch)
        self.wait_window(dlg)
        choice = dlg.choice
        if choice is None:
            self.terminal.log("  Deploy cancelled.", YELLOW); return

        def resolve():
            if choice == "merge":
                self.terminal.log("\n↙  Pulling (merge)…", CYAN)
                ok, out, err = self._run(f"git pull origin {branch} --no-rebase", path)
                if not ok and "conflict" in (out+err).lower():
                    self.terminal.log("✗  Merge conflicts — resolve manually.", RED); return
            elif choice == "rebase":
                self.terminal.log("\n⊛  Pulling (rebase)…", CYAN)
                ok, out, err = self._run(f"git pull --rebase origin {branch}", path)
                if not ok:
                    self.terminal.log("✗  Rebase failed — check conflicts.", RED); return
            elif choice == "force":
                self.terminal.log("\n⚡  Force pushing…", ORANGE)
                ok, _, _ = self._run(f"git push --force origin {branch}", path)
                if ok: self._deploy_success(url)
                else:  self._deploy_fail()
                return
            self.terminal.log("  ↪  Retrying push…", TEXT_DIM)
            self._smart_push(path, url, branch, attempt + 1)

        threading.Thread(target=resolve, daemon=True).start()

    def _deploy_success(self, url):
        div = "─" * 56
        self.terminal.log(f"\n{div}", GREEN)
        self.terminal.log("✓  DEPLOYED SUCCESSFULLY!", GREEN)
        self.terminal.log(f"⬡  {url}", BLUE_HI)
        self.terminal.log(div, GREEN)

    def _deploy_fail(self):
        div = "─" * 56
        self.terminal.log(f"\n{div}", RED)
        self.terminal.log("✗  DEPLOY FAILED  —  See output above.", RED)
        self.terminal.log(div, RED)

    # ═══════════════════════════════════════════════════════════
    #  VERCEL PIPELINE
    # ═══════════════════════════════════════════════════════════
    def _vercel_deploy(self):
        path = self.project_path.get()
        if not path:
            messagebox.showerror("No Project", "Select a project folder first (GitHub tab)."); return
        if not self._env.get("vercel"):
            messagebox.showerror("Vercel CLI Missing",
                                 "Vercel CLI not found.\n"
                                 "Install: npm i -g vercel\n"
                                 "Then run: vercel login"); return

        # Check if they want to deploy
        proj   = self.vercel_proj_name.get().strip() or os.path.basename(path)
        is_prod = self.vercel_prod.get()

        choice = messagebox.askyesnocancel(
            "Vercel Deploy",
            f"Deploy  {proj}  to Vercel?\n\n"
            f"  Mode: {'PRODUCTION 🚀' if is_prod else 'Preview 🔍'}\n"
            f"  Path: {path}\n\n"
            f"Production deploys go live immediately.\n"
            f"Preview deploys give a test URL.\n\n"
            f"Yes = Deploy   No = Open dashboard   Cancel = Abort"
        )
        if choice is None: return
        if choice is False:
            webbrowser.open("https://vercel.com/dashboard"); return

        threading.Thread(target=self._run_vercel_deploy,
                         args=(path, is_prod), daemon=True).start()

    def _run_vercel_deploy(self, path, is_prod):
        vt = self.vercel_terminal
        div = "─" * 56

        vt.log(f"\n{div}")
        vt.log(f"◈  VERCEL DEPLOY  {'(PRODUCTION)' if is_prod else '(preview)'}")
        vt.log(f"{div}\n")

        vt.log("[ 1/4 ]  Checking Vercel auth…", YELLOW)
        auth, user = vercel_logged_in()
        if not auth:
            vt.log("✗  Not logged in. Running 'vercel login'…", RED)
            vt.log("  A browser window will open for authentication.", TEXT_DIM)
            run_cmd("vercel login", cwd=path)
            auth, user = vercel_logged_in()
            if not auth:
                vt.log("✗  Login failed. Try: vercel login in terminal.", RED); return
        vt.log(f"  ✓  Logged in as {user}", GREEN)

        vt.log("\n[ 2/4 ]  Running Vercel deploy…", YELLOW)
        prod_flag = "--prod" if is_prod else ""
        cmd = f"vercel {prod_flag} --confirm --yes"
        vt.log(f"  $ {cmd}", TEXT_DIM)

        try:
            proc = subprocess.Popen(
                cmd, cwd=path, shell=True,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True
            )
            deploy_url = None
            for line in proc.stdout:
                line = line.rstrip()
                vt.log(f"  {line}", TEXT_MID)
                if "https://" in line:
                    urls = re.findall(r'https://[^\s]+', line)
                    if urls:
                        deploy_url = urls[-1]
            proc.wait()
            rc = proc.returncode
        except Exception as e:
            vt.log(f"✗  Error: {e}", RED); return

        vt.log("\n[ 3/4 ]  Checking result…", YELLOW)
        if rc != 0:
            vt.log("✗  Vercel deploy failed.", RED)
            vt.log("  Check output above for framework/config errors.", YELLOW); return

        vt.log("  ✓  Deploy successful.", GREEN)

        vt.log("\n[ 4/4 ]  Deployment info…", YELLOW)
        if deploy_url:
            vt.log(f"\n{div}", GREEN)
            vt.log("✓  DEPLOYED TO VERCEL!", GREEN)
            vt.log(f"⬡  {deploy_url}", VIOLET_HI)
            vt.log(div, GREEN)
            if messagebox.askyesno("Deployed!", f"Open deployment in browser?\n{deploy_url}"):
                webbrowser.open(deploy_url)
        else:
            vt.log("✓  Deploy completed (URL not captured — check terminal).", GREEN)

    def _vercel_login(self):
        self.vercel_terminal.log("\n── vercel login ──", VIOLET_HI)
        self.vercel_terminal.log("  Opening browser for Vercel authentication…", TEXT_DIM)
        threading.Thread(
            target=lambda: run_cmd("vercel login", cwd=self.project_path.get() or os.getcwd()),
            daemon=True).start()

    def _vercel_ls(self):
        self.vercel_terminal.log("\n── vercel ls ──", VIOLET_HI)
        threading.Thread(target=lambda: [
            self.vercel_terminal.log(o or e, TEXT_MID)
            for _, o, e in [run_cmd("vercel ls", cwd=self.project_path.get() or os.getcwd())]
        ], daemon=True).start()

    def _vercel_logs(self):
        self.vercel_terminal.log("\n── vercel logs ──", VIOLET_HI)
        proj = self.vercel_proj_name.get().strip()
        if not proj:
            self.vercel_terminal.log("  Set Project Name first.", YELLOW); return
        threading.Thread(target=lambda: [
            self.vercel_terminal.log(o or e, TEXT_MID)
            for _, o, e in [run_cmd(f"vercel logs {proj}",
                                     cwd=self.project_path.get() or os.getcwd())]
        ], daemon=True).start()


# ═══════════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = DeployPro()
    app.mainloop()
