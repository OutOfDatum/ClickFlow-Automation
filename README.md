# ClickFlow-Automation
Python tool for automating repetitive GUI tasks with a user-friendly interface and robust error handling.

# ClickFlow Studio

**Professional Desktop Automation Tool**  
Automate repetitive GUI tasks with a flexible, user-friendly interface.  
Designed for analysts, testers, and anyone who wants to eliminate manual clicking, typing, and data entry.

---

## Features

- **Visual step editor**: Add, edit, reorder, duplicate, and capture mouse/keyboard actions via GUI.
- **Supports complex actions**: Left/right/double clicks, click-and-hold, key presses, hotkeys, text entry (including special characters), waits, and pure mouse moves.
- **Profile management**: Save/load multiple automation profiles as JSON files.
- **Failsafe**: Emergency stop (F9) and mouse-corner failsafe to prevent runaway automation.
- **Logging and statistics**: Real-time log window and run statistics for transparency and troubleshooting.
- **No coding required**: All configuration via GUI.

---

## Quick Start

### Prerequisites

- **Python 3.8+**
- **Packages**:  
  - `pyautogui`
  - `tkinter` (standard with Python)
  - `pynput` (for hotkey support)

Install dependencies:
```bash
pip install pyautogui pynput
