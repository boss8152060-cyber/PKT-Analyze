"""PKT Analyze as a module of PK Transport (plugin API 1, see PK-Transport/pkt/plugin.py): its main window (Run1App of PKStudio.py) is
built into a frame of the PK Transport window.

PKStudio.py is imported in a background thread the first time the page is shown (it loads PyTorch / Ultralytics, which takes a few
seconds); Run1App then gets a frame that behaves like its root window. The program also runs on its own: python PKStudio.py.
Light at the top: PK Transport imports this file on its Home page."""
import importlib
import os
import queue
import sys
import threading
import tkinter as tk
import traceback
from tkinter import ttk

from pkt.ui.theme import COLORS

BOOTSTRAP_MARKER = "PK_STUDIO_CUDA_RELAUNCHED"      # PKStudio.py would restart itself with another Python at import time; this window already chose its Python


class EmbeddedRoot(tk.Frame):
    """A frame that can stand in for the Tk root of Run1App: the window-level calls do nothing here (the window belongs to PK Transport)."""

    def __init__(self, parent):
        super().__init__(parent, bg=COLORS["bg"])
        self.close_handler = None

    def title(self, *_a, **_k):
        return ""

    def geometry(self, *_a, **_k):
        return ""

    def minsize(self, *_a, **_k):
        return None

    def state(self, *_a, **_k):
        return ""

    def iconbitmap(self, *_a, **_k):
        return None

    def attributes(self, *_a, **_k):
        return None

    def protocol(self, name=None, func=None):
        if name == "WM_DELETE_WINDOW":
            self.close_handler = func

    def bind_all(self, sequence=None, func=None, add=None):
        """Run1App binds the mouse wheel for all windows; here it must add to what is bound and only act while this page is showing."""
        if func is None:
            return super().bind_all(sequence)

        def gated(event, _f=func):
            if self.winfo_ismapped():
                return _f(event)
            return None
        return super().bind_all(sequence, gated, add="+")


class AnalyzePage(ttk.Frame):
    def __init__(self, parent, app, folder):
        super().__init__(parent)
        self.app = app
        self.folder = folder                       # the installed PKT Analyze module
        self.b = app.b
        self.loaded = False
        self.loading = False
        self.error = None
        self.studio = None                  # the Run1App
        self.shell = None                   # the EmbeddedRoot
        self.applied_model = None
        self.q = queue.Queue()
        self.message = ttk.Label(self, text="", style="Muted.TLabel", justify="left", wraplength=800)
        self.message.pack(anchor="nw", padx=30, pady=30)
        app.b.on_change(self._on_language)

    def _on_language(self):
        if self.loading:
            self.message.configure(text=self.app.t("analyze_loading"))
        elif self.error:
            self.message.configure(text=self.app.t("analyze_load_failed", err=self.error))

    # ---------------------------------------------------------------- loading
    def on_show(self):
        if not self.loaded and not self.loading:
            self.load()
        elif self.studio is not None:
            self._apply_model()

    def load(self):
        script = os.path.join(self.folder, "PKStudio.py")
        if not os.path.isfile(script):
            self.loaded = True
            self.error = self.app.t("module_missing", name="PKT Analyze", path=self.folder)
            self.message.configure(text=self.error)
            return
        self.loading = True
        self.message.configure(text=self.app.t("analyze_loading"))
        folder = self.folder
        chosen_model = self.app.get_analyze_model()

        def work():
            had_marker = BOOTSTRAP_MARKER in os.environ
            old_model = os.environ.get("PKT_MODEL_PATH")
            try:
                if folder not in sys.path:
                    sys.path.insert(0, folder)
                os.environ[BOOTSTRAP_MARKER] = "1"
                if chosen_model:
                    os.environ["PKT_MODEL_PATH"] = chosen_model
                module = importlib.import_module(os.path.splitext(os.path.basename(script))[0])
                self.q.put(("ok", module))
            except BaseException:                           # SystemExit included: PKStudio.py must never end this program
                self.q.put(("error", traceback.format_exc(limit=3)))
            finally:
                if not had_marker:
                    os.environ.pop(BOOTSTRAP_MARKER, None)
                if old_model is None:
                    os.environ.pop("PKT_MODEL_PATH", None)
                else:
                    os.environ["PKT_MODEL_PATH"] = old_model

        threading.Thread(target=work, daemon=True).start()
        self.after(150, self._poll)

    def _poll(self):
        try:
            kind, payload = self.q.get_nowait()
        except queue.Empty:
            if self.winfo_exists():
                self.after(150, self._poll)
            return
        self.loading = False
        self.loaded = True
        if kind == "error":
            self.error = payload
            self.message.configure(text=self.app.t("analyze_load_failed", err=payload))
            return
        self.message.pack_forget()
        self.shell = EmbeddedRoot(self)
        self.shell.pack(fill="both", expand=True)
        try:
            self.studio = payload.Run1App(self.shell)
        except Exception:
            self.shell.destroy()
            self.shell = None
            self.error = traceback.format_exc(limit=3)
            self.message.pack(anchor="nw", padx=30, pady=30)
            self.message.configure(text=self.app.t("analyze_load_failed", err=self.error))
            return
        xl = getattr(self.app, "xl", None)
        if xl is not None and hasattr(xl, "tr"):
            self.studio.tr_text = xl.tr                       # the progress window of a batch writes its own texts in the chosen language
        self.applied_model = self.studio.model_var.get()
        self._apply_model()

    # ---------------------------------------------------------------- shared model / closing
    def _apply_model(self):
        """A model sent here from PKT Train (or set in the settings) is put into the Model field once."""
        chosen = self.app.get_analyze_model()
        if chosen and chosen != self.applied_model and os.path.isfile(chosen):
            self.studio.model_var.set(chosen)
            self.applied_model = chosen

    def is_running(self):
        return bool(self.studio is not None and getattr(self.studio, "running", False))

    def stop_for_exit(self):
        """The window is closing while an analysis runs: ask it to stop (it finishes the current frame)."""
        if self.studio is not None:
            self.studio.stop_event.set()
            self.studio.pause_event.set()


def find_analysis_outputs(root, limit=30):
    """The result folders PKT Analyze wrote under `root` (its Output folder): a folder with Run_Summary.json, newest first.
    Each: {'name', 'folder', 'mtime', 'clip', 'ttc', 'pet'} (ttc / pet = the number of events, None when unknown)."""
    import json
    out = []
    if not root or not os.path.isdir(root):
        return out
    root = os.path.normpath(root)
    for dirpath, dirnames, files in os.walk(root):
        depth = os.path.relpath(dirpath, root).count(os.sep) + (0 if dirpath == root else 1)
        if depth >= 4:
            dirnames[:] = []
        sdir = dirpath                                       # the summaries: in the clip folder, or in its 9_Summary (since 1.50.0)
        if "Run_Summary.json" not in files and os.path.isfile(os.path.join(dirpath, "9_Summary", "Run_Summary.json")):
            sdir = os.path.join(dirpath, "9_Summary")
        if os.path.basename(dirpath) == "9_Summary":
            continue
        if os.path.isfile(os.path.join(sdir, "Run_Summary.json")):
            info = {"name": os.path.basename(dirpath), "folder": dirpath, "clip": "", "ttc": None, "pet": None,
                    "mtime": os.path.getmtime(os.path.join(sdir, "Run_Summary.json"))}
            try:
                with open(os.path.join(sdir, "Run_Summary.json"), encoding="utf-8") as f:
                    run = json.load(f)
                info["clip"] = os.path.basename(str(run.get("video", "")).replace("\\", "/"))
            except (OSError, ValueError):
                pass
            if os.path.isfile(os.path.join(sdir, "Summary.json")):
                try:
                    with open(os.path.join(sdir, "Summary.json"), encoding="utf-8") as f:
                        ind = (json.load(f).get("indicators") or {})
                    info["ttc"] = (ind.get("TTC") or {}).get("N")
                    info["pet"] = (ind.get("PET") or {}).get("N")
                except (OSError, ValueError):
                    pass
            out.append(info)
            dirnames[:] = []
    out.sort(key=lambda r: r["mtime"], reverse=True)
    return out[:limit]


TEXTS = {'th': {'analyze_loading': 'กำลังโหลด PKT Analyze (PyTorch และ Ultralytics) ... ครั้งแรกใช้เวลาไม่กี่วินาที',
        'analyze_load_failed': 'โหลด PKT Analyze เข้าหน้าต่างนี้ไม่ได้:\n'
                               '\n'
                               '{err}\n'
                               'ติดตั้งไลบรารีที่ต้องใช้ (install.bat) หรือตรวจโฟลเดอร์ PKT Analyze ในหน้าตั้งค่า',
        'analyze_busy_close': 'PKT Analyze กำลังประมวลผลอยู่ หยุดแล้วปิดโปรแกรมไหม',
        'home_model': 'โมเดล: {name}',
        'home_model_default': 'ค่าตั้งต้นของมันเอง',
        'home_results': 'ผลลัพธ์ {n} โฟลเดอร์',
        'home_recent_analysis': 'วิเคราะห์ {name}'},
 'en': {'analyze_loading': 'Loading PKT Analyze (PyTorch and Ultralytics) ... this takes a few seconds the first time.',
        'analyze_load_failed': 'PKT Analyze could not be loaded into this window:\n'
                               '\n'
                               '{err}\n'
                               'Install its requirements (install.bat) or check the PKT Analyze folder in Settings.',
        'analyze_busy_close': 'PKT Analyze is processing. Stop it and close the program?',
        'home_model': 'Model: {name}',
        'home_model_default': 'its own default',
        'home_results': '{n} result folder(s)',
        'home_recent_analysis': 'Analysis of {name}'}}


API = 1


def texts():
    return TEXTS


def catalogs():
    """Translations of the PKT Analyze windows (it is written in Thai): English when the window language is English."""
    from pkt_analyze_lang import EXACT, TEMPLATES
    return [{"lang": "en", "exact": EXACT, "templates": TEMPLATES, "fragments": True}]


def _outputs(app):
    return find_analysis_outputs(os.path.join(app.user_data_dir("PKT-Analyze"), "Output"))


def summary(app, folder):
    model = app.get_analyze_model()
    text = app.t("home_model", name=os.path.basename(model) if model else app.t("home_model_default"))
    outs = _outputs(app)
    if outs:
        text += " \u00b7 " + app.t("home_results", n=len(outs))
    return text


def recent(app, folder):
    items = []
    for o in _outputs(app)[:5]:
        meta = []
        if o["ttc"] is not None:
            meta.append(f"TTC {o['ttc']}")
        if o["pet"] is not None:
            meta.append(f"PET {o['pet']}")
        items.append({"mtime": o["mtime"], "glyph": "\u25eb", "title": app.t("home_recent_analysis", name=o["clip"] or o["name"]), "meta": " \u00b7 ".join(meta)})
    return items


def create(parent, app, folder):
    return AnalyzePage(parent, app, folder)
