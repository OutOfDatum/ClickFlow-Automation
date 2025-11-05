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
```
### Running
python "ClickFlow Studio.py"

## How to Use
1. Add Steps:
    Use the GUI to define each automation step (click, type, hotkey, etc.). Capture mouse positions directly.

2. Configure Settings:
    Set number of cycles, delays, move speed, and enable/disable failsafe.

3. Save/Load Profiles:
    Save your automation as a profile (JSON). Load or create new profiles as needed.

4. Run Automation:
    Click “Start Automation”. Monitor progress and logs in real time.
5. Emergency Stop:
    Press F9 or move the mouse to a screen corner to halt automation instantly.

## Supported Actions
- Left Click / Right Click / Double Click
- Click & Hold / Release
- Type Text (fast or with special characters)
- Press Key (e.g., Enter, Tab, Esc)
- Key Down / Key Up (for holding/releasing keys)
- Hotkey Combination (e.g., Ctrl+C, Alt+Tab)
- Wait/Pause (custom duration)
- Move Only (move mouse, no click)

## Example Use Cases
- Automating data entry in legacy or web applications
- Repetitive software testing
- GUI workflow demonstrations
- Any scenario where you’re sick of clicking and typing the same thing

## Screenshots
  will add screen shots here

## Author
OutOfDatum
Manufacturing Execution Systems | Analyst | Continuous Improvement 
