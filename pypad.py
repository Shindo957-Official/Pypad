import tkinter as tk
from tkinter import filedialog, messagebox
import os

THEMES = {
    "light": {
        "bg":         "#ffffff",
        "fg":         "#1a1a1a",
        "menu_bg":    "#f0f0f0",
        "menu_fg":    "#1a1a1a",
        "status_bg":  "#e8e8e8",
        "status_fg":  "#555555",
        "select_bg":  "#c8d8f0",
        "ln_bg":      "#f5f5f5",
        "ln_fg":      "#aaaaaa",
        "cursor":     "#1a1a1a",
        "border":     "#cccccc",
        "find_bg":    "#f9f9f9",
    },
    "dark": {
        "bg":         "#1e1e1e",
        "fg":         "#d4d4d4",
        "menu_bg":    "#2d2d2d",
        "menu_fg":    "#d4d4d4",
        "status_bg":  "#252526",
        "status_fg":  "#858585",
        "select_bg":  "#264f78",
        "ln_bg":      "#252526",
        "ln_fg":      "#555555",
        "cursor":     "#aeafad",
        "border":     "#3c3c3c",
        "find_bg":    "#2d2d2d",
    },
}


class PyPad:
    APP_NAME = "PyPad"

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(self.APP_NAME)
        self.root.geometry("900x620")
        self.root.minsize(480, 320)

        self.current_file: str | None = None
        self.modified = False
        self.theme_name = "light"
        self.word_wrap = tk.BooleanVar(value=True)
        self.show_line_numbers = tk.BooleanVar(value=True)
        self.find_bar_visible = False

        self._build_menu()
        self._build_editor()
        self._build_find_bar()
        self._build_status_bar()

        self._apply_theme()
        self._update_status()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.bind("<Control-n>", lambda e: self._new_file())
        self.root.bind("<Control-o>", lambda e: self._open_file())
        self.root.bind("<Control-s>", lambda e: self._save_file())
        self.root.bind("<Control-S>", lambda e: self._save_as())
        self.root.bind("<Control-f>", lambda e: self._toggle_find_bar())
        self.root.bind("<Escape>",    lambda e: self._hide_find_bar())

    def _build_menu(self):
        self.menubar = tk.Menu(self.root, tearoff=False)

        file_menu = tk.Menu(self.menubar, tearoff=False)
        file_menu.add_command(label="New",          accelerator="Ctrl+N",       command=self._new_file)
        file_menu.add_command(label="Open…",        accelerator="Ctrl+O",       command=self._open_file)
        file_menu.add_separator()
        file_menu.add_command(label="Save",         accelerator="Ctrl+S",       command=self._save_file)
        file_menu.add_command(label="Save As…",     accelerator="Ctrl+Shift+S", command=self._save_as)
        file_menu.add_separator()
        file_menu.add_command(label="Exit",         command=self._on_close)
        self.menubar.add_cascade(label="File", menu=file_menu)

        edit_menu = tk.Menu(self.menubar, tearoff=False)
        edit_menu.add_command(label="Undo",         accelerator="Ctrl+Z", command=lambda: self.text.edit_undo())
        edit_menu.add_command(label="Redo",         accelerator="Ctrl+Y", command=lambda: self.text.edit_redo())
        edit_menu.add_separator()
        edit_menu.add_command(label="Cut",          accelerator="Ctrl+X", command=lambda: self.text.event_generate("<<Cut>>"))
        edit_menu.add_command(label="Copy",         accelerator="Ctrl+C", command=lambda: self.text.event_generate("<<Copy>>"))
        edit_menu.add_command(label="Paste",        accelerator="Ctrl+V", command=lambda: self.text.event_generate("<<Paste>>"))
        edit_menu.add_separator()
        edit_menu.add_command(label="Select All",   accelerator="Ctrl+A", command=self._select_all)
        edit_menu.add_separator()
        edit_menu.add_command(label="Find & Replace…", accelerator="Ctrl+F", command=self._toggle_find_bar)
        self.menubar.add_cascade(label="Edit", menu=edit_menu)

        view_menu = tk.Menu(self.menubar, tearoff=False)
        view_menu.add_checkbutton(label="Word Wrap",    variable=self.word_wrap,        command=self._toggle_wrap)
        view_menu.add_checkbutton(label="Line Numbers", variable=self.show_line_numbers, command=self._toggle_line_numbers)
        view_menu.add_separator()
        view_menu.add_command(label="Toggle Theme", command=self._toggle_theme)
        self.menubar.add_cascade(label="View", menu=view_menu)

        self.root.config(menu=self.menubar)

    def _build_editor(self):
        self.editor_frame = tk.Frame(self.root)
        self.editor_frame.pack(fill=tk.BOTH, expand=True)

        self.ln_canvas = tk.Canvas(self.editor_frame, width=48, bd=0, highlightthickness=0)
        self.ln_canvas.pack(side=tk.LEFT, fill=tk.Y)

        self.v_scroll = tk.Scrollbar(self.editor_frame, orient=tk.VERTICAL)
        self.v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.h_scroll = tk.Scrollbar(self.editor_frame, orient=tk.HORIZONTAL)
        self.h_scroll.pack(side=tk.BOTTOM, fill=tk.X)

        self.text = tk.Text(
            self.editor_frame,
            wrap=tk.WORD,
            undo=True,
            autoseparators=True,
            maxundo=-1,
            font=("Consolas", 12),
            relief=tk.FLAT,
            bd=0,
            padx=6,
            pady=4,
            insertwidth=2,
            yscrollcommand=self._on_vscroll,
            xscrollcommand=self.h_scroll.set,
        )
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.v_scroll.config(command=self._sync_scroll)
        self.h_scroll.config(command=self.text.xview)

        self.text.bind("<<Modified>>",    self._on_text_modified)
        self.text.bind("<KeyRelease>",    self._on_key_release)
        self.text.bind("<ButtonRelease>", lambda e: self._update_status())
        self.ln_canvas.bind("<MouseWheel>", lambda e: self.text.yview_scroll(int(-1 * (e.delta / 120)), "units"))
        self.ln_canvas.bind("<Button-4>",   lambda e: self.text.yview_scroll(-1, "units"))
        self.ln_canvas.bind("<Button-5>",   lambda e: self.text.yview_scroll(1, "units"))

    def _on_vscroll(self, *args):
        self.v_scroll.set(*args)
        self._redraw_line_numbers()

    def _sync_scroll(self, *args):
        self.text.yview(*args)
        self._redraw_line_numbers()

    def _redraw_line_numbers(self):
        if not self.show_line_numbers.get():
            return
        t = self.theme()
        self.ln_canvas.delete("all")
        self.ln_canvas.config(bg=t["ln_bg"])
        i = self.text.index("@0,0")
        while True:
            dline = self.text.dlineinfo(i)
            if dline is None:
                break
            y = dline[1]
            linenum = int(str(i).split(".")[0])
            self.ln_canvas.create_text(
                42, y + 2,
                anchor="ne",
                text=str(linenum),
                fill=t["ln_fg"],
                font=("Consolas", 10),
            )
            i = self.text.index(f"{i}+1line")
            if self.text.compare(i, ">=", "end"):
                break

    def _toggle_line_numbers(self):
        if self.show_line_numbers.get():
            self.ln_canvas.pack(side=tk.LEFT, fill=tk.Y, before=self.text)
            self.ln_canvas.config(width=48)
            self._redraw_line_numbers()
        else:
            self.ln_canvas.pack_forget()

    def _build_find_bar(self):
        self.find_frame = tk.Frame(self.root, bd=1, relief=tk.FLAT)
        pad = {"padx": 4, "pady": 4}

        tk.Label(self.find_frame, text="Find:").pack(side=tk.LEFT, **pad)
        self.find_entry = tk.Entry(self.find_frame, width=20)
        self.find_entry.pack(side=tk.LEFT, **pad)

        tk.Label(self.find_frame, text="Replace:").pack(side=tk.LEFT, **pad)
        self.replace_entry = tk.Entry(self.find_frame, width=20)
        self.replace_entry.pack(side=tk.LEFT, **pad)

        btn_cfg = {"relief": tk.FLAT, "padx": 6, "pady": 2, "cursor": "hand2"}
        tk.Button(self.find_frame, text="Find Next",   command=self._find_next,     **btn_cfg).pack(side=tk.LEFT, padx=2)
        tk.Button(self.find_frame, text="Replace",     command=self._replace_one,   **btn_cfg).pack(side=tk.LEFT, padx=2)
        tk.Button(self.find_frame, text="Replace All", command=self._replace_all,   **btn_cfg).pack(side=tk.LEFT, padx=2)
        tk.Button(self.find_frame, text="✕",           command=self._hide_find_bar, relief=tk.FLAT, padx=4, cursor="hand2").pack(side=tk.RIGHT, padx=4)

        self.find_entry.bind("<Return>",    lambda e: self._find_next())
        self.find_entry.bind("<Escape>",    lambda e: self._hide_find_bar())
        self.replace_entry.bind("<Escape>", lambda e: self._hide_find_bar())

        self.text.tag_config("highlight", background="#ffd700", foreground="#000000")

    def _toggle_find_bar(self):
        if self.find_bar_visible:
            self._hide_find_bar()
        else:
            self._show_find_bar()

    def _show_find_bar(self):
        self.find_bar_visible = True
        self.find_frame.pack(fill=tk.X, before=self.editor_frame)
        self._theme_find_bar()
        self.find_entry.focus_set()

    def _hide_find_bar(self):
        self.find_bar_visible = False
        self.find_frame.pack_forget()
        self.text.tag_remove("highlight", "1.0", tk.END)
        self.text.focus_set()

    def _find_next(self, start=None):
        query = self.find_entry.get()
        if not query:
            return
        self.text.tag_remove("highlight", "1.0", tk.END)
        start = start or self.text.index(tk.INSERT)
        idx = self.text.search(query, start, stopindex=tk.END)
        if not idx:
            idx = self.text.search(query, "1.0", stopindex=tk.END)
        if idx:
            end = f"{idx}+{len(query)}c"
            self.text.tag_add("highlight", idx, end)
            self.text.mark_set(tk.INSERT, end)
            self.text.see(idx)
        else:
            messagebox.showinfo("Find", f'"{query}" not found.', parent=self.root)

    def _replace_one(self):
        query   = self.find_entry.get()
        replace = self.replace_entry.get()
        if not query:
            return
        idx = self.text.search(query, tk.INSERT, stopindex=tk.END) or \
              self.text.search(query, "1.0",     stopindex=tk.END)
        if idx:
            end = f"{idx}+{len(query)}c"
            self.text.delete(idx, end)
            self.text.insert(idx, replace)
            self._find_next(start=f"{idx}+{len(replace)}c")

    def _replace_all(self):
        query   = self.find_entry.get()
        replace = self.replace_entry.get()
        if not query:
            return
        count = 0
        start = "1.0"
        while True:
            idx = self.text.search(query, start, stopindex=tk.END)
            if not idx:
                break
            end = f"{idx}+{len(query)}c"
            self.text.delete(idx, end)
            self.text.insert(idx, replace)
            start = f"{idx}+{len(replace)}c"
            count += 1
        messagebox.showinfo("Replace All", f"Replaced {count} occurrence(s).", parent=self.root)

    def _build_status_bar(self):
        self.status_bar = tk.Frame(self.root, height=24)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.status_pos = tk.Label(self.status_bar, text="Ln 1, Col 1", anchor=tk.W, padx=8)
        self.status_pos.pack(side=tk.LEFT)

        self.status_file = tk.Label(self.status_bar, text="Untitled", anchor=tk.E, padx=8)
        self.status_file.pack(side=tk.RIGHT)

        self.status_enc = tk.Label(self.status_bar, text="UTF-8", anchor=tk.E, padx=8)
        self.status_enc.pack(side=tk.RIGHT)

    def _update_status(self):
        try:
            row, col = self.text.index(tk.INSERT).split(".")
            self.status_pos.config(text=f"Ln {row}, Col {int(col)+1}")
        except Exception:
            pass
        fname = os.path.basename(self.current_file) if self.current_file else "Untitled"
        self.status_file.config(text=("● " if self.modified else "") + fname)

    def _new_file(self):
        if not self._confirm_discard():
            return
        self.text.delete("1.0", tk.END)
        self.current_file = None
        self.modified = False
        self.root.title(self.APP_NAME)
        self._update_status()

    def _open_file(self):
        if not self._confirm_discard():
            return
        path = filedialog.askopenfilename(
            title="Open File",
            filetypes=[("Text Files", "*.txt"), ("Python Files", "*.py"),
                       ("Markdown", "*.md"), ("All Files", "*.*")],
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            self.text.delete("1.0", tk.END)
            self.text.insert("1.0", content)
            self.text.edit_reset()
            self.current_file = path
            self.modified = False
            self.root.title(f"{os.path.basename(path)} — {self.APP_NAME}")
            self._update_status()
            self._redraw_line_numbers()
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file:\n{e}", parent=self.root)

    def _save_file(self):
        if self.current_file:
            self._write_file(self.current_file)
        else:
            self._save_as()

    def _save_as(self):
        path = filedialog.asksaveasfilename(
            title="Save As",
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("Python Files", "*.py"),
                       ("Markdown", "*.md"), ("All Files", "*.*")],
        )
        if path:
            self.current_file = path
            self._write_file(path)

    def _write_file(self, path: str):
        try:
            content = self.text.get("1.0", tk.END)
            if content.endswith("\n"):
                content = content[:-1]
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            self.modified = False
            self.root.title(f"{os.path.basename(path)} — {self.APP_NAME}")
            self._update_status()
        except Exception as e:
            messagebox.showerror("Error", f"Could not save file:\n{e}", parent=self.root)

    def _confirm_discard(self) -> bool:
        if not self.modified:
            return True
        answer = messagebox.askyesnocancel(
            "Unsaved Changes",
            "You have unsaved changes. Save before continuing?",
            parent=self.root,
        )
        if answer is None:
            return False
        if answer:
            self._save_file()
        return True

    def _on_close(self):
        if self._confirm_discard():
            self.root.destroy()

    def _select_all(self):
        self.text.tag_add(tk.SEL, "1.0", tk.END)
        self.text.mark_set(tk.INSERT, "1.0")
        self.text.see(tk.INSERT)

    def _toggle_wrap(self):
        self.text.config(wrap=tk.WORD if self.word_wrap.get() else tk.NONE)

    def theme(self) -> dict:
        return THEMES[self.theme_name]

    def _toggle_theme(self):
        self.theme_name = "dark" if self.theme_name == "light" else "light"
        self._apply_theme()

    def _apply_theme(self):
        t = self.theme()
        self.root.config(bg=t["bg"])
        self.text.config(
            bg=t["bg"], fg=t["fg"],
            insertbackground=t["cursor"],
            selectbackground=t["select_bg"],
            selectforeground=t["fg"],
        )
        self.ln_canvas.config(bg=t["ln_bg"])
        self._redraw_line_numbers()
        self.status_bar.config(bg=t["status_bg"])
        for w in (self.status_pos, self.status_file, self.status_enc):
            w.config(bg=t["status_bg"], fg=t["status_fg"])
        self.editor_frame.config(bg=t["border"])
        self._theme_find_bar()
        self._theme_menu()

    def _theme_menu(self):
        t = self.theme()
        try:
            self.menubar.config(
                bg=t["menu_bg"], fg=t["menu_fg"],
                activebackground=t["select_bg"],
                activeforeground=t["fg"],
            )
        except Exception:
            pass

    def _theme_find_bar(self):
        t = self.theme()
        self.find_frame.config(bg=t["find_bg"])
        for child in self.find_frame.winfo_children():
            try:
                if isinstance(child, tk.Label):
                    child.config(bg=t["find_bg"], fg=t["fg"])
                elif isinstance(child, tk.Entry):
                    child.config(bg=t["bg"], fg=t["fg"],
                                 insertbackground=t["cursor"],
                                 relief=tk.FLAT, bd=1)
                elif isinstance(child, tk.Button):
                    child.config(bg=t["find_bg"], fg=t["fg"],
                                 activebackground=t["select_bg"])
            except Exception:
                pass

    def _on_text_modified(self, event=None):
        if self.text.edit_modified():
            self.modified = True
            self._update_status()
            self.text.edit_modified(False)

    def _on_key_release(self, event=None):
        self._update_status()
        self._redraw_line_numbers()


def main():
    root = tk.Tk()
    app = PyPad(root)
    root.mainloop()


if __name__ == "__main__":
    main()
