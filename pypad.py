#!/usr/bin/env python3
"""
PyPad — A lightweight text editor built with Python and Tkinter.

Single file  •  No external dependencies  •  Cross-platform
Runs on Windows, macOS, and Linux without installation.
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import os

# ── Platform font detection ───────────────────────────────────────────────────
if os.path.exists("/System/Library/Fonts"):   # macOS
    _FONT = ("Menlo", 11)
elif os.name == "nt":                          # Windows
    _FONT = ("Consolas", 11)
else:                                          # Linux / other
    _FONT = ("DejaVu Sans Mono", 11)

# ── File dialog filters ───────────────────────────────────────────────────────
_FILETYPES = [
    ("Text files",     "*.txt"),
    ("Python files",   "*.py"),
    ("Markdown files", "*.md"),
    ("All files",      "*.*"),
]

# ── Color themes ──────────────────────────────────────────────────────────────
_THEMES = {
    "light": {
        "bg":        "#ffffff",
        "fg":        "#1a1a1a",
        "cursor":    "#1a1a1a",
        "sel_bg":    "#4a90d9",
        "sel_fg":    "#ffffff",
        "gutter_bg": "#f5f5f5",
        "gutter_fg": "#a0a0a0",
        "status_bg": "#e8e8e8",
        "status_fg": "#555555",
    },
    "dark": {
        "bg":        "#1e1e2e",
        "fg":        "#cdd6f4",
        "cursor":    "#f5e0dc",
        "sel_bg":    "#45475a",
        "sel_fg":    "#cdd6f4",
        "gutter_bg": "#181825",
        "gutter_fg": "#585b70",
        "status_bg": "#11111b",
        "status_fg": "#a6adc8",
    },
}


# ── Find & Replace dialog ─────────────────────────────────────────────────────

class FindReplaceDialog(tk.Toplevel):
    """Non-blocking Find & Replace dialog window."""

    def __init__(self, parent, editor):
        super().__init__(parent)
        self.editor = editor
        self.title("Find & Replace")
        self.resizable(False, False)
        self.transient(parent)
        self.protocol("WM_DELETE_WINDOW", self._close)

        self.editor.tag_configure(
            "found", background="#ffff55", foreground="#000000"
        )

        p = {"padx": 8, "pady": 4}

        tk.Label(self, text="Find:").grid(row=0, column=0, sticky="w", **p)
        self.find_var = tk.StringVar()
        self.find_entry = tk.Entry(self, textvariable=self.find_var, width=28)
        self.find_entry.grid(row=0, column=1, columnspan=2, sticky="ew", **p)

        tk.Label(self, text="Replace:").grid(row=1, column=0, sticky="w", **p)
        self.replace_var = tk.StringVar()
        tk.Entry(self, textvariable=self.replace_var, width=28).grid(
            row=1, column=1, columnspan=2, sticky="ew", **p)

        self.case_var = tk.BooleanVar()
        tk.Checkbutton(
            self, text="Case sensitive", variable=self.case_var
        ).grid(row=2, column=0, columnspan=3, sticky="w", padx=8)

        bf = tk.Frame(self)
        bf.grid(row=3, column=0, columnspan=3, pady=8)
        for label, cmd in [
            ("Find Next",   self.find_next),
            ("Replace",     self.replace_one),
            ("Replace All", self.replace_all),
        ]:
            tk.Button(bf, text=label, width=11, command=cmd).pack(
                side="left", padx=4)

        self.columnconfigure(1, weight=1)
        self.bind("<Return>", lambda _: self.find_next())
        self.bind("<Escape>", lambda _: self._close())
        self.find_entry.focus_set()

    def _close(self):
        self.editor.tag_remove("found", "1.0", tk.END)
        self.destroy()

    def find_next(self, pos=None):
        """Find next occurrence; wraps around end of document."""
        self.editor.tag_remove("found", "1.0", tk.END)
        term = self.find_var.get()
        if not term:
            return None
        pos = pos or self.editor.index(tk.INSERT)
        nocase = not self.case_var.get()
        idx = (
            self.editor.search(term, pos,   stopindex=tk.END, nocase=nocase) or
            self.editor.search(term, "1.0", stopindex=tk.END, nocase=nocase)
        )
        if idx:
            end = f"{idx}+{len(term)}c"
            self.editor.tag_add("found", idx, end)
            self.editor.mark_set(tk.INSERT, end)
            self.editor.see(idx)
            return idx
        messagebox.showinfo("Not Found", f'"{term}" not found.', parent=self)
        return None

    def replace_one(self):
        term = self.find_var.get()
        if not term:
            return
        idx = self.find_next()
        if idx:
            self.editor.delete(idx, f"{idx}+{len(term)}c")
            self.editor.insert(idx, self.replace_var.get())
            self.editor.tag_remove("found", "1.0", tk.END)

    def replace_all(self):
        term = self.find_var.get()
        repl = self.replace_var.get()
        if not term:
            return
        nocase, count, pos = not self.case_var.get(), 0, "1.0"
        while True:
            idx = self.editor.search(term, pos, stopindex=tk.END, nocase=nocase)
            if not idx:
                break
            self.editor.delete(idx, f"{idx}+{len(term)}c")
            self.editor.insert(idx, repl)
            pos, count = f"{idx}+{len(repl)}c", count + 1
        messagebox.showinfo(
            "Replace All",
            f"Replaced {count} occurrence(s)." if count else f'"{term}" not found.',
            parent=self,
        )


# ── Main application ──────────────────────────────────────────────────────────

class PyPad:
    """Lightweight single-file text editor."""

    APP = "PyPad"

    def __init__(self, root):
        self.root    = root
        self.root.title(self.APP)
        self.root.geometry("920x640")
        self.root.minsize(480, 320)

        self.filepath  = None   # current open file path (str or None)
        self.modified  = False  # unsaved-changes flag
        self._theme    = "light"
        self._find_dlg = None   # FindReplaceDialog instance

        self._build_menu()
        self._build_editor()
        self._build_status()
        self._apply_theme()
        self._bind_keys()
        self.root.protocol("WM_DELETE_WINDOW", self.cmd_exit)
        self._refresh()

    # ── Layout builders ───────────────────────────────────────────────────────

    def _build_menu(self):
        bar = tk.Menu(self.root)
        self.root.config(menu=bar)

        # File menu
        fm = tk.Menu(bar, tearoff=0)
        bar.add_cascade(label="File", menu=fm)
        fm.add_command(label="New",       accelerator="Ctrl+N",       command=self.cmd_new)
        fm.add_command(label="Open…",     accelerator="Ctrl+O",       command=self.cmd_open)
        fm.add_separator()
        fm.add_command(label="Save",      accelerator="Ctrl+S",       command=self.cmd_save)
        fm.add_command(label="Save As…",  accelerator="Ctrl+Shift+S", command=self.cmd_save_as)
        fm.add_separator()
        fm.add_command(label="Exit",                                   command=self.cmd_exit)

        # Edit menu
        em = tk.Menu(bar, tearoff=0)
        bar.add_cascade(label="Edit", menu=em)
        em.add_command(label="Undo",       accelerator="Ctrl+Z",
                       command=lambda: self.editor.event_generate("<<Undo>>"))
        em.add_command(label="Redo",       accelerator="Ctrl+Y",
                       command=lambda: self.editor.event_generate("<<Redo>>"))
        em.add_separator()
        em.add_command(label="Cut",        accelerator="Ctrl+X",
                       command=lambda: self.editor.event_generate("<<Cut>>"))
        em.add_command(label="Copy",       accelerator="Ctrl+C",
                       command=lambda: self.editor.event_generate("<<Copy>>"))
        em.add_command(label="Paste",      accelerator="Ctrl+V",
                       command=lambda: self.editor.event_generate("<<Paste>>"))
        em.add_separator()
        em.add_command(label="Select All",         accelerator="Ctrl+A", command=self.cmd_select_all)
        em.add_separator()
        em.add_command(label="Find & Replace…",    accelerator="Ctrl+H", command=self.cmd_find_replace)

        # View menu
        vm = tk.Menu(bar, tearoff=0)
        bar.add_cascade(label="View", menu=vm)
        self.wrap_var   = tk.BooleanVar(value=True)
        self.lineno_var = tk.BooleanVar(value=True)
        self.dark_var   = tk.BooleanVar(value=False)
        vm.add_checkbutton(label="Word Wrap",    variable=self.wrap_var,   command=self._toggle_wrap)
        vm.add_checkbutton(label="Line Numbers", variable=self.lineno_var, command=self._toggle_linenos)
        vm.add_separator()
        vm.add_checkbutton(label="Dark Mode",    variable=self.dark_var,   command=self._toggle_theme)

    def _build_editor(self):
        self.body = tk.Frame(self.root)
        self.body.pack(fill="both", expand=True)

        # Line-number gutter
        self.gutter = tk.Frame(self.body, width=52)
        self.gutter.pack(side="left", fill="y")
        self.gutter.pack_propagate(False)

        self.lineno_text = tk.Text(
            self.gutter, width=4, padx=6, pady=4,
            state="disabled", cursor="arrow", takefocus=0,
            wrap="none", relief="flat", borderwidth=0, font=_FONT,
        )
        self.lineno_text.pack(fill="both", expand=True)

        # Editor pane — grid layout keeps scrollbars flush
        self._pane = tk.Frame(self.body)
        self._pane.pack(side="left", fill="both", expand=True)
        self._pane.rowconfigure(0, weight=1)
        self._pane.columnconfigure(0, weight=1)

        self.editor = tk.Text(
            self._pane, wrap="word", undo=True, maxundo=-1,
            padx=10, pady=4, relief="flat", borderwidth=0,
            font=_FONT, insertwidth=2,
        )
        self.editor.grid(row=0, column=0, sticky="nsew")

        self.vbar = tk.Scrollbar(self._pane, orient="vertical")
        self.vbar.grid(row=0, column=1, sticky="ns")

        self.hbar = tk.Scrollbar(self._pane, orient="horizontal")
        # hbar is only shown when word-wrap is off

        self.editor.config(yscrollcommand=self._yscroll)
        self.vbar.config(command=self._vbar_cmd)

    def _build_status(self):
        sb = tk.Frame(self.root, height=26)
        sb.pack(fill="x", side="bottom")
        sb.pack_propagate(False)
        self._statusbar = sb

        self.lbl_file = tk.Label(sb, text="Untitled", anchor="w", padx=10)
        self.lbl_file.pack(side="left")

        self.lbl_enc = tk.Label(sb, text="UTF-8", anchor="e", padx=10)
        self.lbl_enc.pack(side="right")

        self.lbl_pos = tk.Label(sb, text="Ln 1, Col 1", anchor="e", padx=10)
        self.lbl_pos.pack(side="right")

    # ── Scrolling ─────────────────────────────────────────────────────────────

    def _yscroll(self, *args):
        """Sync vertical scrollbar and line-number gutter together."""
        self.vbar.set(*args)
        if self.lineno_var.get():
            self.lineno_text.yview_moveto(self.editor.yview()[0])

    def _vbar_cmd(self, *args):
        """Scrollbar dragged — move editor and gutter together."""
        self.editor.yview(*args)
        if self.lineno_var.get():
            self.lineno_text.yview_moveto(self.editor.yview()[0])

    # ── Theme ─────────────────────────────────────────────────────────────────

    def _apply_theme(self):
        t = _THEMES[self._theme]
        self.editor.config(
            bg=t["bg"], fg=t["fg"],
            insertbackground=t["cursor"],
            selectbackground=t["sel_bg"], selectforeground=t["sel_fg"],
        )
        self.lineno_text.config(bg=t["gutter_bg"], fg=t["gutter_fg"])
        self.gutter.config(bg=t["gutter_bg"])
        self.body.config(bg=t["bg"])
        self._pane.config(bg=t["bg"])
        self._statusbar.config(bg=t["status_bg"])
        for w in (self.lbl_file, self.lbl_pos, self.lbl_enc):
            w.config(bg=t["status_bg"], fg=t["status_fg"])

    def _toggle_theme(self):
        self._theme = "dark" if self.dark_var.get() else "light"
        self._apply_theme()

    # ── Line numbers ──────────────────────────────────────────────────────────

    def _refresh_linenos(self):
        if not self.lineno_var.get():
            return
        total = int(self.editor.index("end-1c").split(".")[0])
        self.lineno_text.config(state="normal")
        self.lineno_text.delete("1.0", "end")
        self.lineno_text.insert("1.0", "\n".join(str(i) for i in range(1, total + 1)))
        self.lineno_text.config(state="disabled")
        self.lineno_text.yview_moveto(self.editor.yview()[0])

    def _toggle_linenos(self):
        if self.lineno_var.get():
            self.gutter.pack(side="left", fill="y", before=self._pane)
            self._refresh_linenos()
        else:
            self.gutter.pack_forget()

    # ── Word wrap ─────────────────────────────────────────────────────────────

    def _toggle_wrap(self):
        if self.wrap_var.get():
            self.editor.config(wrap="word", xscrollcommand="")
            self.hbar.grid_remove()
        else:
            self.editor.config(wrap="none")
            self.hbar.grid(row=1, column=0, sticky="ew")
            self.editor.config(xscrollcommand=self.hbar.set)
            self.hbar.config(command=self.editor.xview)

    # ── Key bindings ──────────────────────────────────────────────────────────

    def _bind_keys(self):
        for key, cmd in [
            ("<Control-n>", self.cmd_new),
            ("<Control-o>", self.cmd_open),
            ("<Control-s>", self.cmd_save),
            ("<Control-S>", self.cmd_save_as),
            ("<Control-h>", self.cmd_find_replace),
        ]:
            self.root.bind(key, lambda e, c=cmd: c())

        # Override default Ctrl+A (go-to-line-start) with select-all
        self.editor.bind("<Control-a>", lambda e: (self.cmd_select_all(), "break")[1])

        self.editor.bind("<<Modified>>",     self._on_modified)
        self.editor.bind("<KeyRelease>",     lambda e: self._refresh())
        self.editor.bind("<ButtonRelease-1>",lambda e: self._refresh())

    def _on_modified(self, _=None):
        """Fire when Tkinter's internal modified flag flips."""
        if self.editor.edit_modified():
            self.modified = True
            self.editor.edit_modified(False)
            self._update_title()

    def _refresh(self):
        self._update_status()
        self._refresh_linenos()

    def _update_title(self):
        name = os.path.basename(self.filepath) if self.filepath else "Untitled"
        dot  = " \u2022" if self.modified else ""
        self.root.title(f"{self.APP} \u2014 {name}{dot}")

    def _update_status(self):
        ln, col = self.editor.index(tk.INSERT).split(".")
        self.lbl_pos.config(text=f"Ln {ln}, Col {int(col) + 1}")
        self.lbl_file.config(
            text=os.path.basename(self.filepath) if self.filepath else "Untitled")

    # ── Unsaved-changes guard ─────────────────────────────────────────────────

    def _save_prompt(self):
        """Ask user to save if dirty.  Returns False if user cancelled."""
        if not self.modified:
            return True
        ans = messagebox.askyesnocancel(
            "Unsaved Changes", "Save changes before continuing?", parent=self.root)
        if ans is True:
            return self.cmd_save()
        return ans is False   # False ⇒ discard, None ⇒ cancel

    # ── File commands ─────────────────────────────────────────────────────────

    def cmd_new(self):
        if not self._save_prompt():
            return
        self.editor.delete("1.0", "end")
        self.filepath, self.modified = None, False
        self._update_title()
        self._refresh()

    def cmd_open(self):
        if not self._save_prompt():
            return
        path = filedialog.askopenfilename(title="Open File", filetypes=_FILETYPES)
        if not path:
            return
        try:
            try:
                with open(path, encoding="utf-8") as fh:
                    data = fh.read()
            except UnicodeDecodeError:
                with open(path, encoding="latin-1") as fh:
                    data = fh.read()
        except OSError as exc:
            messagebox.showerror("Open Error", str(exc), parent=self.root)
            return
        self.editor.delete("1.0", "end")
        self.editor.insert("1.0", data)
        self.editor.edit_reset()          # clear undo stack for new file
        self.editor.edit_modified(False)
        self.filepath, self.modified = path, False
        self._update_title()
        self._refresh()

    def cmd_save(self):
        if not self.filepath:
            return self.cmd_save_as()
        return self._write(self.filepath)

    def cmd_save_as(self):
        path = filedialog.asksaveasfilename(
            title="Save As", defaultextension=".txt", filetypes=_FILETYPES)
        if not path:
            return False
        self.filepath = path
        return self._write(path)

    def _write(self, path):
        try:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(self.editor.get("1.0", "end-1c"))
            self.modified = False
            self._update_title()
            return True
        except OSError as exc:
            messagebox.showerror("Save Error", str(exc), parent=self.root)
            return False

    def cmd_exit(self):
        if self._save_prompt():
            self.root.destroy()

    # ── Edit commands ─────────────────────────────────────────────────────────

    def cmd_select_all(self):
        self.editor.tag_add("sel", "1.0", "end")

    def cmd_find_replace(self):
        if self._find_dlg and self._find_dlg.winfo_exists():
            self._find_dlg.lift()
            self._find_dlg.find_entry.focus_set()
        else:
            self._find_dlg = FindReplaceDialog(self.root, self.editor)


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    root = tk.Tk()
    PyPad(root)
    root.mainloop()


if __name__ == "__main__":
    main()
