"""
Pyhub Pro v2.0
Production-level GitHub deployment GUI tool.
Handles: Git install detection, config wizard, all push/pull conflicts,
         smart error recovery, splash screen, and full EXE compatibility.

Requirements:
    pip install customtkinter
    pip install pyinstaller   (for EXE build)

Build EXE:
    pyinstaller --onefile --windowed --icon=icon.ico Pyhub_pro.py
"""

import customtkinter as ctk
import subprocess, threading, os, sys, time, shutil, webbrowser, re
from tkinter import filedialog, messagebox
import tkinter as tk

# ══════════════════════════════════════════════════════════════════
#  THEME
# ══════════════════════════════════════════════════════════════════
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

ACCENT   = "#00FF88"
BG_DEEP  = "#0D0F14"
BG_CARD  = "#13161E"
BG_PANEL = "#1A1D28"
BORDER   = "#2A2D3E"
TEXT_DIM = "#6B7280"
TEXT_MID = "#9CA3AF"
TEXT_HI  = "#F9FAFB"
RED      = "#FF4757"
YELLOW   = "#FFD32A"
BLUE     = "#38BDF8"

F_MONO    = ("Courier New", 13)
F_MONO_SM = ("Courier New", 12)
F_MONO_LG = ("Courier New", 16, "bold")
F_MONO_H  = ("Courier New", 24, "bold")
F_UI      = ("Segoe UI", 13)
F_UI_SM   = ("Segoe UI", 12)
F_UI_LG   = ("Segoe UI", 15, "bold")
F_LABEL   = ("Courier New", 12)
F_FIELD   = ("Courier New", 13)

GITIGNORE_PRESETS = {
    "Python":        ["__pycache__/","*.pyc","*.pyo",".env","venv/",".venv/","dist/","build/","*.egg-info/"],
    "Node.js":       ["node_modules/",".env","dist/","build/",".DS_Store","*.log","package-lock.json"],
    "Web":           [".DS_Store","*.log",".env","dist/","build/"],
    "Kali/Security": ["*.log","*.pcap","*.cap","credentials.txt","passwords.txt","*.key",".env","loot/","output/"],
    "Java":          ["target/","*.class","*.jar","*.war",".gradle/","build/",".idea/"],
    "C/C++":         ["*.o","*.obj","*.exe","*.out","*.a","*.so","build/","CMakeFiles/"],
    "Go":            ["*.exe","vendor/","bin/"],
    "Rust":          ["target/","Cargo.lock"],
    "Custom":        [],
}


# ══════════════════════════════════════════════════════════════════
#  HELPERS — run subprocess
# ══════════════════════════════════════════════════════════════════
def run_cmd(cmd, cwd=None):
    """Run shell command, return (returncode, stdout, stderr)."""
    try:
        r = subprocess.run(
            cmd, cwd=cwd, capture_output=True,
            text=True, shell=True, timeout=60
        )
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out."
    except Exception as e:
        return -1, "", str(e)


def git_available():
    code, out, _ = run_cmd("git --version")
    return code == 0


def get_git_global(key):
    _, out, _ = run_cmd(f'git config --global {key}')
    return out.strip()


# ══════════════════════════════════════════════════════════════════
#  SPLASH / LOADING SCREEN
# ══════════════════════════════════════════════════════════════════
class SplashScreen(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.overrideredirect(True)
        self.configure(fg_color=BG_DEEP)
        self.geometry("540x360")
        self._center()
        self.lift(); self.attributes("-topmost", True)
        self._build()

    def _center(self):
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"540x360+{(sw-540)//2}+{(sh-360)//2}")

    def _build(self):
        ctk.CTkLabel(self, text="⚡", font=("Segoe UI Emoji", 56)).pack(pady=(32, 2))
        ctk.CTkLabel(self, text="Pyhub Pro",
                     font=F_MONO_H, text_color=ACCENT).pack()
        ctk.CTkLabel(self, text="Universal GitHub Deployment Tool",
                     font=F_MONO_SM, text_color=TEXT_DIM).pack(pady=(4, 24))

        self.pb = ctk.CTkProgressBar(self, width=400, height=12,
                                      fg_color=BG_PANEL, progress_color=ACCENT)
        self.pb.pack(); self.pb.set(0)

        self.lbl = ctk.CTkLabel(self, text="Starting up…",
                                 font=F_MONO_SM, text_color=TEXT_DIM)
        self.lbl.pack(pady=(10, 0))

        ctk.CTkLabel(self, text="v2.0  ·  Made by CYBERSAREEN",
                     font=F_MONO_SM, text_color=TEXT_DIM).pack(side="bottom", pady=14)

    def set_progress(self, val, text=""):
        self.pb.set(val)
        if text: self.lbl.configure(text=text)
        self.update()


# ══════════════════════════════════════════════════════════════════
#  GIT SETUP WIZARD  (shown if Git not installed or not configured)
# ══════════════════════════════════════════════════════════════════
class GitSetupWizard(ctk.CTkToplevel):
    def __init__(self, parent, git_missing, current_name="", current_email="", on_done=None):
        super().__init__(parent)
        self.title("Git Setup Wizard — Pyhub Pro")
        self.geometry("580x540")
        self.resizable(False, False)
        self.configure(fg_color=BG_DEEP)
        self.grab_set()
        self.on_done = on_done
        self.git_missing = git_missing
        self._center()
        self._build(current_name, current_email)

    def _center(self):
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"580x540+{(sw-580)//2}+{(sh-540)//2}")

    def _build(self, cur_name, cur_email):
        ctk.CTkLabel(self, text="🔧  Git Setup Wizard",
                     font=F_MONO_LG, text_color=ACCENT).pack(pady=(22, 2))

        if self.git_missing:
            msg = "Git is NOT installed. Please install it first, then re-open Pyhub Pro."
        else:
            msg = "Git is installed ✅  —  Please complete your global identity below."

        ctk.CTkLabel(self, text=msg, font=F_UI, text_color=TEXT_MID,
                     wraplength=480, justify="center").pack(pady=(2, 16))

        # Install section
        if self.git_missing:
            card = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=10,
                                border_color=BORDER, border_width=1)
            card.pack(fill="x", padx=28, pady=(0, 12))
            ctk.CTkLabel(card, text="Step 1 — Download & Install Git",
                         font=F_UI_LG, text_color=TEXT_HI).pack(anchor="w", padx=18, pady=(14, 2))
            ctk.CTkLabel(card,
                         text="Download Git for Windows from the official site.\n"
                              "Run the installer with default settings, then click 'Re-check'.",
                         font=F_UI_SM, text_color=TEXT_MID, wraplength=500, justify="left"
                         ).pack(anchor="w", padx=18, pady=(0, 8))
            btn_row = ctk.CTkFrame(card, fg_color="transparent")
            btn_row.pack(fill="x", padx=18, pady=(0, 14))
            ctk.CTkButton(btn_row, text="🌐 Open git-scm.com", width=200, height=36,
                          font=F_MONO, fg_color=BLUE, hover_color="#2563EB",
                          text_color="#000",
                          command=lambda: webbrowser.open("https://git-scm.com/download/win")
                          ).pack(side="left", padx=(0, 10))
            ctk.CTkButton(btn_row, text="↻ Re-check", width=120, height=36,
                          font=F_MONO, fg_color=BG_PANEL, hover_color=BORDER,
                          text_color=ACCENT, border_color=ACCENT, border_width=1,
                          command=self._recheck).pack(side="left")

        # Identity section
        id_card = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=10,
                               border_color=BORDER, border_width=1)
        id_card.pack(fill="x", padx=28, pady=(0, 12))
        step = "Step 2" if self.git_missing else "Step 1"
        ctk.CTkLabel(id_card, text=f"{step} — Set Git Global Identity",
                     font=F_UI_LG, text_color=TEXT_HI).pack(anchor="w", padx=18, pady=(14, 6))

        self.name_var  = ctk.StringVar(value=cur_name)
        self.email_var = ctk.StringVar(value=cur_email)
        self._wiz_field(id_card, "Full Name / Username", self.name_var,  "e.g.  Jane Doe")
        self._wiz_field(id_card, "GitHub Email",         self.email_var, "e.g.  jane@example.com")

        ctk.CTkButton(id_card, text="💾  Save Identity", height=38, font=F_MONO,
                      fg_color=ACCENT, hover_color="#00CC66", text_color="#000",
                      command=self._save_identity).pack(fill="x", padx=18, pady=(8, 14))

        # PAT hint
        pat_card = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=10,
                                border_color=BORDER, border_width=1)
        pat_card.pack(fill="x", padx=28, pady=(0, 12))
        step2 = "Step 3" if self.git_missing else "Step 2"
        ctk.CTkLabel(pat_card, text=f"{step2} — Personal Access Token (PAT)",
                     font=F_UI_LG, text_color=TEXT_HI).pack(anchor="w", padx=18, pady=(14, 2))
        ctk.CTkLabel(pat_card,
                     text="GitHub requires a PAT instead of a password.\n"
                          "When Git prompts for password, paste your PAT.\n"
                          "Generate one at: GitHub → Settings → Developer Settings → Tokens.",
                     font=F_UI_SM, text_color=TEXT_MID, wraplength=500, justify="left"
                     ).pack(anchor="w", padx=18, pady=(0, 8))
        ctk.CTkButton(pat_card, text="🌐 Open GitHub Token Page", height=34, font=F_MONO,
                      fg_color=BG_PANEL, hover_color=BORDER, text_color=ACCENT,
                      border_color=ACCENT, border_width=1,
                      command=lambda: webbrowser.open(
                          "https://github.com/settings/tokens/new?scopes=repo&description=PyhubPro")
                      ).pack(anchor="w", padx=18, pady=(0, 14))

        ctk.CTkButton(self, text="✅  Done — Close Wizard", height=44, font=F_MONO_LG,
                      fg_color=ACCENT, hover_color="#00CC66", text_color="#000",
                      command=self._finish).pack(fill="x", padx=28, pady=(4, 18))

    def _wiz_field(self, parent, label, var, placeholder):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=18, pady=3)
        ctk.CTkLabel(row, text=label, font=F_LABEL, text_color=TEXT_DIM,
                     width=180, anchor="w").pack(side="left")
        ctk.CTkEntry(row, textvariable=var, placeholder_text=placeholder,
                     font=F_FIELD, height=34,
                     fg_color=BG_DEEP, border_color=BORDER,
                     text_color=TEXT_HI).pack(side="left", fill="x", expand=True)

    def _save_identity(self):
        name  = self.name_var.get().strip()
        email = self.email_var.get().strip()
        if not name or not email:
            messagebox.showerror("Missing", "Both name and email are required."); return
        run_cmd(f'git config --global user.name "{name}"')
        run_cmd(f'git config --global user.email "{email}"')
        messagebox.showinfo("Saved", f"Git identity saved:\n  Name : {name}\n  Email: {email}")

    def _recheck(self):
        if git_available():
            messagebox.showinfo("Git Found!", "Git is now installed ✅\nClose this wizard and re-open Pyhub Pro.")
        else:
            messagebox.showwarning("Not Found", "Git still not detected.\nMake sure installation completed and restart the app.")

    def _finish(self):
        self.grab_release()
        self.destroy()
        if self.on_done: self.on_done()


# ══════════════════════════════════════════════════════════════════
#  CONFLICT RESOLUTION DIALOG
# ══════════════════════════════════════════════════════════════════
class ConflictDialog(ctk.CTkToplevel):
    """Ask user what to do when push is rejected."""
    def __init__(self, parent, url, branch):
        super().__init__(parent)
        self.title("Push Conflict — Resolve")
        self.geometry("520x380")
        self.resizable(False, False)
        self.configure(fg_color=BG_DEEP)
        self.grab_set()
        self.choice = None
        self._center()
        self._build(url, branch)

    def _center(self):
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"520x380+{(sw-520)//2}+{(sh-380)//2}")

    def _build(self, url, branch):
        ctk.CTkLabel(self, text="⚠️  Push Rejected", font=F_MONO_LG,
                     text_color=YELLOW).pack(pady=(24, 4))
        ctk.CTkLabel(self,
                     text=f"Remote has commits your local copy doesn't have.\n"
                          f"  Remote: {url}\n  Branch: {branch}\n\n"
                          f"Choose how to resolve:",
                     font=F_UI, text_color=TEXT_MID, justify="left",
                     wraplength=460).pack(padx=28, pady=(0, 18))

        opts = [
            ("🔄  Pull & Merge then Push",
             "Fetches remote changes and merges.\nSafe — preserves both histories.",
             "merge"),
            ("♻️  Force Push (overwrite remote)",
             "YOUR local files will replace remote.\nWarning: remote commits will be lost.",
             "force"),
            ("📥  Pull with Rebase then Push",
             "Reapplies your commits on top of remote.\nClean history, advanced option.",
             "rebase"),
        ]
        for label, desc, key in opts:
            btn = ctk.CTkButton(self, text=label, height=48, font=F_MONO,
                                fg_color=BG_PANEL, hover_color=BORDER,
                                text_color=ACCENT, border_color=BORDER, border_width=1,
                                anchor="w",
                                command=lambda k=key: self._pick(k))
            btn.pack(fill="x", padx=28, pady=4)
            ctk.CTkLabel(self, text=f"   {desc}", font=F_UI_SM,
                         text_color=TEXT_DIM, justify="left").pack(anchor="w", padx=36)

        ctk.CTkButton(self, text="✖  Cancel deploy", height=36, font=F_MONO,
                      fg_color=BG_DEEP, hover_color=RED, text_color=RED,
                      border_color=RED, border_width=1,
                      command=lambda: self._pick(None)).pack(pady=(12, 0))

    def _pick(self, choice):
        self.choice = choice
        self.grab_release()
        self.destroy()


# ══════════════════════════════════════════════════════════════════
#  TERMINAL WIDGET
# ══════════════════════════════════════════════════════════════════
class TerminalBox(ctk.CTkTextbox):
    def __init__(self, master, **kw):
        super().__init__(master, **kw)
        self.configure(state="disabled", font=("Courier New", 13),
                       text_color=ACCENT, fg_color="#0A0C10",
                       border_color=BORDER, border_width=1)

    def log(self, msg, color=ACCENT):
        self.configure(state="normal")
        self.insert("end", msg + "\n")
        self.configure(state="disabled")
        self.see("end")

    def clear(self):
        self.configure(state="normal")
        self.delete("1.0", "end")
        self.configure(state="disabled")


# ══════════════════════════════════════════════════════════════════
#  FILE LIST WIDGET
# ══════════════════════════════════════════════════════════════════
class FileListFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, **kw):
        super().__init__(master, **kw)
        self.file_vars = {}

    def populate(self, path):
        for w in self.winfo_children(): w.destroy()
        self.file_vars.clear()
        if not path or not os.path.isdir(path): return
        skip_dirs = {'.git', '__pycache__', 'node_modules', '.venv', 'venv',
                     'dist', 'build', '.idea', '.vs', 'target'}
        all_files = []
        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            for f in files:
                rel = os.path.relpath(os.path.join(root, f), path)
                all_files.append(rel)
        for f in sorted(all_files):
            var = ctk.BooleanVar(value=True)
            row = ctk.CTkFrame(self, fg_color="transparent")
            row.pack(fill="x", pady=1)
            ctk.CTkCheckBox(row, text=f, variable=var,
                            font=("Courier New", 12), text_color=TEXT_MID,
                            fg_color=ACCENT, hover_color="#00CC66",
                            checkmark_color="#000", border_color=BORDER
                            ).pack(anchor="w", padx=8)
            self.file_vars[f] = var

    def get_selected(self):
        return [f for f, v in self.file_vars.items() if v.get()]

    def select_all(self):
        for v in self.file_vars.values(): v.set(True)

    def deselect_all(self):
        for v in self.file_vars.values(): v.set(False)


# ══════════════════════════════════════════════════════════════════
#  MAIN APPLICATION
# ══════════════════════════════════════════════════════════════════
class PyhubPro(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.withdraw()  # hide until splash done

        self.title("⚡ Pyhub Pro")
        self.geometry("1240x860")
        self.minsize(1060, 720)
        self.configure(fg_color=BG_DEEP)

        # State vars — intentionally blank (no hardcoded username)
        self.project_path     = ctk.StringVar()
        self.repo_name        = ctk.StringVar()
        self.git_username     = ctk.StringVar()
        self.git_email        = ctk.StringVar()
        self.gh_username      = ctk.StringVar()
        self.branch           = ctk.StringVar(value="main")
        self.commit_msg       = ctk.StringVar(value="Initial commit")
        self.gitignore_preset = ctk.StringVar(value="Python")
        self.create_gitignore = ctk.BooleanVar(value=True)

        # Show splash then boot
        self.splash = SplashScreen(self)
        threading.Thread(target=self._boot, daemon=True).start()

    # ── Boot sequence ─────────────────────────────────────────────
    def _boot(self):
        sp = self.splash
        sp.set_progress(0.10, "Checking Git installation…")
        time.sleep(0.4)

        self._git_ok = git_available()

        sp.set_progress(0.35, "Reading Git identity…")
        time.sleep(0.3)
        name  = get_git_global("user.name")
        email = get_git_global("user.email")
        self.git_username.set(name)
        self.git_email.set(email)
        # Try to derive GitHub username from email
        if not self.gh_username.get() and email:
            self.gh_username.set(email.split("@")[0])

        sp.set_progress(0.60, "Building UI…")
        time.sleep(0.3)
        self.after(0, self._build_ui)

        sp.set_progress(0.85, "Finalising…")
        time.sleep(0.4)
        sp.set_progress(1.0, "Ready!")
        time.sleep(0.5)

        self.after(0, self._finish_boot, name, email)

    def _finish_boot(self, name, email):
        self.splash.destroy()
        self.deiconify()
        self._center()

        need_wizard = (not self._git_ok) or (not name) or (not email)
        if need_wizard:
            reason = "Git not found." if not self._git_ok else "Git identity not configured."
            self.terminal.log(f"⚠  {reason}  Opening Setup Wizard…", YELLOW)
            self.after(400, lambda: GitSetupWizard(
                self, not self._git_ok, name, email,
                on_done=self._post_wizard
            ))
        else:
            self.terminal.log("✅  Git detected and configured.", ACCENT)
            self.terminal.log(f"   Identity : {name} <{email}>", TEXT_MID)
            self.terminal.log("📂  Select a project folder to begin.", TEXT_DIM)

    def _post_wizard(self):
        name  = get_git_global("user.name")
        email = get_git_global("user.email")
        self.git_username.set(name)
        self.git_email.set(email)
        self.terminal.log(f"✅  Identity confirmed: {name} <{email}>", ACCENT)

    def _center(self):
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        x, y = (sw - 1240) // 2, (sh - 860) // 2
        self.geometry(f"1240x860+{x}+{y}")

    # ── UI Build ──────────────────────────────────────────────────
    def _build_ui(self):
        # ── Header ──
        hdr = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=0, height=68)
        hdr.pack(fill="x"); hdr.pack_propagate(False)

        ctk.CTkLabel(hdr, text="⚡ Pyhub Pro",
                     font=("Courier New", 22, "bold"), text_color=ACCENT
                     ).pack(side="left", padx=24)
        ctk.CTkLabel(hdr, text="Universal GitHub Deployment Tool",
                     font=F_MONO_SM, text_color=TEXT_DIM).pack(side="left")
        ctk.CTkLabel(hdr, text="Made by CYBERSAREEN  ·  v2.0",
                     font=F_MONO_SM, text_color=TEXT_DIM).pack(side="right", padx=24)

        # ── Body ──
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=16, pady=12)
        body.columnconfigure(0, weight=38)
        body.columnconfigure(1, weight=62)
        body.rowconfigure(0, weight=1)

        self._build_left(body)
        self._build_right(body)

    # ─────────────────────────────────────────────────────────────
    def _build_left(self, parent):
        left = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=12,
                             border_color=BORDER, border_width=1)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        # ── Project ──
        self._section(left, "📁  PROJECT FOLDER")
        pr = ctk.CTkFrame(left, fg_color="transparent")
        pr.pack(fill="x", padx=16, pady=(0, 12))
        ctk.CTkEntry(pr, textvariable=self.project_path,
                     placeholder_text="Click Browse to select your project…",
                     font=F_FIELD, height=38,
                     fg_color=BG_DEEP, border_color=BORDER, text_color=TEXT_HI
                     ).pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(pr, text="Browse", width=88, height=38,
                      font=("Courier New", 13, "bold"),
                      fg_color=BG_PANEL, hover_color=BORDER,
                      text_color=ACCENT, border_color=ACCENT, border_width=1,
                      command=self._browse).pack(side="right")

        # ── Git Identity ──
        self._section(left, "👤  GIT IDENTITY")
        self._field(left, "Full Name",    self.git_username, "Your name for commits")
        self._field(left, "Git Email",    self.git_email,    "Email linked to GitHub")
        ctk.CTkButton(left, text="💾  Save to Git Global Config", height=34,
                      font=F_MONO, fg_color=BG_PANEL, hover_color=BORDER,
                      text_color=ACCENT, border_color=BORDER, border_width=1,
                      command=self._save_identity).pack(fill="x", padx=16, pady=(2, 8))

        # ── GitHub Config ──
        self._section(left, "⚙️  GITHUB CONFIG")
        self._field(left, "GitHub Username", self.gh_username,  "Your GitHub account name")
        self._field(left, "Repository Name", self.repo_name,    "Target repo (must exist on GitHub)")
        self._field(left, "Branch",          self.branch,       "main / master / dev")
        self._field(left, "Commit Message",  self.commit_msg,   "Describe your changes")

        # ── Options ──
        opt = ctk.CTkFrame(left, fg_color=BG_PANEL, corner_radius=8)
        opt.pack(fill="x", padx=16, pady=8)
        ctk.CTkCheckBox(opt, text="Auto-create .gitignore",
                        variable=self.create_gitignore, font=F_LABEL,
                        text_color=TEXT_MID, fg_color=ACCENT,
                        hover_color="#00CC66", checkmark_color="#000",
                        border_color=BORDER,
                        command=self._toggle_preset).pack(anchor="w", padx=12, pady=(10, 4))
        pr2 = ctk.CTkFrame(opt, fg_color="transparent")
        pr2.pack(fill="x", padx=12, pady=(0, 10))
        ctk.CTkLabel(pr2, text="Preset:", font=F_LABEL, text_color=TEXT_DIM).pack(side="left")
        self.preset_menu = ctk.CTkOptionMenu(
            pr2, variable=self.gitignore_preset,
            values=list(GITIGNORE_PRESETS.keys()),
            font=F_LABEL, height=32,
            fg_color=BG_DEEP, button_color=BG_PANEL,
            button_hover_color=BORDER, text_color=ACCENT,
            dropdown_fg_color=BG_PANEL)
        self.preset_menu.pack(side="left", padx=8)

        # ── Deploy Button ──
        ctk.CTkButton(left, text="🚀  DEPLOY TO GITHUB",
                      font=("Courier New", 16, "bold"), height=56,
                      fg_color=ACCENT, hover_color="#00CC66", text_color="#000",
                      corner_radius=10,
                      command=self._confirm_deploy).pack(fill="x", padx=16, pady=(12, 8))

        # ── Quick Actions ──
        self._section(left, "⚡  QUICK ACTIONS")
        qa = ctk.CTkFrame(left, fg_color="transparent")
        qa.pack(fill="x", padx=16, pady=(0, 8))
        for txt, cmd in [("git status", self._status),
                         ("git log",    self._git_log),
                         ("git pull",   self._pull)]:
            ctk.CTkButton(qa, text=txt, height=34, font=F_MONO,
                          fg_color=BG_PANEL, hover_color=BORDER,
                          text_color=ACCENT, border_color=BORDER, border_width=1,
                          command=cmd).pack(side="left", expand=True, padx=3)

        qa2 = ctk.CTkFrame(left, fg_color="transparent")
        qa2.pack(fill="x", padx=16, pady=(0, 12))
        ctk.CTkButton(qa2, text="🔧 Git Wizard", height=34, font=F_MONO,
                      fg_color=BG_PANEL, hover_color=BORDER,
                      text_color=YELLOW, border_color=BORDER, border_width=1,
                      command=self._open_wizard).pack(side="left", expand=True, padx=3)
        ctk.CTkButton(qa2, text="🌐 Open GitHub", height=34, font=F_MONO,
                      fg_color=BG_PANEL, hover_color=BORDER,
                      text_color=BLUE, border_color=BORDER, border_width=1,
                      command=self._open_github).pack(side="left", expand=True, padx=3)

    # ─────────────────────────────────────────────────────────────
    def _build_right(self, parent):
        right = ctk.CTkFrame(parent, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew")
        right.rowconfigure(0, weight=5)
        right.rowconfigure(1, weight=4)
        right.columnconfigure(0, weight=1)

        # ── File list ──
        fl = ctk.CTkFrame(right, fg_color=BG_CARD, corner_radius=12,
                           border_color=BORDER, border_width=1)
        fl.grid(row=0, column=0, sticky="nsew", pady=(0, 8))
        fl.rowconfigure(1, weight=1); fl.columnconfigure(0, weight=1)

        hr = ctk.CTkFrame(fl, fg_color="transparent")
        hr.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 4))
        ctk.CTkLabel(hr, text="📂  FILES TO COMMIT",
                     font=("Courier New", 13, "bold"), text_color=ACCENT).pack(side="left")
        for txt, cmd, col in [("None", lambda: self.file_list.deselect_all(), TEXT_DIM),
                               ("All",  lambda: self.file_list.select_all(),   ACCENT),
                               ("↻ Refresh", self._refresh_files, TEXT_MID)]:
            ctk.CTkButton(hr, text=txt, width=80, height=30, font=F_MONO_SM,
                          fg_color=BG_PANEL, hover_color=BORDER, text_color=col,
                          border_color=BORDER, border_width=1,
                          command=cmd).pack(side="right", padx=3)

        self.file_list = FileListFrame(fl, fg_color=BG_DEEP, corner_radius=8)
        self.file_list.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))

        # ── Terminal ──
        term = ctk.CTkFrame(right, fg_color=BG_CARD, corner_radius=12,
                             border_color=BORDER, border_width=1)
        term.grid(row=1, column=0, sticky="nsew")
        term.rowconfigure(1, weight=1); term.columnconfigure(0, weight=1)

        tr = ctk.CTkFrame(term, fg_color="transparent")
        tr.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 4))
        ctk.CTkLabel(tr, text="⬛  TERMINAL OUTPUT",
                     font=("Courier New", 13, "bold"), text_color=ACCENT).pack(side="left")
        ctk.CTkButton(tr, text="Clear", width=64, height=28, font=F_MONO_SM,
                      fg_color=BG_PANEL, hover_color=BORDER,
                      text_color=TEXT_DIM, border_color=BORDER, border_width=1,
                      command=lambda: self.terminal.clear()).pack(side="right")

        self.terminal = TerminalBox(term, height=200)
        self.terminal.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))

    # ── UI helpers ────────────────────────────────────────────────
    def _section(self, parent, title):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=(12, 4))
        ctk.CTkLabel(row, text=title, font=("Courier New", 12, "bold"),
                     text_color=ACCENT).pack(side="left")
        ctk.CTkFrame(row, fg_color=BORDER, height=1
                     ).pack(side="left", fill="x", expand=True, padx=(8, 0))

    def _field(self, parent, label, var, placeholder=""):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=3)
        ctk.CTkLabel(row, text=label, font=F_LABEL, text_color=TEXT_DIM,
                     width=148, anchor="w").pack(side="left")
        ctk.CTkEntry(row, textvariable=var, placeholder_text=placeholder,
                     font=F_FIELD, height=34,
                     fg_color=BG_DEEP, border_color=BORDER,
                     text_color=TEXT_HI).pack(side="left", fill="x", expand=True)

    def _toggle_preset(self):
        self.preset_menu.configure(
            state="normal" if self.create_gitignore.get() else "disabled")

    # ── Actions ───────────────────────────────────────────────────
    def _browse(self):
        path = filedialog.askdirectory(title="Select Your Project Folder")
        if not path: return
        self.project_path.set(path)
        if not self.repo_name.get():
            self.repo_name.set(os.path.basename(path))
        self._refresh_files()
        self.terminal.log(f"\n📁  Project: {path}", ACCENT)

    def _refresh_files(self):
        self.file_list.populate(self.project_path.get())
        n = len(self.file_list.file_vars)
        self.terminal.log(f"↻  Found {n} files", TEXT_DIM)

    def _save_identity(self):
        name  = self.git_username.get().strip()
        email = self.git_email.get().strip()
        if not name or not email:
            messagebox.showerror("Missing", "Please fill in both name and email."); return
        run_cmd(f'git config --global user.name "{name}"')
        run_cmd(f'git config --global user.email "{email}"')
        self.terminal.log(f"💾  Identity saved: {name} <{email}>", ACCENT)

    def _open_wizard(self):
        GitSetupWizard(self, not git_available(),
                       self.git_username.get(), self.git_email.get(),
                       on_done=self._post_wizard)

    def _post_wizard(self):
        name  = get_git_global("user.name")
        email = get_git_global("user.email")
        self.git_username.set(name)
        self.git_email.set(email)
        self.terminal.log(f"✅  Identity updated: {name} <{email}>", ACCENT)

    def _open_github(self):
        user = self.gh_username.get().strip()
        repo = self.repo_name.get().strip()
        url  = f"https://github.com/{user}/{repo}" if user and repo else "https://github.com"
        webbrowser.open(url)

    # ── Run a git command and log output ─────────────────────────
    def _run(self, cmd, cwd=None):
        path = cwd or self.project_path.get()
        code, out, err = run_cmd(cmd, cwd=path)
        if out: self.terminal.log(out, TEXT_MID)
        if err:
            col = RED if code != 0 else TEXT_DIM
            self.terminal.log(err, col)
        return code == 0, out, err

    # ── Quick actions ─────────────────────────────────────────────
    def _status(self):
        if not self._check_path(): return
        self.terminal.log("\n── git status ──", ACCENT)
        self._run("git status")

    def _git_log(self):
        if not self._check_path(): return
        self.terminal.log("\n── git log (last 8) ──", ACCENT)
        self._run("git log --oneline -8")

    def _pull(self):
        if not self._check_path(): return
        self.terminal.log("\n── git pull ──", ACCENT)
        ok, out, err = self._run("git pull")
        if not ok:
            self.terminal.log("⚠  Pull failed. Check remote config.", YELLOW)

    def _check_path(self):
        if not self.project_path.get():
            self.terminal.log("⚠  No project folder selected.", YELLOW)
            return False
        return True

    # ── .gitignore ────────────────────────────────────────────────
    def _write_gitignore(self, path):
        preset  = self.gitignore_preset.get()
        rules   = GITIGNORE_PRESETS.get(preset, [])
        defaults = [".DS_Store", "Thumbs.db", "*.log", ".env", ".env.*", "*.swp"]
        final   = list(dict.fromkeys(defaults + rules))
        with open(os.path.join(path, ".gitignore"), "w") as f:
            f.write(f"# Generated by Pyhub Pro — preset: {preset}\n\n")
            for line in final:
                f.write(line + "\n")
        self.terminal.log(f"✅  .gitignore ({preset}, {len(final)} rules)", ACCENT)

    # ── Validate before deploy ────────────────────────────────────
    def _confirm_deploy(self):
        if not git_available():
            messagebox.showerror("Git Not Found",
                                 "Git is not installed or not in PATH.\n"
                                 "Open Git Wizard from Quick Actions to install.")
            return

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
        gi  = f"\n📄  .gitignore: {self.gitignore_preset.get()}" if self.create_gitignore.get() else ""

        if messagebox.askyesno("Confirm Deploy",
                               f"🚀  Ready to deploy?\n\n"
                               f"  Project : {os.path.basename(path)}\n"
                               f"  Repo    : {url}\n"
                               f"  Branch  : {branch}\n"
                               f"  Files   : {len(selected)} selected\n"
                               f"  Commit  : \"{msg}\""
                               f"{gi}\n\nProceed?"):
            threading.Thread(target=self._deploy, daemon=True).start()

    # ══════════════════════════════════════════════════════════════
    #  CORE DEPLOY PIPELINE
    # ══════════════════════════════════════════════════════════════
    def _deploy(self):
        path   = self.project_path.get()
        repo   = self.repo_name.get().strip()
        user   = self.gh_username.get().strip()
        branch = self.branch.get().strip()
        msg    = self.commit_msg.get().strip()
        url    = f"https://github.com/{user}/{repo}.git"
        div    = "━" * 52

        self.terminal.log(f"\n{div}", ACCENT)
        self.terminal.log(f"🚀  DEPLOYING → {url}", ACCENT)
        self.terminal.log(f"{div}\n", ACCENT)

        # ── Step 1: .gitignore ──
        self.terminal.log("[ 1/8 ]  Writing .gitignore…", YELLOW)
        if self.create_gitignore.get():
            self._write_gitignore(path)
            self._refresh_files()
        else:
            self.terminal.log("  Skipped (disabled)", TEXT_DIM)

        # ── Step 2: Ensure git is installed ──
        self.terminal.log("\n[ 2/8 ]  Checking Git…", YELLOW)
        if not git_available():
            self.terminal.log("❌  Git not found. Open Git Wizard first.", RED)
            return

        # ── Step 3: git init ──
        self.terminal.log("\n[ 3/8 ]  Checking git init…", YELLOW)
        git_dir = os.path.join(path, ".git")
        if not os.path.isdir(git_dir):
            ok, _, err = self._run("git init", path)
            if not ok:
                self.terminal.log(f"❌  git init failed: {err}", RED); return
            self.terminal.log("  ✅  Repository initialised.", ACCENT)
        else:
            self.terminal.log("  ✅  Already a git repository.", TEXT_DIM)

        # ── Step 4: Ensure identity ──
        self.terminal.log("\n[ 4/8 ]  Verifying git identity…", YELLOW)
        name  = get_git_global("user.name")
        email = get_git_global("user.email")
        if not name or not email:
            self.terminal.log("⚠  No git identity. Setting from UI fields…", YELLOW)
            name  = self.git_username.get().strip()
            email = self.git_email.get().strip()
            if name and email:
                run_cmd(f'git config --global user.name "{name}"')
                run_cmd(f'git config --global user.email "{email}"')
                self.terminal.log(f"  ✅  Set: {name} <{email}>", ACCENT)
            else:
                self.terminal.log("❌  No identity configured. Fill Name and Email in UI.", RED)
                return
        else:
            self.terminal.log(f"  ✅  {name} <{email}>", TEXT_DIM)

        # ── Step 5: Set remote ──
        self.terminal.log("\n[ 5/8 ]  Setting remote origin…", YELLOW)
        self._run("git remote remove origin", path)   # silent fail if none
        ok, _, err = self._run(f'git remote add origin {url}', path)
        if not ok:
            self._run(f'git remote set-url origin {url}', path)
        self.terminal.log(f"  origin → {url}", TEXT_MID)

        # ── Step 6: Stage files ──
        self.terminal.log("\n[ 6/8 ]  Staging selected files…", YELLOW)
        selected = self.file_list.get_selected()
        fail_stage = []
        for f in selected:
            ok, _, err = self._run(f'git add "{f}"', path)
            if not ok: fail_stage.append(f)
        if fail_stage:
            self.terminal.log(f"  ⚠  {len(fail_stage)} file(s) failed to stage.", YELLOW)
        self.terminal.log(f"  ✅  {len(selected) - len(fail_stage)} files staged.", ACCENT)

        # ── Step 7: Commit ──
        self.terminal.log(f"\n[ 7/8 ]  Committing: \"{msg}\"", YELLOW)
        ok, out, err = self._run(f'git commit -m "{msg}"', path)
        if not ok:
            if "nothing to commit" in out.lower() or "nothing to commit" in err.lower():
                self.terminal.log("  ℹ  Nothing new to commit. Attempting push anyway…", TEXT_DIM)
            else:
                self.terminal.log(f"  ⚠  Commit issue: {err}", YELLOW)

        # ── Branch rename ──
        self._run(f"git branch -M {branch}", path)

        # ── Step 8: Push (with smart conflict handling) ──
        self.terminal.log(f"\n[ 8/8 ]  Pushing to GitHub…", YELLOW)
        self._smart_push(path, url, branch)

    # ─────────────────────────────────────────────────────────────
    def _smart_push(self, path, url, branch, attempt=1):
        """Push with automatic conflict detection and resolution."""
        ok, out, err = self._run(f"git push -u origin {branch}", path)
        combined = (out + err).lower()

        if ok:
            self._deploy_success(url)
            return

        # ── Conflict: remote has commits we don't ──
        if any(k in combined for k in ["rejected", "fetch first", "non-fast-forward"]):
            self.terminal.log("\n⚠  Push rejected — remote has newer commits.", YELLOW)
            if attempt > 2:
                self.terminal.log("❌  Too many retries. Please resolve manually.", RED)
                self._deploy_fail()
                return
            self.after(0, lambda: self._ask_conflict(path, url, branch, attempt))
            return

        # ── Auth failure ──
        if any(k in combined for k in ["authentication", "403", "401", "bad credentials",
                                        "could not read username", "permission denied"]):
            self.terminal.log("\n❌  Authentication failed.", RED)
            self.terminal.log("💡  Use a GitHub Personal Access Token as your password.", YELLOW)
            self.terminal.log("💡  Generate at: GitHub → Settings → Developer Settings → Tokens", YELLOW)
            self.terminal.log("💡  Make sure the PAT has 'repo' scope.", YELLOW)
            webbrowser.open("https://github.com/settings/tokens/new?scopes=repo")
            self._deploy_fail()
            return

        # ── Repo doesn't exist ──
        if any(k in combined for k in ["repository not found", "does not exist",
                                        "not found", "remote: repository"]):
            self.terminal.log("\n❌  Repository not found on GitHub.", RED)
            self.terminal.log("💡  Create the repo first at github.com/new", YELLOW)
            webbrowser.open(f"https://github.com/new")
            self._deploy_fail()
            return

        # ── No upstream ──
        if "no upstream branch" in combined or "set-upstream" in combined:
            self.terminal.log("  ↪  Setting upstream and retrying…", TEXT_DIM)
            ok2, _, _ = self._run(f"git push --set-upstream origin {branch}", path)
            if ok2: self._deploy_success(url); return
            self._deploy_fail(); return

        # ── SSL / network ──
        if any(k in combined for k in ["ssl", "tls", "network", "timeout",
                                        "could not resolve", "connection refused"]):
            self.terminal.log("\n❌  Network/SSL error.", RED)
            self.terminal.log("💡  Check your internet connection.", YELLOW)
            self.terminal.log("💡  If behind a proxy: git config --global http.proxy <proxy>", YELLOW)
            self._deploy_fail(); return

        # ── Large file ──
        if "large files" in combined or "file exceeds" in combined:
            self.terminal.log("\n❌  Push rejected due to large files.", RED)
            self.terminal.log("💡  Add large files to .gitignore and re-stage.", YELLOW)
            self._deploy_fail(); return

        # ── Unknown error ──
        self.terminal.log(f"\n❌  Unknown push error.", RED)
        self._deploy_fail()

    def _ask_conflict(self, path, url, branch, attempt):
        dlg = ConflictDialog(self, url, branch)
        self.wait_window(dlg)
        choice = dlg.choice
        if choice is None:
            self.terminal.log("🚫  Deploy cancelled by user.", YELLOW); return

        def resolve():
            if choice == "merge":
                self.terminal.log("\n🔄  Pulling remote changes (merge)…", YELLOW)
                ok, out, err = self._run(f"git pull origin {branch} --no-rebase", path)
                if not ok and "conflict" in (out + err).lower():
                    self.terminal.log("❌  Merge conflicts detected. Resolve manually in your editor.", RED)
                    return
            elif choice == "rebase":
                self.terminal.log("\n📥  Pulling with rebase…", YELLOW)
                ok, out, err = self._run(f"git pull --rebase origin {branch}", path)
                if not ok:
                    self.terminal.log("❌  Rebase failed. Check for conflicts.", RED)
                    return
            elif choice == "force":
                self.terminal.log("\n♻️  Force pushing…", YELLOW)
                ok, _, _ = self._run(f"git push --force origin {branch}", path)
                if ok: self._deploy_success(url)
                else:  self._deploy_fail()
                return

            self.terminal.log("  ↪  Retrying push…", TEXT_DIM)
            self._smart_push(path, url, branch, attempt + 1)

        threading.Thread(target=resolve, daemon=True).start()

    def _deploy_success(self, url):
        div = "━" * 52
        self.terminal.log(f"\n{div}", ACCENT)
        self.terminal.log("✅  DEPLOYED SUCCESSFULLY!", ACCENT)
        self.terminal.log(f"🌐  {url}", BLUE)
        self.terminal.log(div, ACCENT)

    def _deploy_fail(self):
        div = "━" * 52
        self.terminal.log(f"\n{div}", RED)
        self.terminal.log("❌  DEPLOY FAILED  —  See messages above for details.", RED)
        self.terminal.log(div, RED)


# ══════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = PyhubPro()
    app.mainloop()
    
    
    