# screenshot
This Python script provides a robust tool for taking screenshots of customizable areas on the screen. 

## Overview
This Python script is a versatile screenshot tool designed to provide users with fine-grained control over the screenshot process. Unlike standard screenshot utilities, this tool allows you to:

 1. Select and Customize a Screenshot Area:
	  - Use a draggable and resizable rectangle overlay to define the exact area of the screen you want to capture.
	  - The rectangle can be adjusted dynamically using resize handles located at all edges and corners.
 2. Configure Screenshot Options:
	- Capture the mouse pointer and include it in the screenshot.
	- Save the screenshot to the clipboard for quick pasting into other 	- 	- applications.
	- Save the screenshot directly to a specified folder with a timestamped filename.
	- Delay the screenshot by 5 seconds to allow time for setup.
 3. Multi-Monitor Support:
	- The tool works seamlessly across multiple monitors, adjusting for negative offsets and spanning all connected displays.
 4. Persistent Configuration:
	- User preferences, including the last-used rectangle position and size, are saved to a JSON file. This ensures that your settings persist across sessions.
 5. Keyboard Shortcut Integration:
The Print Screen key (PrtScn) is intercepted and suppressed to trigger the screenshot process. Other keys remain unaffected.

## Key Features

 - Interactive Overlay:
	 - A semi-transparent overlay window appears when the Print Screen key
   is pressed. Users can drag and resize the rectangle to select the
   desired area. 
 - Customizable Dialog: 
	 - A dialog window provides checkboxes and options for configuring the screenshot behavior. For example, you can toggle whether to save the screenshot to the clipboard or a folder. 
 - Delayed Screenshots:
	 - If needed, users can delay the screenshot by 5 seconds to prepare the screen before capturing.
 - Mouse Pointer Capture:
	 - The mouse pointer is captured as a red arrow pointing towards the top-left direction, making it easy to highlight interactions in the screenshot.
 - Cross-Platform Compatibility (Windows):
	 - While the script is primarily designed for Windows, it leverages libraries like pynput and screeninfo to ensure compatibility with modern multi-monitor setups.

## How It Works

 1. Triggering the Tool:
	 - Press the Print Screen key (PrtScn) to activate the overlay. The tool suppresses the default behavior of the key to prevent unwanted system screenshots.
2. Defining the Area:
	 - Drag the rectangle to position it and use the resize handles to adjust its size. The tool automatically adjusts for multi-monitor setups.
3. Configuring Options:
	 - A dialog window appears near the rectangle, allowing you to configure options such as capturing the mouse pointer, saving to clipboard or folder, and delaying the screenshot.
4. Taking the Screenshot:
	 - Click the "Save" button in the dialog to capture the screenshot. The tool hides itself during the capture to avoid interference.
5. Saving the Screenshot:
	 - Depending on your configuration, the screenshot is saved to the clipboard, a folder, or both. Timestamped filenames ensure that screenshots are uniquely identifiable.

## Dependencies
The script relies on the following Python libraries:

 - `tkinter`: For creating the GUI components (overlay, dialog, etc.).
 - `pynput`: For listening to keyboard events and suppressing the Print Screen key.
 - `Pillow`: For capturing and processing screenshots.
 - `screeninfo`: For detecting monitor information and handling multi-monitor setups.
 - `win32api`: For capturing the mouse pointer position.
 - `json`: For saving and loading user preferences.
 -  `threading`: For implementing delayed screenshots.

You can install the required dependencies using pip:

    pip install pynput pillow screeninfo pywin32

## Usage Instructions
1. Clone the repository and navigate to the project directory.
2. Run the script using Python:
python screenshot_tool.py
3. Press the Print Screen key (PrtScn) to activate the overlay.
4. Adjust the rectangle and configure options in the dialog window.
5. Click "Save" to capture the screenshot or "Cancel" to exit without capturing.

## Future Enhancements
- Hotkey Customization:
	- Allow users to define custom hotkeys for triggering the screenshot process.
- Additional Annotation Tools:
	- Add features for drawing shapes, adding text, or highlighting areas directly on the screenshot.
- Cross-Platform Support:
	- Extend the tool to work on macOS and Linux with appropriate adjustments for platform-specific behaviors.
- Improved UI/UX:
	- Refine the dialog and overlay design for a more polished user experience.

## Contributing
Contributions are welcome! If you have ideas for improvements or encounter any issues, feel free to open an issue or submit a pull request. Make sure to follow the existing coding style and include tests for new features.

### License
This project is licensed under the MIT License. See the LICENSE file for details.
