# PyPad

A lightweight, no-nonsense text editor built entirely in Python using only the standard library. No pip. No installs. Just run it.

---

## Why PyPad?

Most text editors are bloated. PyPad is not. It opens instantly, uses almost no memory, and works on any machine that has Python — including old school laptops, Chromebooks running Linux, and low-spec classroom computers.

One file. One command. Done.

---

## Features

- **Open / Save / Save As** — full file management with unsaved-changes protection
- **Find & Replace** — inline bar with Find Next, Replace, and Replace All
- **Word Wrap toggle** — switch between wrapped and unwrapped mode
- **Line numbers** — optional gutter, toggleable from the View menu
- **Status bar** — live line and column position, modified indicator, filename
- **Light & Dark theme** — full palette swap, one click

---

## Getting Started

**Requirements:** Python 3.10+ (uses `str | None` type hint syntax)

```bash
python pypad.py
```

That's it. No virtual environment, no dependencies, no setup.

---

## Keyboard Shortcuts

| Action | Shortcut |
|---|---|
| New file | `Ctrl+N` |
| Open file | `Ctrl+O` |
| Save | `Ctrl+S` |
| Save As | `Ctrl+Shift+S` |
| Find & Replace | `Ctrl+F` |
| Close Find bar | `Esc` |
| Undo | `Ctrl+Z` |
| Redo | `Ctrl+Y` |
| Select All | `Ctrl+A` |

---

## Screenshots

> Light and dark themes, with line numbers and the Find & Replace bar.

*(Add your screenshots here)*

---

## Platform Support

| Platform | Status |
|---|---|
| Windows | ✅ |
| macOS | ✅ |
| Linux | ✅ |

Tkinter ships with Python on all major platforms. On some minimal Linux installs you may need to run `sudo apt install python3-tk` first.

---

## Project Structure

```
pypad.py   ← the entire application, ~455 lines
README.md
```

---

## Design Philosophy

- Single `.py` file, zero external imports
- No plugin system, no tabs, no bloat
- Designed to run on the weakest hardware in the room
- Code is readable first, clever second

---

## License

MIT — do whatever you want with it.
