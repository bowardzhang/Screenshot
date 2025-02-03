"""
Screenshot Tool with Customizable Area Selection and Options

Author: bowardzhang@gmail.com
Date: Feb 3rd, 2025

This Python script provides a robust tool for taking screenshots of customizable areas on the screen. 
It allows users to define a rectangular region, adjust its size and position, and configure various 
options such as capturing the mouse pointer, saving to clipboard or folder, and delaying the screenshot. 
The tool uses `tkinter` for GUI components, `pynput` for keyboard event handling, and `Pillow` for image 
processing. It supports multi-monitor setups and persists user preferences using a JSON configuration file.
"""

import tkinter as tk
from tkinter import filedialog, ttk
from screeninfo import get_monitors  # To detect monitor information
from pynput import keyboard  # For listening to keyboard events
import json  # For saving/loading configuration
import os  # For file path operations
from PIL import Image, ImageGrab  # For capturing screenshots
from datetime import datetime  # For generating timestamps
import win32api  # For getting mouse pointer position
import threading  # For delayed screenshot functionality
import time

# Global variables
root = tk.Tk()  # Root window (hidden)
overlay_window = None  # Overlay window for selecting the area
canvas = None  # Canvas for drawing the rectangle
canvas_offset_x = 0  # Offset for multi-monitor setups
rectangle = None  # The draggable and resizable rectangle
resize_handles = {}  # Handles for resizing the rectangle
drag_data = {"x": 0, "y": 0, "dragging": False, "resizing": None}  # Data for dragging/resizing
dialog = None  # Dialog window for options

# Default folder for saving screenshots (user's desktop)
screenshot_folder = os.path.join(os.path.expanduser("~"), "Desktop")

# JSON file for saving/loading configuration
CONFIG_FILE = "screenshot_config.json"

# Constants for rectangle and handle size
RECTANGLE_DEFAULT_WIDTH = 900  # Default width of the rectangle
RECTANGLE_DEFAULT_HEIGHT = 600  # Default height of the rectangle
RECTANGLE_DEFAULT_BORDER = 5  # Border thickness of the rectangle
HANDLE_SIZE = 10  # Size of resize handles
DIALOG_WIDTH = 490  # Width of the dialog window
DIALOG_HEIGHT = 170  # Height of the dialog window

# Load configuration from the JSON file
def load_config():
    """
    Load configuration from the JSON file.
    If the file doesn't exist or is invalid, return default values.
    """
    default_config = {
        "rectangle": {  # Rectangle position and size
            "x": 0,
            "y": 0,
            "width": 0,
            "height": 0
        },
        "dialog": {  # Dialog options
            "capture_pointer": False,  # Capture mouse pointer checkbox
            "save_clipboard": True,  # Save to clipboard checkbox
            "save_folder": False,  # Save to folder checkbox
            "folder_path": screenshot_folder,  # Folder path for saving screenshots
            "delay_screenshot": False  # Take screenshot after 5 seconds checkbox
        }
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
                return config
        except Exception as e:
            print(f"Error loading configuration: {e}")
    return default_config

# Save configuration to the JSON file
def save_config(config):
    """
    Save configuration to the JSON file.
    """
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)  # Save with indentation for readability
    except Exception as e:
        print(f"Error saving configuration: {e}")

# Load rectangle configuration from the JSON file
def load_rectangle_config():
    """
    Load rectangle position and size from the JSON file.
    """
    config = load_config()
    rect_config = config.get("rectangle", {})
    return (
        rect_config.get("x", 0),
        rect_config.get("y", 0),
        rect_config.get("width", RECTANGLE_DEFAULT_WIDTH),
        rect_config.get("height", RECTANGLE_DEFAULT_HEIGHT)
    )

# Save rectangle configuration to the JSON file
def save_rectangle_config(x, y, width, height):
    """
    Save rectangle position and size to the JSON file.
    """
    config = load_config()
    config["rectangle"] = {"x": x, "y": y, "width": width, "height": height}
    save_config(config)

# Create the overlay window for selecting the area
def create_overlay():
    """
    Create a semi-transparent overlay spanning all monitors with a draggable and resizable rectangle.
    """
    global root, overlay_window, canvas, canvas_offset_x, rectangle, resize_handles, RECTANGLE_DEFAULT_WIDTH, RECTANGLE_DEFAULT_HEIGHT

    # Get the current mouse position
    mouse_x, mouse_y = root.winfo_pointerxy()
    root.withdraw()  # Hide the root window

    destroy_overlay()  # Destroy any existing overlay

    # Get information about all monitors
    monitors = get_monitors()

    # Calculate the total virtual screen dimensions
    min_x = min(monitor.x for monitor in monitors)
    min_y = min(monitor.y for monitor in monitors)
    max_x = max(monitor.x + monitor.width for monitor in monitors)
    max_y = max(monitor.y + monitor.height for monitor in monitors)
    total_width = max_x - min_x
    total_height = max_y - min_y

    # Adjust for negative offsets in multi-monitor setups
    if min_x < 0:
        canvas_offset_x = -min_x

    # Create a single overlay window spanning all monitors
    overlay_window = tk.Toplevel()
    overlay_window.attributes("-alpha", 0.5)  # Semi-transparent (50% opacity)
    overlay_window.config(bg="white")  # White background
    overlay_window.geometry(f"{total_width}x{total_height}+{min_x}+{min_y}")
    overlay_window.overrideredirect(True)  # Remove window decorations
    overlay_window.update_idletasks()  # Ensure geometry is applied immediately

    # Add a canvas for drawing the rectangle
    canvas = tk.Canvas(overlay_window, bg="white", highlightthickness=0)
    canvas.pack(fill=tk.BOTH, expand=True)

    # Determine the monitor where the mouse pointer is located
    current_monitor = None
    for monitor in monitors:
        if monitor.x <= mouse_x < monitor.x + monitor.width and monitor.y <= mouse_y < monitor.y + monitor.height:
            current_monitor = monitor
            break

    if not current_monitor:
        current_monitor = monitors[0]  # Default to the first monitor if no match is found

    # Load rectangle position and size from the JSON file
    rect_x, rect_y, RECTANGLE_DEFAULT_WIDTH, RECTANGLE_DEFAULT_HEIGHT = load_rectangle_config()
    
    # Validate rectangle configuration
    if not (current_monitor.x <= rect_x - canvas_offset_x < current_monitor.x + current_monitor.width and
            current_monitor.y <= rect_y < current_monitor.y + current_monitor.height and
            current_monitor.x <= rect_x + RECTANGLE_DEFAULT_WIDTH - canvas_offset_x < current_monitor.x + current_monitor.width and
            current_monitor.y <= rect_y + RECTANGLE_DEFAULT_HEIGHT < current_monitor.y + current_monitor.height):
        # Reset the rectangle at the center of the current screen
        print("Reset the rectangle")
        RECTANGLE_DEFAULT_WIDTH = current_monitor.width // 2
        RECTANGLE_DEFAULT_HEIGHT = current_monitor.height // 2
        rect_x = current_monitor.x + (current_monitor.width // 2) - (RECTANGLE_DEFAULT_WIDTH // 2) + canvas_offset_x
        rect_y = current_monitor.y + (current_monitor.height // 2) - (RECTANGLE_DEFAULT_HEIGHT // 2)

    # Draw the rectangle
    rectangle = canvas.create_rectangle(
        rect_x, rect_y,
        rect_x + RECTANGLE_DEFAULT_WIDTH, rect_y + RECTANGLE_DEFAULT_HEIGHT,
        outline="black", width=RECTANGLE_DEFAULT_BORDER
    )

    # Add resize handles
    resize_handles["top_left"] = canvas.create_rectangle(
        rect_x - HANDLE_SIZE // 2, rect_y - HANDLE_SIZE // 2,
        rect_x + HANDLE_SIZE // 2, rect_y + HANDLE_SIZE // 2,
        fill="blue", outline="black"
    )
    resize_handles["top_right"] = canvas.create_rectangle(
        rect_x + RECTANGLE_DEFAULT_WIDTH - HANDLE_SIZE // 2, rect_y - HANDLE_SIZE // 2,
        rect_x + RECTANGLE_DEFAULT_WIDTH + HANDLE_SIZE // 2, rect_y + HANDLE_SIZE // 2,
        fill="blue", outline="black"
    )
    resize_handles["bottom_left"] = canvas.create_rectangle(
        rect_x - HANDLE_SIZE // 2, rect_y + RECTANGLE_DEFAULT_HEIGHT - HANDLE_SIZE // 2,
        rect_x + HANDLE_SIZE // 2, rect_y + RECTANGLE_DEFAULT_HEIGHT + HANDLE_SIZE // 2,
        fill="blue", outline="black"
    )
    resize_handles["bottom_right"] = canvas.create_rectangle(
        rect_x + RECTANGLE_DEFAULT_WIDTH - HANDLE_SIZE // 2, rect_y + RECTANGLE_DEFAULT_HEIGHT - HANDLE_SIZE // 2,
        rect_x + RECTANGLE_DEFAULT_WIDTH + HANDLE_SIZE // 2, rect_y + RECTANGLE_DEFAULT_HEIGHT + HANDLE_SIZE // 2,
        fill="blue", outline="black"
    )
    resize_handles["top_mid"] = canvas.create_rectangle(
        rect_x + RECTANGLE_DEFAULT_WIDTH // 2 - HANDLE_SIZE // 2, rect_y - HANDLE_SIZE // 2,
        rect_x + RECTANGLE_DEFAULT_WIDTH // 2 + HANDLE_SIZE // 2, rect_y + HANDLE_SIZE // 2,
        fill="blue", outline="black"
    )
    resize_handles["bottom_mid"] = canvas.create_rectangle(
        rect_x + RECTANGLE_DEFAULT_WIDTH // 2 - HANDLE_SIZE // 2, rect_y + RECTANGLE_DEFAULT_HEIGHT - HANDLE_SIZE // 2,
        rect_x + RECTANGLE_DEFAULT_WIDTH // 2 + HANDLE_SIZE // 2, rect_y + RECTANGLE_DEFAULT_HEIGHT + HANDLE_SIZE // 2,
        fill="blue", outline="black"
    )
    resize_handles["left_mid"] = canvas.create_rectangle(
        rect_x - HANDLE_SIZE // 2, rect_y + RECTANGLE_DEFAULT_HEIGHT // 2 - HANDLE_SIZE // 2,
        rect_x + HANDLE_SIZE // 2, rect_y + RECTANGLE_DEFAULT_HEIGHT // 2 + HANDLE_SIZE // 2,
        fill="blue", outline="black"
    )
    resize_handles["right_mid"] = canvas.create_rectangle(
        rect_x + RECTANGLE_DEFAULT_WIDTH - HANDLE_SIZE // 2, rect_y + RECTANGLE_DEFAULT_HEIGHT // 2 - HANDLE_SIZE // 2,
        rect_x + RECTANGLE_DEFAULT_WIDTH + HANDLE_SIZE // 2, rect_y + RECTANGLE_DEFAULT_HEIGHT // 2 + HANDLE_SIZE // 2,
        fill="blue", outline="black"
    )

    # Bind events for dragging and resizing
    bind_rectangle_events(canvas, rectangle, resize_handles)

    # Position the dialog window relative to the rectangle
    dialog_x = rect_x - (current_monitor.width // 2) - 100
    dialog_y = rect_y + 20 + RECTANGLE_DEFAULT_HEIGHT
    if dialog_x + DIALOG_WIDTH > current_monitor.x + current_monitor.width:
        dialog_x = current_monitor.x + current_monitor.width - DIALOG_WIDTH
    if dialog_y + DIALOG_HEIGHT > current_monitor.y + current_monitor.height:
        dialog_y = current_monitor.y + current_monitor.height - DIALOG_HEIGHT
    show_dialog(dialog_x, dialog_y)

def bind_rectangle_events(canvas, rectangle, handles):
    """
    Bind events for dragging and resizing the rectangle.
    """

    def start_drag(event):
        """Start dragging or resizing."""
        x, y = event.x, event.y
        rect_coords = canvas.coords(rectangle)
        handle_coords = {handle: canvas.coords(handles[handle]) for handle in handles}

        # Check if resizing
        for handle, coords in handle_coords.items():
            if coords[0] <= x <= coords[2] and coords[1] <= y <= coords[3]:
                drag_data["resizing"] = handle
                break
        else:
            # Not resizing, start dragging
            drag_data["dragging"] = True
            drag_data["x"] = x - rect_coords[0]
            drag_data["y"] = y - rect_coords[1]

    def drag(event):
        """Drag or resize the rectangle."""
        x, y = event.x, event.y
        rect_coords = canvas.coords(rectangle)

        if drag_data["dragging"]:
            # Move the rectangle
            new_x = x - drag_data["x"]
            new_y = y - drag_data["y"]
            new_x2 = new_x + (rect_coords[2] - rect_coords[0])
            new_y2 = new_y + (rect_coords[3] - rect_coords[1])
            canvas.coords(rectangle, new_x, new_y, new_x2, new_y2)
            update_resize_handles(canvas, rectangle, handles)
        elif drag_data["resizing"]:
            # Resize the rectangle
            if drag_data["resizing"] == "top_left":
                canvas.coords(rectangle, x, y, rect_coords[2], rect_coords[3])
            elif drag_data["resizing"] == "top_right":
                canvas.coords(rectangle, rect_coords[0], y, x, rect_coords[3])
            elif drag_data["resizing"] == "bottom_left":
                canvas.coords(rectangle, x, rect_coords[1], rect_coords[2], y)
            elif drag_data["resizing"] == "bottom_right":
                canvas.coords(rectangle, rect_coords[0], rect_coords[1], x, y)
            elif drag_data["resizing"] == "top_mid":
                canvas.coords(rectangle, rect_coords[0], y, rect_coords[2], rect_coords[3])
            elif drag_data["resizing"] == "bottom_mid":
                canvas.coords(rectangle, rect_coords[0], rect_coords[1], rect_coords[2], y)
            elif drag_data["resizing"] == "left_mid":
                canvas.coords(rectangle, x, rect_coords[1], rect_coords[2], rect_coords[3])
            elif drag_data["resizing"] == "right_mid":
                canvas.coords(rectangle, rect_coords[0], rect_coords[1], x, rect_coords[3])
            update_resize_handles(canvas, rectangle, handles)

    def stop_drag(event):
        """Stop dragging or resizing."""
        drag_data["dragging"] = False
        drag_data["resizing"] = None

    # Bind events
    canvas.tag_bind(rectangle, "<ButtonPress-1>", start_drag)
    canvas.tag_bind(rectangle, "<B1-Motion>", drag)
    canvas.tag_bind(rectangle, "<ButtonRelease-1>", stop_drag)
    for handle in handles.values():
        canvas.tag_bind(handle, "<ButtonPress-1>", start_drag)
        canvas.tag_bind(handle, "<B1-Motion>", drag)
        canvas.tag_bind(handle, "<ButtonRelease-1>", stop_drag)

def update_resize_handles(canvas, rectangle, handles):
    """
    Update the position of resize handles based on the rectangle's position.
    """
    rect_coords = canvas.coords(rectangle)
    canvas.coords(handles["top_left"], rect_coords[0] - HANDLE_SIZE // 2, rect_coords[1] - HANDLE_SIZE // 2,
                  rect_coords[0] + HANDLE_SIZE // 2, rect_coords[1] + HANDLE_SIZE // 2)
    canvas.coords(handles["top_right"], rect_coords[2] - HANDLE_SIZE // 2, rect_coords[1] - HANDLE_SIZE // 2,
                  rect_coords[2] + HANDLE_SIZE // 2, rect_coords[1] + HANDLE_SIZE // 2)
    canvas.coords(handles["bottom_left"], rect_coords[0] - HANDLE_SIZE // 2, rect_coords[3] - HANDLE_SIZE // 2,
                  rect_coords[0] + HANDLE_SIZE // 2, rect_coords[3] + HANDLE_SIZE // 2)
    canvas.coords(handles["bottom_right"], rect_coords[2] - HANDLE_SIZE // 2, rect_coords[3] - HANDLE_SIZE // 2,
                  rect_coords[2] + HANDLE_SIZE // 2, rect_coords[3] + HANDLE_SIZE // 2)
    canvas.coords(handles["top_mid"], rect_coords[0] + (rect_coords[2] - rect_coords[0]) // 2 - HANDLE_SIZE // 2,
                  rect_coords[1] - HANDLE_SIZE // 2,
                  rect_coords[0] + (rect_coords[2] - rect_coords[0]) // 2 + HANDLE_SIZE // 2,
                  rect_coords[1] + HANDLE_SIZE // 2)
    canvas.coords(handles["bottom_mid"], rect_coords[0] + (rect_coords[2] - rect_coords[0]) // 2 - HANDLE_SIZE // 2,
                  rect_coords[3] - HANDLE_SIZE // 2,
                  rect_coords[0] + (rect_coords[2] - rect_coords[0]) // 2 + HANDLE_SIZE // 2,
                  rect_coords[3] + HANDLE_SIZE // 2)
    canvas.coords(handles["left_mid"], rect_coords[0] - HANDLE_SIZE // 2,
                  rect_coords[1] + (rect_coords[3] - rect_coords[1]) // 2 - HANDLE_SIZE // 2,
                  rect_coords[0] + HANDLE_SIZE // 2,
                  rect_coords[1] + (rect_coords[3] - rect_coords[1]) // 2 + HANDLE_SIZE // 2)
    canvas.coords(handles["right_mid"], rect_coords[2] - HANDLE_SIZE // 2,
                  rect_coords[1] + (rect_coords[3] - rect_coords[1]) // 2 - HANDLE_SIZE // 2,
                  rect_coords[2] + HANDLE_SIZE // 2,
                  rect_coords[1] + (rect_coords[3] - rect_coords[1]) // 2 + HANDLE_SIZE // 2)

# Show the dialog window with options
def show_dialog(x, y):
    """
    Show a dialog with 'Save' and 'Cancel' buttons.
    """
    global dialog
    dialog = tk.Toplevel()
    dialog.overrideredirect(True)  # Remove title bar
    dialog.attributes("-topmost", True)  # Keep the dialog on top
    dialog.geometry('%dx%d+%d+%d' % (DIALOG_WIDTH, DIALOG_HEIGHT, x, y))

    # Add a custom title bar
    title_bar = tk.Frame(dialog, bg="lightgray", relief="raised", bd=1)
    title_bar.pack(fill="x")
    title_label = tk.Label(title_bar, text="Take Screenshot", bg="lightgray")
    title_label.pack(side="left", padx=5)

    # Custom drag functionality
    def start_drag(event):
        dialog._drag_data = {"x": event.x_root - dialog.winfo_x(), "y": event.y_root - dialog.winfo_y()}

    def drag(event):
        new_x = event.x_root - dialog._drag_data["x"]
        new_y = event.y_root - dialog._drag_data["y"]
        dialog.geometry(f"+{new_x}+{new_y}")

    def stop_drag(event):
        dialog._drag_data = None

    # Bind mouse events for dragging
    dialog.bind("<ButtonPress-1>", start_drag)  # Start dragging on left mouse button press
    dialog.bind("<B1-Motion>", drag)           # Drag the window while holding the left mouse button
    dialog.bind("<ButtonRelease-1>", stop_drag)  # Stop dragging on left mouse button release
    
    # Load configuration
    config = load_config()
    dialog_config = config.get("dialog", {})

    # Left frame for checkboxes
    left_frame = tk.Frame(dialog)
    left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

    # Right frame for buttons and folder selection
    right_frame = tk.Frame(dialog)
    right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)

    # Checkbox: Capture mouse pointer
    capture_pointer_var = tk.BooleanVar(value=dialog_config.get("capture_pointer", False))
    chk_capture_pointer = ttk.Checkbutton(left_frame, text="Capture mouse pointer", variable=capture_pointer_var)
    chk_capture_pointer.pack(anchor="w", pady=5)

    # Checkbox: Save to clipboard
    save_clipboard_var = tk.BooleanVar(value=dialog_config.get("save_clipboard", True))
    chk_save_clipboard = ttk.Checkbutton(left_frame, text="Save to clipboard", variable=save_clipboard_var)
    chk_save_clipboard.pack(anchor="w", pady=5)

    # Checkbox: Save to folder
    save_folder_var = tk.BooleanVar(value=dialog_config.get("save_folder", False))
    chk_save_folder = ttk.Checkbutton(left_frame, text="Save to folder", variable=save_folder_var)
    chk_save_folder.pack(anchor="w", pady=5)

    # Checkbox: Take screenshot after 5 seconds
    delay_screenshot_var = tk.BooleanVar(value=dialog_config.get("delay_screenshot", False))
    chk_delay_screenshot = ttk.Checkbutton(left_frame, text="Take screenshot after 5 seconds", variable=delay_screenshot_var)
    chk_delay_screenshot.pack(anchor="w", pady=5)

    # Folder selection field (hidden by default)
    folder_frame = tk.Frame(right_frame)
    folder_path_var = tk.StringVar(value=dialog_config.get("folder_path", screenshot_folder))
    folder_entry = tk.Entry(folder_frame, textvariable=folder_path_var, width=30)
    folder_button = tk.Button(folder_frame, text="Browse...", command=lambda: browse_folder(folder_path_var))
    
    def browse_folder(folder_path_var):
        """Open a folder selection dialog and update the folder path."""
        folder_selected = filedialog.askdirectory(initialdir=folder_path_var.get())
        if folder_selected:
            folder_path_var.set(folder_selected)

    def toggle_folder_field(*args):
        """Show or hide the folder selection field based on the 'Save to folder' checkbox."""
        if save_folder_var.get():
            folder_frame.pack(fill="x", pady=5)
        else:
            folder_frame.pack_forget()
    
    # Bind the toggle function to changes in the checkbox
    save_folder_var.trace_add("write", toggle_folder_field)
    
    def on_save(event=None):
        """
        Save configuration and take the screenshot.
        """
        # Get rectangle coordinates
        rect_coords = canvas.coords(rectangle)

        # Update configuration
        new_config = {
            "rectangle": {
                "x": int(rect_coords[0]),
                "y": int(rect_coords[1]),
                "width": int(rect_coords[2] - rect_coords[0]),
                "height": int(rect_coords[3] - rect_coords[1])
            },
            "dialog": {
                "capture_pointer": capture_pointer_var.get(),
                "save_clipboard": save_clipboard_var.get(),
                "save_folder": save_folder_var.get(),
                "folder_path": folder_path_var.get(),
                "delay_screenshot": delay_screenshot_var.get()
            }
        }
        save_config(new_config)

        # Function to take the screenshot
        def take_screenshot():
            screenshot = capture_screenshot(rect_coords, capture_pointer=capture_pointer_var.get())
            save_screenshot(screenshot, save_clipboard=save_clipboard_var.get(), save_file=save_folder_var.get(), folder=folder_path_var.get())
            destroy_overlay()
            dialog.destroy()
            #root.quit()

        # Delay the screenshot if requested
        if delay_screenshot_var.get():
            threading.Timer(5, take_screenshot).start()
        else:
            take_screenshot()

    def on_cancel():
        """
        Cancel the operation and exit.
        """
        destroy_overlay()
        dialog.destroy()
        #root.quit()
        
    # Buttons: Save and Cancel
    btn_save = tk.Button(right_frame, text="Save", command=on_save)
    btn_save.pack(fill="x", padx=100, pady=5)

    btn_cancel = tk.Button(right_frame, text="Cancel", command=on_cancel)
    btn_cancel.pack(fill="x", padx=100, pady=5)
    
    folder_entry.pack(side=tk.LEFT, fill="x", expand=True)
    folder_button.pack(side=tk.RIGHT)
    
    # Explicitly call toggle_folder_field to set the initial visibility of the folder field
    toggle_folder_field()
    
    # Bind Enter key to the Save button
    dialog.bind("<Return>", on_save)
    btn_save.focus_set()
    dialog.update_idletasks()

# Capture the screenshot
def capture_screenshot(rect, capture_pointer=False):
    """
    Capture a screenshot of the specified rectangular area or the entire screen.
    Temporarily hides the overlay window to avoid interference.
    """
    global overlay_window, dialog

    # Hide the overlay and dialog windows
    if overlay_window:
        overlay_window.withdraw()
        overlay_window.update_idletasks()
    if dialog:
        dialog.withdraw()
        dialog.update_idletasks()

    # Capture the screenshot
    if rect:
        x1, y1, x2, y2 = map(int, rect)  # Convert to integers
        x1, x2 = (x1 - canvas_offset_x, x2 - canvas_offset_x)  # Adjust for multi-monitor setups
        screenshot = ImageGrab.grab(bbox=(x1, y1, x2, y2), all_screens=True)

        # Capture mouse pointer if requested
        if capture_pointer:
            mouse_x, mouse_y = win32api.GetCursorPos()
            if x1 < mouse_x < x2 and y1 < mouse_y < y2:
                draw_mouse_pointer(screenshot, mouse_x - x1, mouse_y - y1)
    else:
        screenshot = ImageGrab.grab(bbox=None, all_screens=True)

    return screenshot

# Save the screenshot
def save_screenshot(screenshot, save_clipboard=True, save_file=False, folder=None):
    """
    Save the screenshot to the clipboard and/or a file.
    """
    if save_clipboard:
        from io import BytesIO
        output = BytesIO()
        screenshot.convert("RGB").save(output, "BMP")
        data = output.getvalue()[14:]  # Remove BMP header
        output.close()

        import win32clipboard
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
        win32clipboard.CloseClipboard()
        print(f"Screenshot saved to clipboard")

    if save_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"
        file_path = os.path.join(folder, filename)
        screenshot.save(file_path)
        print(f"Screenshot saved to {file_path}")

# Draw the mouse pointer on the screenshot
def draw_mouse_pointer(image, x, y):
    """
    Draw a red arrow pointing towards the top-left direction at the specified (x, y) position.
    """
    from PIL import ImageDraw, Image
    import math

    draw = ImageDraw.Draw(image)
    arrow_length = 30  # Length of the main arrow line
    arrowhead_angle = 40  # Angle of the arrowhead lines relative to the main line (in degrees)
    arrowhead_length = 15  # Length of the arrowhead lines

    # Calculate the end point of the main line (45 degrees from bottom-right to top-left)
    main_line_end_x = x - arrow_length * math.cos(math.radians(45))
    main_line_end_y = y - arrow_length * math.sin(math.radians(45))
    main_line_end = (main_line_end_x, main_line_end_y)

    # Calculate the end points of the arrowhead lines
    left_arrowhead_end_x = main_line_end_x + arrowhead_length * math.cos(math.radians(45 - arrowhead_angle))
    left_arrowhead_end_y = main_line_end_y + arrowhead_length * math.sin(math.radians(45 - arrowhead_angle))
    left_arrowhead_end = (left_arrowhead_end_x, left_arrowhead_end_y)

    right_arrowhead_end_x = main_line_end_x + arrowhead_length * math.cos(math.radians(45 + arrowhead_angle))
    right_arrowhead_end_y = main_line_end_y + arrowhead_length * math.sin(math.radians(45 + arrowhead_angle))
    right_arrowhead_end = (right_arrowhead_end_x, right_arrowhead_end_y)

    # Draw the three lines forming the arrow
    draw.line([(x, y), main_line_end], fill="red", width=4)  # Main line
    draw.line([main_line_end, left_arrowhead_end], fill="red", width=4)  # Left arrowhead line
    draw.line([main_line_end, right_arrowhead_end], fill="red", width=4)  # Right arrowhead line

# Destroy the overlay window
def destroy_overlay():
    """
    Destroy the overlay window.
    """
    global overlay_window, canvas, rectangle, resize_handles
    if overlay_window:
        try:
            overlay_window.destroy()
        except tk.TclError:
            pass
    overlay_window = None
    canvas = None
    rectangle = None
    resize_handles.clear()

listener = None
# Define the win32_event_filter callback function
def win32_event_filter(msg, data):
    # Check if the event is a key down event (WM_KEYDOWN or WM_SYSKEYDOWN)
    if msg in (0x0100, 0x0104):  # WM_KEYDOWN = 0x0100, WM_SYSKEYDOWN = 0x0104
        # Check if the virtual key code corresponds to the Print Screen key (VK_SNAPSHOT = 0x2C)
        if data.vkCode == 0x2C:  # VK_SNAPSHOT is the virtual key code for Print Screen
            create_overlay()
            listener.suppress_event()
            return False  # Suppress the Print Screen key by returning False
    
    # Allow all other keys to be processed normally
    return True
    
# Handle key press events
def on_press(key):
    """
    Handle key press events.
    Exit the program if the 'Esc' key is pressed.
    """
    try:
        if key == keyboard.Key.esc:
            destroy_overlay()
            global dialog
            if dialog:
                dialog.destroy()
    except Exception as e:
        print(f"Error: {e}")
        root.quit()
        
# Start listening for keyboard events
def start_keyboard_listener():
    """
    Start listening for keyboard events.
    """
    global listener
    listener = keyboard.Listener(on_press=on_press, win32_event_filter=win32_event_filter)
    listener.start()
    
# Main function
def main():
    """
    Main function to create and manage overlays.
    """
    try:
        print("Waiting for hotkey press to start the screenshot process...")
        start_keyboard_listener()
        root.withdraw()  # Hide the root window
        root.mainloop()  # Keep the root window alive to listen for events
    except KeyboardInterrupt:
        print("\nExiting...")
        destroy_overlay()
        root.quit()

if __name__ == "__main__":
    main()