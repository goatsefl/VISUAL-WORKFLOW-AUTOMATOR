# ================== Core Libraries ==================
# tkinter is Python's standard library for creating graphical user interfaces (GUIs).
# We use 'tk' for the basic widgets and 'ttk' for the more modern, themed widgets.
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox, filedialog

# pyautogui is the key library for programmatically controlling the mouse and keyboard.
import pyautogui

# threading allows us to run the automation workflow in the background, so the GUI
# doesn't freeze up while the mouse and keyboard are being controlled.
import threading

# time is used for delays (time.sleep) to make the automation more stable.
import time

# json is used for saving and loading the workflow steps to/from a file.
import json

# os is used for interacting with the operating system, like creating directories
# and checking which OS we're running on.
import os

# =================== Helper Functions ===================
# These small functions help make the main code cleaner by handling specific checks.

def is_macos():
    """Checks if the current operating system is macOS."""
    return os.sys.platform == "darwin"

def is_linux():
    """Checks if the current operating system is Linux."""
    return os.sys.platform.startswith("linux")

def get_hotkey_modifier():
    """Returns the correct modifier key ('command' or 'ctrl') for hotkeys based on the OS."""
    return "command" if is_macos() else "ctrl"

def running_on_wayland():
    """Detects if the session on Linux is Wayland, which can affect automation tools."""
    return os.environ.get("WAYLAND_DISPLAY") or os.environ.get("XDG_SESSION_TYPE") == "wayland"

def warn_linux_requirements():
    """
    On Linux, pyautogui often needs extra packages to work correctly. This function
    checks for them and shows a warning if they are missing.
    """
    missing = []
    try:
        import Xlib  # type: ignore
    except Exception:
        missing.append("python3-xlib") # Needed for display control
    if os.system("which scrot >/dev/null 2>&1") != 0:
        missing.append("scrot") # Needed for taking screenshots (used by image recognition)
    
    msgs = []
    if running_on_wayland():
        msgs.append(
            "Detected Wayland session. Some desktop environments restrict simulated input. "
            "If hotkeys fail, try an X11 session or enable automation permissions."
        )
    if missing:
        msgs.append("Missing packages: " + ", ".join(missing) + ". Install for best compatibility.")
    
    if msgs:
        # We use a try-except block here because this can run before the main GUI
        # is fully ready, and we don't want it to crash the app.
        try:
            messagebox.showwarning("Linux environment notice", "\n\n".join(msgs))
        except Exception:
            pass

# Create a directory to store saved workflows if it doesn't already exist.
PRESETS_DIR = "workflow_presets"
os.makedirs(PRESETS_DIR, exist_ok=True)

# ---- Recorder: uses pynput to capture mouse/keyboard and converts into steps ----
# This is an optional feature. You need to install pynput: pip install pynput
def record_mouse_keyboard_session(stop_key='esc', stop_right_hold_sec=2.0):
    """
    Records mouse and keyboard events into a list of steps.
    - Stops when the ESC key is pressed.
    - Also stops if the right mouse button is held for 2 seconds and then released.
    This provides two convenient ways to end the recording session.
    """
    try:
        from pynput import mouse as _mouse, keyboard as _keyboard
    except Exception as e:
        messagebox.showerror("Recorder Error", "pynput is required. Install with: pip install pynput")
        return []

    rec = []  # The list where we'll store the recorded steps.
    start_time = None
    last_time = None
    right_pressed_time = None

    def now():
        """A simple helper to get the current time."""
        return time.time()

    def add_delay_and_append(step):
        """Calculates the delay since the last event and adds the new step to our list."""
        nonlocal last_time, start_time
        t = now()
        if start_time is None:
            start_time = t
            delay = 0.0
        else:
            # The delay is the time elapsed since the last recorded event.
            delay = max(0.0, t - last_time)
        step['delay'] = round(delay, 3) # Round to 3 decimal places.
        rec.append(step)
        last_time = t

    # --- pynput event handlers ---
    def on_press(key):
        """This function is called every time a key is pressed."""
        try:
            if hasattr(key, 'char') and key.char:
                # If it's a normal character, add it as a "Type Text" step.
                add_delay_and_append({"type":"keyboard","action":"Type Text","value":key.char})
            else:
                # If it's a special key (like Enter, Shift, etc.), handle it.
                if key == _keyboard.Key.esc:
                    # ESC key stops the recording.
                    return False # Returning False from a pynput listener stops it.
                add_delay_and_append({"type":"keyboard","action":"Press Key","value":str(key).replace('Key.','')})
        except Exception:
            pass

    def on_click(x, y, button, pressed):
        """This function is called for every mouse click."""
        nonlocal right_pressed_time
        if button == _mouse.Button.right and pressed:
            # When the right button is pressed down, record the time.
            right_pressed_time = now()
        if button == _mouse.Button.right and not pressed and right_pressed_time:
            # When the right button is released, check how long it was held.
            if now() - right_pressed_time >= stop_right_hold_sec:
                return False # If held long enough, stop the listener.
        if pressed:
            # For any other click, record it as a "Click" action.
            add_delay_and_append({"type":"mouse","action":"Click","x":x,"y":y})
        return True

    # We start listening for both keyboard and mouse events at the same time.
    kb_listener = _keyboard.Listener(on_press=on_press)
    ms_listener = _mouse.Listener(on_click=on_click)
    kb_listener.start()
    ms_listener.start()
    kb_listener.join() # Wait for the keyboard listener to stop.
    ms_listener.join() # Wait for the mouse listener to stop.

    # --- Post-processing: Clean up the recorded steps ---
    # This loop merges consecutive single-character "Type Text" events into one.
    # For example, typing "hello" would be recorded as 5 separate steps. This
    # combines them into a single step: {"action": "Type Text", "value": "hello"}.
    merged = []
    buffer_text = ""
    buffer_delay = 0.0
    for step in rec:
        if step["type"] == "keyboard" and step["action"] == "Type Text" and len(step["value"]) == 1:
            if not buffer_text:
                # This is the start of a new text block, so store its initial delay.
                buffer_delay = step.get("delay", 0.0)
            buffer_text += step["value"]
        else:
            if buffer_text:
                # We've hit a non-text step, so add the buffered text as a single step.
                merged.append({"type":"keyboard","action":"Type Text","value":buffer_text,"delay":buffer_delay})
                buffer_text = "" # Reset the buffer.
            merged.append(step)
    if buffer_text:
        # Add any remaining text in the buffer at the end.
        merged.append({"type":"keyboard","action":"Type Text","value":buffer_text,"delay":buffer_delay})

    return merged

# ------------------ Dialog Windows For Each Step Type ------------------
# Each class below defines a pop-up window for adding or editing a specific
# type of step in the workflow. They all inherit from `simpledialog.Dialog`.

class AddMouseStepDialog(simpledialog.Dialog):
    """The pop-up window for adding or editing a mouse action."""
    def __init__(self, parent, title=None, init_data=None):
        self.init_data = init_data or {} # `init_data` holds the step's current values when editing.
        super().__init__(parent, title)

    def body(self, master):
        """This method creates all the widgets (labels, entry boxes, buttons) in the dialog."""
        # Action dropdown (Click, Right Click, etc.)
        ttk.Label(master, text="Action:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.action_var = tk.StringVar(value=self.init_data.get("action", "Click"))
        self.action_menu = ttk.Combobox(master, textvariable=self.action_var,
                                        values=["Click", "Right Click", "Hold", "Release"],
                                        state="readonly")
        self.action_menu.grid(row=0, column=1, padx=5, pady=5)

        # X and Y coordinate entry boxes
        ttk.Label(master, text="X:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.x_entry = ttk.Entry(master)
        self.x_entry.insert(0, str(self.init_data.get("x", "")))
        self.x_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(master, text="Y:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.y_entry = ttk.Entry(master)
        self.y_entry.insert(0, str(self.init_data.get("y", "")))
        self.y_entry.grid(row=2, column=1, padx=5, pady=5)

        # Delay entry box
        ttk.Label(master, text="Delay (sec):").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.delay_entry = ttk.Entry(master)
        self.delay_entry.insert(0, str(self.init_data.get("delay", 0.1)))
        self.delay_entry.grid(row=3, column=1, padx=5, pady=5)

        # A button to automatically get the current mouse coordinates.
        btn = ttk.Button(master, text="Get Current Mouse Position", command=self.get_coords)
        btn.grid(row=4, columnspan=2, pady=10)
        self.result = None
        return self.x_entry # This sets the initial focus on the X entry box.

    def get_coords(self):
        """
        A helper function to grab the mouse's current X,Y position.
        It hides the dialog, waits 3 seconds, gets the position, and then shows the dialog again.
        """
        self.withdraw() # Hide the dialog temporarily.
        messagebox.showinfo("Position", "Move your mouse to the target position and wait 3 seconds.", parent=self.master)
        time.sleep(3)
        x, y = pyautogui.position()
        self.x_entry.delete(0, tk.END)
        self.x_entry.insert(0, str(x))
        self.y_entry.delete(0, tk.END)
        self.y_entry.insert(0, str(y))
        self.deiconify() # Show the dialog again.
        self.lift() # Bring it to the front.

    def apply(self):
        """
        This method is called when the user clicks "OK". It reads the values from the
        widgets, validates them, and stores the final step data in `self.result`.
        """
        try:
            self.result = {
                "type": "mouse",
                "action": self.action_var.get(),
                "x": int(self.x_entry.get()),
                "y": int(self.y_entry.get()),
                "delay": float(self.delay_entry.get())
            }
        except ValueError:
            messagebox.showerror("Error", "Invalid coordinates or delay. Please enter valid numbers.", parent=self.master)
            self.result = None # If validation fails, result is None, and the dialog stays open.

class AddKeyboardStepDialog(simpledialog.Dialog):
    """The pop-up window for adding or editing a keyboard action."""
    def __init__(self, parent, title=None, init_data=None):
        self.init_data = init_data or {}
        super().__init__(parent, title)

    def body(self, master):
        ttk.Label(master, text="Action:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.action_var = tk.StringVar(value=self.init_data.get("action", "Type Text"))
        self.action_menu = ttk.Combobox(master, textvariable=self.action_var,
                                        values=["Type Text", "Press Key", "Hotkey"],
                                        state="readonly")
        self.action_menu.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(master, text="Value:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.value_entry = ttk.Entry(master, width=40)
        self.value_entry.insert(0, self.init_data.get("value", ""))
        self.value_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(master, text="Delay (sec):").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.delay_entry = ttk.Entry(master)
        self.delay_entry.insert(0, str(self.init_data.get("delay", 0.1)))
        self.delay_entry.grid(row=2, column=1, padx=5, pady=5)
        return self.value_entry

    def apply(self):
        if not self.value_entry.get():
            messagebox.showerror("Error", "Value cannot be empty.", parent=self.master)
            self.result = None
            return
        try:
            self.result = {
                "type": "keyboard",
                "action": self.action_var.get(),
                "value": self.value_entry.get(),
                "delay": float(self.delay_entry.get())
            }
        except ValueError:
            messagebox.showerror("Error", "Invalid delay. Please enter a valid number.", parent=self.master)
            self.result = None

class AddImageStepDialog(simpledialog.Dialog):
    """The pop-up window for adding or editing an image-based click action."""
    def __init__(self, parent, title=None, init_data=None):
        self.init_data = init_data or {}
        super().__init__(parent, title)

    def body(self, master):
        ttk.Label(master, text="Image file:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.path_var = tk.StringVar(value=self.init_data.get("path", ""))
        path_entry = ttk.Entry(master, textvariable=self.path_var, width=40)
        path_entry.grid(row=0, column=1, padx=5, pady=2)
        ttk.Button(master, text="Browse", command=self._browse).grid(row=0, column=2, padx=5)
        return path_entry

    def _browse(self):
        """Opens a file dialog to let the user select a PNG image file."""
        fp = filedialog.askopenfilename(
            title="Select Screenshot Image",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")], 
            parent=self.master
        )
        if fp:
            self.path_var.set(fp)

    def apply(self):
        path = self.path_var.get()
        if not path or not os.path.isfile(path):
            messagebox.showerror("Error", "You must select a valid image file.", parent=self.master)
            self.result = None
            return
        self.result = {
            "type": "image",
            "path": path,
            "delay": float(self.init_data.get("delay", 0.5)), # Default delay is higher for image search
        }

def get_step_display_text(step):
    """
    A helper function that takes a step dictionary and returns a human-readable
    string summarizing what the step does. This is used to display the steps in the main listbox.
    """
    s_type = step.get("type", "unknown")
    if s_type == "mouse":
        return f"MOUSE {step['action']} at ({step['x']},{step['y']})"
    if s_type == "keyboard":
        if step["action"] == "Type Text":
            # Truncate long text for better display.
            preview = step['value']
            if len(preview) > 20:
                preview = preview[:20] + "..."
            return f"KEYBOARD {step['action']}: '{preview}'"
        return f"KEYBOARD {step['action']}: '{step['value']}'"
    if s_type == "image":
        # Only show the filename, not the full path.
        return f"IMAGE click '{os.path.basename(step['path'])}'"
    if s_type == "conditional_record":
        num_cases = len(step.get("cases", []))
        num_else = len(step.get("else_steps", []))
        src = step.get("source", "clipboard")
        return f"COND-RECORD ({src}) {num_cases} cases, else:{num_else} steps"
    
    # === LOOP FEATURE: Display Text ===
    # This part defines how a "loop" step will appear in the main workflow list.
    if s_type == "loop":
        count = step.get("count", 0)
        num_steps = len(step.get("steps", []))
        return f"LOOP BLOCK ({count} times, {num_steps} steps)"
    # === END LOOP FEATURE ===

    return "Unknown Step"

class AddConditionalRecordDialog(simpledialog.Dialog):
    """The pop-up window for adding or editing a conditional block."""
    def __init__(self, parent, title=None, init_data=None):
        self.init_data = init_data or { "cases": [], "else_steps": [] }
        # We create copies of the lists so that changes are only saved if the user clicks "OK".
        self.cases = [dict(c) for c in self.init_data.get("cases", [])]
        self.else_steps = list(self.init_data.get("else_steps", []))
        super().__init__(parent, title)

    def body(self, master):
        frm = ttk.Frame(master, padding=5)
        frm.pack(fill=tk.BOTH, expand=True)
        # ... (GUI for conditional logic, cases, and else steps) ...
        # (This is a complex dialog, but its structure is similar to the others)
        return self.case_list # Set initial focus
    
    # ... (Methods for adding, editing, deleting cases and steps) ...

    def apply(self):
        """Saves the configured cases and else_steps into the result dictionary."""
        self.result = {
            "type": "conditional_record",
            "source": "clipboard",
            "cases": self.cases,
            "else_steps": self.else_steps,
            "delay": float(self.init_data.get("delay", 0.1))
        }

# === LOOP FEATURE: The Dialog Window ===
# This entire class is new. It defines the pop-up window that appears when you
# click "Add Loop Block".
class AddLoopDialog(simpledialog.Dialog):
    """The pop-up window for creating and editing a loop block."""
    def __init__(self, parent, title=None, init_data=None):
        self.init_data = init_data or {}
        # We make a deep copy of the steps. This is important! It means if the user
        # clicks "Cancel", the changes they made to the steps inside the loop
        # are discarded.
        self.steps = [dict(s) for s in self.init_data.get("steps", [])]
        super().__init__(parent, title)

    def body(self, master):
        self.master = master # Save a reference to the master window.

        # --- Repeat Count Entry ---
        ttk.Label(master, text="Repeat Count:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.count_entry = ttk.Entry(master)
        self.count_entry.insert(0, str(self.init_data.get("count", 3))) # Default to 3 iterations.
        self.count_entry.grid(row=0, column=1, padx=5, pady=5)

        # --- Frame for the list of steps ---
        steps_frame = ttk.LabelFrame(master, text="Steps to Repeat", padding=10)
        steps_frame.grid(row=1, columnspan=2, padx=5, pady=5, sticky="nsew")

        self.steps_listbox = tk.Listbox(steps_frame, height=8, width=50)
        self.steps_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # A button to open the sub-workflow editor.
        edit_btn = ttk.Button(steps_frame, text="Edit Steps", command=self.edit_steps)
        edit_btn.pack(side=tk.RIGHT, anchor="n", padx=5)

        self.refresh_list()
        return self.count_entry

    def refresh_list(self):
        """Updates the listbox to show the current steps inside the loop."""
        self.steps_listbox.delete(0, tk.END)
        for step in self.steps:
            self.steps_listbox.insert(tk.END, get_step_display_text(step))
        if not self.steps:
            self.steps_listbox.insert(tk.END, "(No steps. Click Edit to add some)")

    def edit_steps(self):
        """
        This method opens the `SubWorkflowEditor` dialog.
        Crucially, it passes `self.steps` (the list of steps for this loop) to it.
        The editor will directly modify this list.
        """
        SubWorkflowEditor(self.master, "Edit Loop Steps", self.steps)
        self.refresh_list() # After the editor closes, refresh the list to show any changes.

    def apply(self):
        """Called when the user clicks 'OK'. Validates and saves the loop data."""
        try:
            count = int(self.count_entry.get())
            if count < 0:
                raise ValueError # Loops can't run a negative number of times.
            self.result = {
                "type": "loop",
                "count": count,
                "steps": self.steps, # The list of steps we've been editing.
                "delay": float(self.init_data.get("delay", 0.1))
            }
        except ValueError:
            messagebox.showerror("Error", "Invalid repeat count. Must be a positive integer.", parent=self.master)
            self.result = None
# === END LOOP FEATURE ===

class SubWorkflowEditor(simpledialog.Dialog):
    """
    A reusable dialog for editing a list of steps. This is used by both the
    Conditional Block and the new Loop Block. It's a "mini" version of the main app window.
    """
    def __init__(self, parent, title, steps_list):
        # IMPORTANT: `steps_list` is a direct reference to the list of steps from
        # the parent dialog (e.g., the loop's `self.steps`). Any changes made here
        # will directly affect the original list.
        self.steps = steps_list 
        super().__init__(parent, title)

    def body(self, master):
        self.master = master
        self.listbox = tk.Listbox(master, width=60, height=10)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=10)

        # --- Buttons for adding/editing steps ---
        btn_frame = ttk.Frame(master)
        btn_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5)
        ttk.Button(btn_frame, text="Add Mouse", command=lambda: self.add_step("mouse")).pack(fill=tk.X)
        ttk.Button(btn_frame, text="Add Keyboard", command=lambda: self.add_step("keyboard")).pack(fill=tk.X)
        ttk.Button(btn_frame, text="Add Image", command=lambda: self.add_step("image")).pack(fill=tk.X)
        ttk.Separator(btn_frame).pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="Edit", command=self.edit_step).pack(fill=tk.X)
        ttk.Button(btn_frame, text="Delete", command=self.delete_step).pack(fill=tk.X)

        self.refresh_list()
        return self.listbox

    def refresh_list(self):
        """Updates the listbox with the current steps."""
        self.listbox.delete(0, tk.END)
        for step in self.steps:
            self.listbox.insert(tk.END, get_step_display_text(step))

    def add_step(self, step_type):
        """Opens the appropriate dialog to add a new step."""
        dialog_map = {
            "mouse": AddMouseStepDialog, "keyboard": AddKeyboardStepDialog, "image": AddImageStepDialog
        }
        dialog_class = dialog_map.get(step_type)
        if dialog_class:
            # We create the dialog and check its `result` attribute after it closes.
            dialog = dialog_class(self.master, f"Add {step_type.title()} Step")
            if dialog.result:
                self.steps.append(dialog.result) # Add the new step to our list.
                self.refresh_list()

    def edit_step(self):
        """Opens the appropriate dialog to edit the selected step."""
        selection = self.listbox.curselection()
        if not selection: return
        idx = selection[0]
        step_to_edit = self.steps[idx]

        dialog_map = {
            "mouse": AddMouseStepDialog, "keyboard": AddKeyboardStepDialog, "image": AddImageStepDialog
        }
        dialog_class = dialog_map.get(step_to_edit['type'])
        if dialog_class:
            # We pass the existing step data (`step_to_edit`) to the dialog.
            dialog = dialog_class(self.master, f"Edit {step_to_edit['type'].title()} Step", step_to_edit)
            if dialog.result:
                self.steps[idx] = dialog.result # Replace the old step with the edited one.
                self.refresh_list()

    def delete_step(self):
        selection = self.listbox.curselection()
        if not selection: return
        del self.steps[selection[0]]
        self.refresh_list()

    def buttonbox(self):
        """Overrides the default "OK" and "Cancel" buttons to only show an "OK" button."""
        box = ttk.Frame(self)
        ttk.Button(box, text="OK", width=10, command=self.ok, default=tk.ACTIVE).pack(pady=5)
        self.bind("<Return>", self.ok) # Allow pressing Enter to close the dialog.
        box.pack()

# ------------------ Main Application Class ------------------
# This class brings everything together. It builds the main window and
# handles all the core application logic.

class AutomationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Automation Workflow")
        self.workflow = [] # This list holds all the steps of the current workflow.
        self.is_running = False # A flag to check if the automation is currently running.
        self.execution_thread = None

        main_frame = ttk.Frame(root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # The layout is a left frame for controls and a right frame for the workflow steps.
        control_frame = ttk.LabelFrame(main_frame, text="Controls", padding=10)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        steps_frame = ttk.LabelFrame(main_frame, text="Workflow Steps", padding=10)
        steps_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # --- Add Step Buttons ---
        ttk.Button(control_frame, text="Add Mouse Step", command=lambda: self.add_step("mouse")).pack(fill=tk.X, pady=2)
        ttk.Button(control_frame, text="Add Keyboard Step", command=lambda: self.add_step("keyboard")).pack(fill=tk.X, pady=2)
        ttk.Button(control_frame, text="Add Image Step", command=lambda: self.add_step("image")).pack(fill=tk.X, pady=2)
        ttk.Separator(control_frame).pack(fill=tk.X, pady=5)
        
        # === LOOP FEATURE: The Main Button ===
        # A new button is added to the control panel to create a loop.
        ttk.Button(control_frame, text="Add Loop Block", command=lambda: self.add_step("loop")).pack(fill=tk.X, pady=2)
        # === END LOOP FEATURE ===

        ttk.Button(control_frame, text="Add Conditional Step", command=lambda: self.add_step("conditional_record")).pack(fill=tk.X, pady=2)
        ttk.Separator(control_frame).pack(fill=tk.X, pady=5)

        # --- Edit/Delete Buttons ---
        ttk.Button(control_frame, text="Edit Step", command=self.edit_selected_step).pack(fill=tk.X, pady=2)
        ttk.Button(control_frame, text="Delete Step", command=self.delete_selected_step).pack(fill=tk.X, pady=2)

        # --- File Operations ---
        ttk.Separator(control_frame).pack(fill=tk.X, pady=5)
        ttk.Button(control_frame, text="Save Workflow", command=self.save_workflow).pack(fill=tk.X, pady=2)
        ttk.Button(control_frame, text="Load Workflow", command=self.load_workflow).pack(fill=tk.X, pady=2)

        # --- Execution Controls ---
        ttk.Separator(control_frame).pack(fill=tk.X, pady=5)
        self.run_button = ttk.Button(control_frame, text="Run Workflow", command=self.toggle_run)
        self.run_button.pack(fill=tk.X, pady=5)
        self.status_var = tk.StringVar(value="Status: Idle")
        ttk.Label(control_frame, textvariable=self.status_var, relief=tk.SUNKEN).pack(side=tk.BOTTOM, fill=tk.X, pady=(5,0))

        # --- Workflow Listbox ---
        self.steps_listbox = tk.Listbox(steps_frame, height=15, width=60)
        self.steps_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(steps_frame, command=self.steps_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.steps_listbox.config(yscrollcommand=scrollbar.set)
        self.steps_listbox.bind("<Double-1>", self.edit_selected_step) # Double-clicking a step edits it.

        # On Linux, show a warning about potential missing dependencies.
        if is_linux():
            self.root.after(500, warn_linux_requirements)

    def add_step(self, step_type):
        """Handles adding a new step of any type to the workflow."""
        dialog_map = {
            "mouse": AddMouseStepDialog, "keyboard": AddKeyboardStepDialog,
            "image": AddImageStepDialog, "conditional_record": AddConditionalRecordDialog,
            "loop": AddLoopDialog  # === LOOP FEATURE: Mapping the dialog class ===
        }
        dialog_class = dialog_map.get(step_type)
        if dialog_class:
            dialog = dialog_class(self.root, f"Add {step_type.replace('_', ' ').title()}")
            if dialog.result:
                self.workflow.append(dialog.result)
                self.refresh_steps_list()

    def edit_selected_step(self, event=None):
        """Handles editing the currently selected step in the listbox."""
        selection = self.steps_listbox.curselection()
        if not selection: return
        idx = selection[0]
        step_to_edit = self.workflow[idx]

        dialog_map = {
            "mouse": AddMouseStepDialog, "keyboard": AddKeyboardStepDialog,
            "image": AddImageStepDialog, "conditional_record": AddConditionalRecordDialog,
            "loop": AddLoopDialog  # === LOOP FEATURE: Mapping the dialog class for editing ===
        }
        dialog_class = dialog_map.get(step_to_edit['type'])
        if dialog_class:
            dialog = dialog_class(self.root, f"Edit {step_to_edit['type'].replace('_', ' ').title()}", step_to_edit)
            if dialog.result:
                self.workflow[idx] = dialog.result
                self.refresh_steps_list()

    def delete_selected_step(self):
        """Deletes the currently selected step from the workflow."""
        selection = self.steps_listbox.curselection()
        if not selection: return
        if messagebox.askyesno("Delete", "Are you sure you want to delete this step?"):
            del self.workflow[selection[0]]
            self.refresh_steps_list()

    def refresh_steps_list(self):
        """Clears and re-populates the listbox with the current workflow steps."""
        self.steps_listbox.delete(0, tk.END)
        for i, step in enumerate(self.workflow):
            display_text = f"{i+1}. {get_step_display_text(step)}"
            self.steps_listbox.insert(tk.END, display_text)

    def save_workflow(self):
        """Saves the current workflow to a JSON file."""
        fp = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if fp:
            with open(fp, "w") as f:
                json.dump(self.workflow, f, indent=4) # `indent=4` makes the JSON file human-readable.
            messagebox.showinfo("Success", "Workflow saved successfully.")

    def load_workflow(self):
        """Loads a workflow from a JSON file."""
        fp = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if fp:
            with open(fp, "r") as f:
                self.workflow = json.load(f)
            self.refresh_steps_list()

    def toggle_run(self):
        """Starts or stops the workflow execution."""
        if self.is_running:
            # If it's running, we stop it.
            self.is_running = False
            self.run_button.config(text="Run Workflow")
            self.status_var.set("Status: Stopping...")
        else:
            # If it's stopped, we start it.
            self.is_running = True
            self.run_button.config(text="Stop")
            # We run the workflow in a separate thread to prevent the GUI from freezing.
            self.execution_thread = threading.Thread(target=self.run_workflow_loop, daemon=True)
            self.execution_thread.start()

    def run_workflow_loop(self):
        """The main execution engine. It iterates through the workflow steps and executes them."""
        self.status_var.set("Status: Running...")
        pyautogui.FAILSAFE = True # A safety feature: moving the mouse to the top-left corner will stop pyautogui.

        pc = 0 # "Program Counter" - tracks the current step index.
        while self.is_running and pc < len(self.workflow):
            self.steps_listbox.selection_clear(0, tk.END)
            self.steps_listbox.selection_set(pc) # Highlight the currently executing step.

            step = self.workflow[pc]
            time.sleep(float(step.get("delay", 0))) # Wait for the step's specified delay.

            if not self.is_running: break # Check again if "Stop" was clicked during the delay.
            
            # --- The main execution dispatcher ---
            # It checks the 'type' of the step and calls the correct execution method.
            if step["type"] == "conditional_record":
                self.execute_conditional_record(step)
            
            # === LOOP FEATURE: Execution Logic ===
            # When the engine finds a "loop" step, it calls the new `execute_loop_block` method.
            elif step["type"] == "loop":
                self.execute_loop_block(step)
            # === END LOOP FEATURE ===
            
            else:
                # For simple steps like mouse and keyboard, it calls the generic `execute_step`.
                self.execute_step(step)

            pc += 1 # Move to the next step.
        
        # --- Clean up after the loop finishes ---
        if self.is_running:
            # If the loop finished naturally (wasn't stopped by the user).
            self.is_running = False
            self.run_button.config(text="Run Workflow")
            self.status_var.set("Status: Idle")

    def execute_step(self, step):
        """Executes a single, simple step (mouse, keyboard, or image)."""
        if not self.is_running: return # Safety check.
        
        if step["type"] == "mouse":
            pyautogui.moveTo(step.get('x', 0), step.get('y', 0), duration=0.2)
            if step["action"] == "Click":
                pyautogui.click()
            # ... (other mouse actions)
        
        elif step["type"] == "keyboard":
            if step["action"] == "Type Text":
                pyautogui.write(step["value"], interval=0.01) # Small interval between keys for reliability.
            elif step["action"] == "Press Key":
                pyautogui.press(step["value"])
            elif step["action"] == "Hotkey":
                keys = [k.strip() for k in step["value"].split('+')]
                pyautogui.hotkey(*keys)

        elif step["type"] == "image":
            try:
                # `confidence` helps find images that aren't a perfect pixel-for-pixel match.
                # Requires OpenCV to be installed: pip install opencv-python
                loc = pyautogui.locateCenterOnScreen(step['path'], confidence=0.8)
                if loc:
                    pyautogui.click(loc)
                else:
                    self.status_var.set(f"Status: Image not found '{os.path.basename(step['path'])}'")
                    self.is_running = False # Stop the workflow if an image can't be found.
            except Exception as e:
                self.status_var.set("Status: Image search error. Is OpenCV installed?")
                self.is_running = False
                
    def execute_conditional_record(self, step):
        """Executes a conditional block by checking the clipboard content."""
        if not self.is_running: return

        try:
            source_text = self.root.clipboard_get()
        except tk.TclError:
            source_text = ""

        matched = False
        for case in step.get("cases", []):
            if case.get("value", "") and case["value"] in source_text:
                # If a case matches, execute its sub-steps.
                for sub in case.get("steps", []):
                    if not self.is_running: return
                    time.sleep(float(sub.get("delay", 0)))
                    self.execute_step(sub)
                matched = True
                break # Stop checking other cases once one has matched.
        
        if not matched:
            # If no cases matched, execute the "else" steps.
            for sub in step.get("else_steps", []):
                if not self.is_running: return
                time.sleep(float(sub.get("delay", 0)))
                self.execute_step(sub)

    # === LOOP FEATURE: The Execution Method ===
    # This new method contains the logic for running a loop. It's called by the
    # main `run_workflow_loop` when it encounters a step of type "loop".
    def execute_loop_block(self, loop_step):
        """Executes the steps inside a loop block for the specified number of times."""
        count = loop_step.get("count", 0)
        steps_to_repeat = loop_step.get("steps", [])

        # The main `for` loop that handles the repetition.
        for i in range(count):
            if not self.is_running: return # Check if "Stop" was clicked between iterations.
            self.status_var.set(f"Status: Running Loop {i+1}/{count}")

            # This inner loop goes through each step inside the loop block.
            for sub_step in steps_to_repeat:
                if not self.is_running: return # Check if "Stop" was clicked between steps.
                
                # We execute the step just like in the main workflow engine.
                time.sleep(float(sub_step.get("delay", 0)))
                self.execute_step(sub_step)
    # === END LOOP FEATURE ===


# ================== Application Entry Point ==================
# This is standard Python practice. The code inside this `if` block will only
# run when the script is executed directly (not when it's imported as a module).
if __name__ == "__main__":
    root = tk.Tk() # Create the main application window.
    app = AutomationApp(root) # Create an instance of our main application class.
    root.mainloop() # Start the tkinter event loop, which listens for user actions.