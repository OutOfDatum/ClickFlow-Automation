import pyautogui
import time
import json
import logging
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
from pathlib import Path
from datetime import datetime
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'clickflow_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)


class AutomationConfig:
    """Configuration manager for automation coordinates and settings"""
    
    DEFAULT_CONFIG = {
        "failsafe_enabled": True,
        "initial_delay": 3,
        "move_duration": 0.3,
        "click_delay": 0.25,
        "steps": []
    }
    
    def __init__(self, config_file='clickflow_default.json'):
        self.config_file = Path(config_file)
        self.config = self.load_config()
    
    def load_config(self):
        """Load configuration from file or create default"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    loaded = json.load(f)
                    logging.info(f"Loaded configuration from {self.config_file}")
                    return loaded
            except Exception as e:
                logging.warning(f"Error loading config: {e}. Using defaults.")
        return self.DEFAULT_CONFIG.copy()
    
    def save_config(self, filepath=None):
        """Save current configuration to file"""
        save_path = Path(filepath) if filepath else self.config_file
        with open(save_path, 'w') as f:
            json.dump(self.config, f, indent=4)
        self.config_file = save_path
        logging.info(f"Configuration saved to {save_path}")


class AutomationRunner:
    """Main automation runner with error handling and statistics"""
    
    def __init__(self, config, log_callback=None):
        self.config = config
        self.log_callback = log_callback
        self.is_running = False
        self.should_stop = False
        self.stats = {
            "total_runs": 0,
            "successful_runs": 0,
            "failed_runs": 0,
            "total_time": 0,
            "cycle_times": []
        }
        pyautogui.FAILSAFE = config.config["failsafe_enabled"]
    
    def log(self, message, level="INFO"):
        """Log message with callback to GUI"""
        if self.log_callback:
            self.log_callback(message, level)
        if level == "ERROR":
            logging.error(message)
        else:
            logging.info(message)
    
    def execute_step(self, step):
        """Execute a single step based on its action type"""
        try:
            action = step.get("action", "left_click")
            
            # Move to position for actions that need it (not for key-only actions)
            if action not in ["press_key", "key_down", "key_up", "hotkey", "wait"]:
                pyautogui.moveTo(
                    step["x"], 
                    step["y"], 
                    duration=self.config.config["move_duration"]
                )
                time.sleep(self.config.config["click_delay"])
            
            if action == "left_click":
                pyautogui.click(button='left')
                self.log(f"✓ Left Click: {step['description']} at ({step['x']}, {step['y']})", "DEBUG")
            
            elif action == "right_click":
                pyautogui.click(button='right')
                self.log(f"✓ Right Click: {step['description']} at ({step['x']}, {step['y']})", "DEBUG")
            
            elif action == "double_click":
                pyautogui.doubleClick(button='left')
                self.log(f"✓ Double Click: {step['description']} at ({step['x']}, {step['y']})", "DEBUG")
            
            elif action == "left_hold":
                pyautogui.mouseDown(button='left')
                self.log(f"✓ Left Click Hold: {step['description']} at ({step['x']}, {step['y']})", "DEBUG")
            
            elif action == "left_release":
                pyautogui.mouseUp(button='left')
                self.log(f"✓ Left Click Release: {step['description']}", "DEBUG")
            
            elif action == "type_text":
                text = step.get("text", "")
                pyautogui.click(button='left')
                time.sleep(0.2)
                pyautogui.typewrite(text, interval=0.05)
                self.log(f"✓ Typed '{text}' at {step['description']}", "DEBUG")
            
            elif action == "type_text_hotkey":
                text = step.get("text", "")
                pyautogui.click(button='left')
                time.sleep(0.2)
                pyautogui.write(text, interval=0.05)
                self.log(f"✓ Typed '{text}' at {step['description']}", "DEBUG")
            
            elif action == "press_key":
                key = step.get("text", "enter")
                pyautogui.press(key)
                self.log(f"✓ Pressed key '{key}'", "DEBUG")
            
            elif action == "key_down":
                key = step.get("text", "shift")
                pyautogui.keyDown(key)
                self.log(f"✓ Key Down (hold) '{key}'", "DEBUG")
            
            elif action == "key_up":
                key = step.get("text", "shift")
                pyautogui.keyUp(key)
                self.log(f"✓ Key Up (release) '{key}'", "DEBUG")
            
            elif action == "hotkey":
                keys = step.get("text", "").split("+")
                pyautogui.hotkey(*keys)
                self.log(f"✓ Hotkey '{step['text']}'", "DEBUG")
            
            elif action == "wait":
                wait_time = float(step.get("text", "1"))
                time.sleep(wait_time)
                self.log(f"✓ Waited {wait_time}s: {step['description']}", "DEBUG")
            
            elif action == "move_only":
                self.log(f"✓ Moved to: {step['description']} at ({step['x']}, {step['y']})", "DEBUG")
            
            return True
            
        except Exception as e:
            self.log(f"✗ Error executing {step['name']}: {e}", "ERROR")
            return False
    
    def run_single_cycle(self, cycle_num):
        """Execute a single automation cycle"""
        self.log(f"\n{'='*50}")
        self.log(f"Starting Cycle {cycle_num}")
        self.log(f"{'='*50}")
        start_time = time.time()
        
        try:
            for step in self.config.config["steps"]:
                if self.should_stop:
                    self.log("⚠ Automation stopped by user", "WARNING")
                    return False, 0
                
                self.log(f"→ {step['description']}")
                if not self.execute_step(step):
                    raise Exception(f"Failed to execute {step['name']}")
            
            cycle_time = time.time() - start_time
            self.stats["successful_runs"] += 1
            self.stats["cycle_times"].append(cycle_time)
            self.log(f"✓ Cycle {cycle_num} completed in {cycle_time:.2f}s")
            return True, cycle_time
            
        except pyautogui.FailSafeException:
            self.log("⚠ Failsafe triggered! Mouse moved to corner.", "WARNING")
            return False, 0
        except Exception as e:
            self.log(f"✗ Cycle {cycle_num} failed: {e}", "ERROR")
            self.stats["failed_runs"] += 1
            return False, 0
    
    def run(self, loops):
        """Run automation for specified number of loops"""
        self.is_running = True
        self.should_stop = False
        self.stats = {
            "total_runs": loops,
            "successful_runs": 0,
            "failed_runs": 0,
            "total_time": 0,
            "cycle_times": []
        }
        
        self.log(f"\n{'='*50}")
        self.log(f"🚀 Starting automation: {loops} cycle(s)")
        self.log(f"Failsafe: {'ENABLED' if pyautogui.FAILSAFE else 'DISABLED'}")
        self.log(f"{'='*50}\n")
        
        delay = self.config.config['initial_delay']
        self.log(f"⏱ Waiting {delay} seconds before starting...")
        time.sleep(delay)
        
        overall_start = time.time()
        
        for i in range(loops):
            if self.should_stop:
                break
            
            success, cycle_time = self.run_single_cycle(i + 1)
            
            if not success and pyautogui.FAILSAFE:
                self.log("\n⚠ Automation stopped by failsafe or error.", "WARNING")
                break
            
            if i < loops - 1:
                time.sleep(0.5)
        
        self.stats["total_time"] = time.time() - overall_start
        self.print_statistics()
        self.is_running = False
    
    def stop(self):
        """Stop the automation"""
        self.should_stop = True
    
    def print_statistics(self):
        """Print automation statistics"""
        self.log(f"\n{'='*50}")
        self.log("📊 AUTOMATION STATISTICS")
        self.log(f"{'='*50}")
        self.log(f"Total runs:       {self.stats['total_runs']}")
        self.log(f"Successful:       {self.stats['successful_runs']}")
        self.log(f"Failed:           {self.stats['failed_runs']}")
        self.log(f"Total time:       {self.stats['total_time']:.2f}s")
        
        if self.stats["cycle_times"]:
            avg_time = sum(self.stats["cycle_times"]) / len(self.stats["cycle_times"])
            min_time = min(self.stats["cycle_times"])
            max_time = max(self.stats["cycle_times"])
            self.log(f"Average cycle:    {avg_time:.2f}s")
            self.log(f"Fastest cycle:    {min_time:.2f}s")
            self.log(f"Slowest cycle:    {max_time:.2f}s")
        
        self.log(f"{'='*50}\n")


class StepDialog:
    """Dialog for adding/editing steps"""
    
    ACTION_TYPES = [
        ("Left Click", "left_click"),
        ("Right Click", "right_click"),
        ("Double Click", "double_click"),
        ("Left Click & Hold", "left_hold"),
        ("Release Left Click", "left_release"),
        ("Type Text (fast)", "type_text"),
        ("Type Text (with special chars)", "type_text_hotkey"),
        ("Press Key", "press_key"),
        ("Key Down (hold)", "key_down"),
        ("Key Up (release)", "key_up"),
        ("Hotkey Combination", "hotkey"),
        ("Wait/Pause", "wait"),
        ("Move Only (no click)", "move_only")
    ]
    
    def __init__(self, parent, title, step=None):
        self.result = None
        self.captured_position = None
        
        dialog = tk.Toplevel(parent)
        dialog.title(title)
        dialog.geometry("500x500")
        dialog.resizable(True, True)
        dialog.transient(parent)
        dialog.attributes('-topmost', True)
        dialog.grab_set()
        
        dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - dialog.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")
        
        row = 0
        
        ttk.Label(dialog, text="Name:").grid(row=row, column=0, sticky=tk.W, padx=10, pady=10)
        name_var = tk.StringVar(value=step["name"] if step else "")
        name_entry = ttk.Entry(dialog, textvariable=name_var, width=40)
        name_entry.grid(row=row, column=1, padx=10, pady=10)
        row += 1
        
        ttk.Label(dialog, text="Action Type:").grid(row=row, column=0, sticky=tk.W, padx=10, pady=10)
        action_var = tk.StringVar(value=step.get("action", "left_click") if step else "left_click")
        action_combo = ttk.Combobox(dialog, textvariable=action_var, width=37, state='readonly')
        action_combo['values'] = [name for name, _ in self.ACTION_TYPES]
        current_action = step.get("action", "left_click") if step else "left_click"
        for display_name, action_value in self.ACTION_TYPES:
            if action_value == current_action:
                action_combo.set(display_name)
                break
        action_combo.grid(row=row, column=1, padx=10, pady=10)
        row += 1
        
        # Position frame with capture button
        position_frame = ttk.Frame(dialog)
        position_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=10, pady=5)
        
        ttk.Label(position_frame, text="X Position:").pack(side=tk.LEFT, padx=5)
        x_var = tk.IntVar(value=step["x"] if step else 0)
        x_entry = ttk.Entry(position_frame, textvariable=x_var, width=10)
        x_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(position_frame, text="Y Position:").pack(side=tk.LEFT, padx=5)
        y_var = tk.IntVar(value=step["y"] if step else 0)
        y_entry = ttk.Entry(position_frame, textvariable=y_var, width=10)
        y_entry.pack(side=tk.LEFT, padx=5)
        
        def capture_position_inline():
            capture_dialog = CaptureDialog(dialog, name_var.get() or "New Step")
            if capture_dialog.result:
                x_var.set(capture_dialog.result[0])
                y_var.set(capture_dialog.result[1])
                self.captured_position = capture_dialog.result
        
        ttk.Button(position_frame, text="📍 Capture", command=capture_position_inline).pack(side=tk.LEFT, padx=10)
        row += 1
        
        ttk.Label(dialog, text="Text/Value:").grid(row=row, column=0, sticky=tk.W, padx=10, pady=10)
        text_var = tk.StringVar(value=step.get("text", "") if step else "")
        text_entry = ttk.Entry(dialog, textvariable=text_var, width=40)
        text_entry.grid(row=row, column=1, padx=10, pady=10)
        row += 1
        
        # Help text for current action
        help_frame = ttk.LabelFrame(dialog, text="Action Help", padding="10")
        help_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=10, pady=10)
        
        help_text = tk.Text(help_frame, height=6, width=55, wrap=tk.WORD, state='disabled')
        help_text.pack()
        
        def update_help(*args):
            selected_display = action_combo.get()
            help_messages = {
                "Left Click": "Performs a standard left mouse button click at the specified position.",
                "Right Click": "Performs a right mouse button click at the specified position.",
                "Double Click": "Performs a double left-click at the specified position.",
                "Left Click & Hold": "Presses and HOLDS the left mouse button down (use with Release).",
                "Release Left Click": "Releases the left mouse button (after a hold action).",
                "Type Text (fast)": "Types the text from Text/Value field. Works for basic text only (a-z, 0-9).",
                "Type Text (with special chars)": "Types text including special characters, unicode. Slower but more compatible.",
                "Press Key": "Presses a single key. Enter key name in Text/Value (e.g., 'enter', 'tab', 'esc', 'space').",
                "Key Down (hold)": "Presses and HOLDS a key down. Enter key name in Text/Value (e.g., 'shift', 'ctrl').",
                "Key Up (release)": "Releases a held key. Enter key name in Text/Value (e.g., 'shift', 'ctrl').",
                "Hotkey Combination": "Presses multiple keys simultaneously. Enter keys separated by '+' (e.g., 'ctrl+c', 'alt+tab').",
                "Wait/Pause": "Pauses execution. Enter wait time in seconds in Text/Value field (e.g., '2.5').",
                "Move Only (no click)": "Just moves the mouse to the position without clicking."
            }
            
            help_text.config(state='normal')
            help_text.delete(1.0, tk.END)
            help_text.insert(1.0, help_messages.get(selected_display, ""))
            help_text.config(state='disabled')
        
        action_combo.bind('<<ComboboxSelected>>', update_help)
        update_help()
        
        row += 1
        
        ttk.Label(dialog, text="Description:").grid(row=row, column=0, sticky=tk.W, padx=10, pady=10)
        desc_var = tk.StringVar(value=step["description"] if step else "")
        ttk.Entry(dialog, textvariable=desc_var, width=40).grid(row=row, column=1, padx=10, pady=10)
        row += 1
        
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=row, column=0, columnspan=2, pady=20)
        
        def on_ok():
            if not name_var.get():
                messagebox.showwarning("Validation Error", "Name is required")
                return
            
            selected_display = action_combo.get()
            action_value = "left_click"
            for display_name, val in self.ACTION_TYPES:
                if display_name == selected_display:
                    action_value = val
                    break
            
            self.result = {
                "name": name_var.get(),
                "action": action_value,
                "x": x_var.get(),
                "y": y_var.get(),
                "text": text_var.get(),
                "description": desc_var.get()
            }
            dialog.destroy()
        
        ttk.Button(button_frame, text="OK", command=on_ok, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy, width=15).pack(side=tk.LEFT, padx=5)
        
        name_entry.focus()
        dialog.wait_window()


class CaptureDialog:
    """Dialog for capturing mouse position"""
    
    def __init__(self, parent, step_name):
        self.result = None
        self.listening = False
        self.last_click_time = 0
        self.countdown_active = False
        
        dialog = tk.Toplevel(parent)
        dialog.title("Capture Position")
        dialog.geometry("550x280")
        dialog.resizable(True, True)
        dialog.transient(parent)
        dialog.attributes('-topmost', True)
        dialog.grab_set()
        
        dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - dialog.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")
        
        ttk.Label(dialog, text=f"Capturing position for: {step_name}", 
                 font=('Arial', 12, 'bold')).pack(pady=15)
        
        instruction_label = ttk.Label(dialog, 
                                      text="Choose a capture method below", 
                                      font=('Arial', 10))
        instruction_label.pack(pady=10)
        
        position_label = ttk.Label(dialog, text="Current position: X=0, Y=0", 
                                   font=('Arial', 10))
        position_label.pack(pady=10)
        
        delay_frame = ttk.Frame(dialog)
        delay_frame.pack(pady=5)
        
        ttk.Label(delay_frame, text="Delay (seconds):").pack(side=tk.LEFT, padx=5)
        delay_var = tk.IntVar(value=3)
        ttk.Spinbox(delay_frame, from_=1, to=10, textvariable=delay_var, width=5).pack(side=tk.LEFT, padx=5)
        
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=15)
        
        start_button = ttk.Button(button_frame, text="⏱️ Start Listening (with delay)")
        start_button.pack(side=tk.LEFT, padx=5)
        
        instant_button = ttk.Button(button_frame, text="⚡ Instant Listen")
        instant_button.pack(side=tk.LEFT, padx=5)
        
        manual_capture_button = ttk.Button(button_frame, text="📍 Capture Current")
        manual_capture_button.pack(side=tk.LEFT, padx=5)
        
        cancel_button = ttk.Button(button_frame, text="Cancel", command=dialog.destroy)
        cancel_button.pack(side=tk.LEFT, padx=5)
        
        def update_position():
            if dialog.winfo_exists():
                x, y = pyautogui.position()
                position_label.config(text=f"Current position: X={x}, Y={y}")
                dialog.after(50, update_position)
        
        def countdown(seconds_left):
            if dialog.winfo_exists() and self.countdown_active:
                if seconds_left > 0:
                    instruction_label.config(
                        text=f"⏳ Capturing in {seconds_left}... (Click dropdown now!)", 
                        foreground='orange'
                    )
                    dialog.after(1000, lambda: countdown(seconds_left - 1))
                else:
                    instruction_label.config(
                        text="🎯 Ready! LEFT CLICK to capture position", 
                        foreground='red'
                    )
                    self.listening = True
                    check_click()
        
        def check_click():
            if dialog.winfo_exists() and self.listening:
                try:
                    import ctypes
                    left_button_state = ctypes.windll.user32.GetAsyncKeyState(0x01)
                    
                    if left_button_state & 0x8000:
                        current_time = time.time()
                        if current_time - self.last_click_time > 0.3:
                            self.last_click_time = current_time
                            x, y = pyautogui.position()
                            self.result = (x, y)
                            self.listening = False
                            dialog.destroy()
                            return
                    
                    dialog.after(50, check_click)
                except:
                    dialog.after(50, check_click)
        
        def manual_capture():
            x, y = pyautogui.position()
            self.result = (x, y)
            dialog.destroy()
        
        def start_listening_with_delay():
            self.countdown_active = True
            self.last_click_time = time.time()
            start_button.config(state='disabled')
            instant_button.config(state='disabled')
            manual_capture_button.config(state='disabled')
            countdown(delay_var.get())
        
        def start_listening_instant():
            self.listening = True
            self.last_click_time = time.time()
            start_button.config(state='disabled')
            instant_button.config(state='disabled')
            manual_capture_button.config(state='disabled')
            instruction_label.config(text="🎯 Listening... LEFT CLICK anywhere to capture position", 
                                    foreground='red')
            check_click()
        
        start_button.config(command=start_listening_with_delay)
        instant_button.config(command=start_listening_instant)
        manual_capture_button.config(command=manual_capture)
        
        update_position()
        dialog.wait_window()


class AutomationGUI:
    """Tkinter GUI for ClickFlow Studio"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("ClickFlow Studio - Professional Automation Tool")
        self.root.geometry("1200x750")
        
        self.config = AutomationConfig()
        self.runner = None
        self.automation_thread = None
        self.hotkey_listener = None
        self.current_profile = "clickflow_default.json"
        
        self.create_widgets()
        self.load_steps()
        self.setup_hotkey_listener()
        self.update_title()
        
    def update_title(self):
        """Update window title with current profile"""
        profile_name = Path(self.current_profile).stem
        self.root.title(f"ClickFlow Studio - {profile_name}")
    
    def create_widgets(self):
        """Create all GUI widgets"""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        settings_frame = ttk.LabelFrame(main_frame, text="Settings", padding="10")
        settings_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(settings_frame, text="Number of Cycles:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.loops_var = tk.IntVar(value=1)
        ttk.Spinbox(settings_frame, from_=1, to=1000, textvariable=self.loops_var, width=10).grid(row=0, column=1, padx=5)
        
        ttk.Label(settings_frame, text="Initial Delay (s):").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.delay_var = tk.DoubleVar(value=self.config.config["initial_delay"])
        ttk.Spinbox(settings_frame, from_=0, to=10, increment=0.5, textvariable=self.delay_var, width=10).grid(row=0, column=3, padx=5)
        
        ttk.Label(settings_frame, text="Move Duration (s):").grid(row=0, column=4, sticky=tk.W, padx=5)
        self.move_duration_var = tk.DoubleVar(value=self.config.config["move_duration"])
        ttk.Spinbox(settings_frame, from_=0, to=2, increment=0.1, textvariable=self.move_duration_var, width=10).grid(row=0, column=5, padx=5)
        
        self.failsafe_var = tk.BooleanVar(value=self.config.config["failsafe_enabled"])
        ttk.Checkbutton(settings_frame, text="Enable Failsafe", variable=self.failsafe_var).grid(row=0, column=6, padx=10)
        
        self.always_on_top_var = tk.BooleanVar(value=False)
        always_on_top_check = ttk.Checkbutton(settings_frame, text="📌 Pin Window", 
                                               variable=self.always_on_top_var,
                                               command=self.toggle_always_on_top)
        always_on_top_check.grid(row=0, column=7, padx=10)
        
        steps_frame = ttk.LabelFrame(main_frame, text="Automation Steps", padding="10")
        steps_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        steps_frame.columnconfigure(0, weight=1)
        steps_frame.rowconfigure(0, weight=1)
        
        columns = ("name", "action", "x", "y", "text", "description")
        self.steps_tree = ttk.Treeview(steps_frame, columns=columns, show="headings", height=10)
        
        self.steps_tree.heading("name", text="Name")
        self.steps_tree.heading("action", text="Action")
        self.steps_tree.heading("x", text="X")
        self.steps_tree.heading("y", text="Y")
        self.steps_tree.heading("text", text="Text/Value")
        self.steps_tree.heading("description", text="Description")
        
        self.steps_tree.column("name", width=120)
        self.steps_tree.column("action", width=100)
        self.steps_tree.column("x", width=60)
        self.steps_tree.column("y", width=60)
        self.steps_tree.column("text", width=120)
        self.steps_tree.column("description", width=250)
        
        scrollbar = ttk.Scrollbar(steps_frame, orient=tk.VERTICAL, command=self.steps_tree.yview)
        self.steps_tree.configure(yscroll=scrollbar.set)
        
        self.steps_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        step_buttons_frame = ttk.Frame(main_frame)
        step_buttons_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(step_buttons_frame, text="➕ Add Step", command=self.add_step).pack(side=tk.LEFT, padx=5)
        ttk.Button(step_buttons_frame, text="✏️ Edit Step", command=self.edit_step).pack(side=tk.LEFT, padx=5)
        ttk.Button(step_buttons_frame, text="📍 Capture Position", command=self.capture_position).pack(side=tk.LEFT, padx=5)
        ttk.Button(step_buttons_frame, text="🗑️ Delete Step", command=self.delete_step).pack(side=tk.LEFT, padx=5)
        ttk.Button(step_buttons_frame, text="⬆️ Move Up", command=self.move_step_up).pack(side=tk.LEFT, padx=5)
        ttk.Button(step_buttons_frame, text="⬇️ Move Down", command=self.move_step_down).pack(side=tk.LEFT, padx=5)
        ttk.Button(step_buttons_frame, text="📋 Duplicate", command=self.duplicate_step).pack(side=tk.LEFT, padx=5)
        
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="10")
        log_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, state='disabled')
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=4, column=0, sticky=(tk.W, tk.E))
        
        self.start_button = ttk.Button(control_frame, text="▶️ Start Automation", command=self.start_automation)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(control_frame, text="⏹️ Stop", command=self.stop_automation, state='disabled')
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Separator(control_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        ttk.Button(control_frame, text="💾 Save Profile", command=self.save_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="💾 Save As...", command=self.save_config_as).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="📂 Load Profile", command=self.load_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="🆕 New Profile", command=self.new_profile).pack(side=tk.LEFT, padx=5)
        
        ttk.Separator(control_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        ttk.Button(control_frame, text="🗑️ Clear Log", command=self.clear_log).pack(side=tk.LEFT, padx=5)
        
        hotkey_label = ttk.Label(control_frame, text="⚡ Emergency Stop: F9", foreground='red', font=('Arial', 9, 'bold'))
        hotkey_label.pack(side=tk.RIGHT, padx=10)
        
    def load_steps(self):
        """Load steps into treeview"""
        for item in self.steps_tree.get_children():
            self.steps_tree.delete(item)
        
        for step in self.config.config["steps"]:
            self.steps_tree.insert("", tk.END, values=(
                step["name"],
                step.get("action", "left_click"),
                step["x"],
                step["y"],
                step.get("text", ""),
                step["description"]
            ))
    
    def add_step(self):
        """Add a new step"""
        dialog = StepDialog(self.root, "Add Step")
        if dialog.result:
            self.config.config["steps"].append(dialog.result)
            self.load_steps()
            self.log_message("Step added successfully")
    
    def edit_step(self):
        """Edit selected step"""
        selection = self.steps_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a step to edit")
            return
        
        index = self.steps_tree.index(selection[0])
        step = self.config.config["steps"][index]
        
        dialog = StepDialog(self.root, "Edit Step", step)
        if dialog.result:
            self.config.config["steps"][index] = dialog.result
            self.load_steps()
            self.log_message("Step updated successfully")
    
    def capture_position(self):
        """Capture mouse position for selected step"""
        selection = self.steps_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a step to capture position")
            return
        
        index = self.steps_tree.index(selection[0])
        step = self.config.config["steps"][index]
        
        dialog = CaptureDialog(self.root, step["name"])
        if dialog.result:
            step["x"] = dialog.result[0]
            step["y"] = dialog.result[1]
            self.load_steps()
            self.log_message(f"Position captured for {step['name']}: ({step['x']}, {step['y']})")
    
    def delete_step(self):
        """Delete selected step"""
        selection = self.steps_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a step to delete")
            return
        
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this step?"):
            index = self.steps_tree.index(selection[0])
            del self.config.config["steps"][index]
            self.load_steps()
            self.log_message("Step deleted successfully")
    
    def duplicate_step(self):
        """Duplicate selected step"""
        selection = self.steps_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a step to duplicate")
            return
        
        index = self.steps_tree.index(selection[0])
        step = self.config.config["steps"][index].copy()
        step["name"] = step["name"] + "_copy"
        self.config.config["steps"].insert(index + 1, step)
        self.load_steps()
        self.log_message("Step duplicated successfully")
    
    def move_step_up(self):
        """Move selected step up"""
        selection = self.steps_tree.selection()
        if not selection:
            return
        
        index = self.steps_tree.index(selection[0])
        if index > 0:
            self.config.config["steps"][index], self.config.config["steps"][index-1] = \
                self.config.config["steps"][index-1], self.config.config["steps"][index]
            self.load_steps()
            new_item = self.steps_tree.get_children()[index-1]
            self.steps_tree.selection_set(new_item)
    
    def move_step_down(self):
        """Move selected step down"""
        selection = self.steps_tree.selection()
        if not selection:
            return
        
        index = self.steps_tree.index(selection[0])
        if index < len(self.config.config["steps"]) - 1:
            self.config.config["steps"][index], self.config.config["steps"][index+1] = \
                self.config.config["steps"][index+1], self.config.config["steps"][index]
            self.load_steps()
            new_item = self.steps_tree.get_children()[index+1]
            self.steps_tree.selection_set(new_item)
    
    def new_profile(self):
        """Create a new profile"""
        if messagebox.askyesno("New Profile", "Create a new profile? Any unsaved changes will be lost."):
            self.config = AutomationConfig()
            self.config.config["steps"] = []
            self.current_profile = "clickflow_default.json"
            self.load_steps()
            self.update_title()
            self.log_message("New profile created")
    
    def save_config(self):
        """Save configuration to current file"""
        self.config.config["initial_delay"] = self.delay_var.get()
        self.config.config["move_duration"] = self.move_duration_var.get()
        self.config.config["failsafe_enabled"] = self.failsafe_var.get()
        
        self.config.save_config(self.current_profile)
        self.log_message(f"Profile saved to {self.current_profile}")
        messagebox.showinfo("Success", f"Profile saved to {self.current_profile}")
    
    def save_config_as(self):
        """Save configuration to a new file"""
        filepath = filedialog.asksaveasfilename(
            title="Save Profile As",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile="clickflow_profile.json"
        )
        
        if filepath:
            self.config.config["initial_delay"] = self.delay_var.get()
            self.config.config["move_duration"] = self.move_duration_var.get()
            self.config.config["failsafe_enabled"] = self.failsafe_var.get()
            
            self.config.save_config(filepath)
            self.current_profile = filepath
            self.update_title()
            self.log_message(f"Profile saved to {filepath}")
            messagebox.showinfo("Success", f"Profile saved to {filepath}")
    
    def load_config(self):
        """Load configuration from a file"""
        filepath = filedialog.askopenfilename(
            title="Load Profile",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filepath:
            self.config = AutomationConfig(filepath)
            self.current_profile = filepath
            self.load_steps()
            
            self.delay_var.set(self.config.config["initial_delay"])
            self.move_duration_var.set(self.config.config["move_duration"])
            self.failsafe_var.set(self.config.config["failsafe_enabled"])
            
            self.update_title()
            self.log_message(f"Profile loaded from {filepath}")
            messagebox.showinfo("Success", f"Profile loaded from {filepath}")
    
    def log_message(self, message, level="INFO"):
        """Add message to log"""
        self.log_text.configure(state='normal')
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state='disabled')
    
    def clear_log(self):
        """Clear the log"""
        self.log_text.configure(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state='disabled')
    
    def toggle_always_on_top(self):
        """Toggle always on top"""
        self.root.attributes('-topmost', self.always_on_top_var.get())
    
    def setup_hotkey_listener(self):
        """Setup keyboard listener for emergency stop hotkey"""
        try:
            from pynput import keyboard
            
            def on_press(key):
                try:
                    if key == keyboard.Key.f9:
                        if self.runner and self.runner.is_running:
                            self.log_message("🚨 EMERGENCY STOP (F9) - Terminating automation!", "ERROR")
                            self.stop_automation()
                except:
                    pass
            
            self.hotkey_listener = keyboard.Listener(on_press=on_press)
            self.hotkey_listener.daemon = True
            self.hotkey_listener.start()
            self.log_message("✓ Hotkey listener active: Press F9 for emergency stop")
        except ImportError:
            self.log_message("⚠ Warning: pynput not installed. Emergency hotkey (F9) not available.", "WARNING")
            self.log_message("  Install with: pip install pynput", "WARNING")
    
    def start_automation(self):
        """Start the automation in a separate thread"""
        self.config.config["initial_delay"] = self.delay_var.get()
        self.config.config["move_duration"] = self.move_duration_var.get()
        self.config.config["click_delay"] = 0.25
        self.config.config["failsafe_enabled"] = self.failsafe_var.get()
        
        if not self.config.config["steps"]:
            messagebox.showwarning("No Steps", "Please add at least one step before starting")
            return
        
        loops = self.loops_var.get()
        
        self.start_button.configure(state='disabled')
        self.stop_button.configure(state='normal')
        
        self.runner = AutomationRunner(self.config, log_callback=self.log_message)
        
        def run_in_thread():
            self.runner.run(loops)
            self.root.after(0, self.automation_finished)
        
        self.automation_thread = threading.Thread(target=run_in_thread, daemon=True)
        self.automation_thread.start()
    
    def stop_automation(self):
        """Stop the automation"""
        if self.runner:
            self.runner.stop()
            self.log_message("Stopping automation...", "WARNING")
    
    def automation_finished(self):
        """Called when automation finishes"""
        self.start_button.configure(state='normal')
        self.stop_button.configure(state='disabled')


def main():
    """Main entry point"""
    root = tk.Tk()
    app = AutomationGUI(root)
    
    def on_closing():
        """Handle window closing"""
        if app.hotkey_listener:
            app.hotkey_listener.stop()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.error(f"Unexpected error: {e}", exc_info=True)
        messagebox.showerror("Fatal Error", f"An unexpected error occurred:\n{e}")
