Visual Workflow Automator

![alt text](https://img.shields.io/badge/python-3.11-blue.svg)
![alt text](https://img.shields.io/badge/License-MIT-yellow.svg)

A robust, cross-platform desktop application designed to empower users to automate repetitive GUI-based tasks through an intuitive, visual workflow editor. This tool bridges the gap between manual labor and complex scripting, offering a no-code solution for process automation.

Overview

The Visual Workflow Automator provides a powerful yet simple interface for building, editing, and executing sequences of user actions. By chaining together steps like mouse clicks, keyboard inputs, and image recognition, users can create sophisticated macros to handle tasks ranging from data entry to software testing. The architecture is modular, allowing for the easy addition of complex control flow structures like conditionals and loops.

Key Features

Visual Workflow Editor: Build and manage automation sequences with a clean, intuitive graphical user interface.

Rich Step Library: Automate any task with a comprehensive set of actions:

Mouse Control: Click, right-click, move, hold, and release.

Keyboard Control: Type text, press individual keys, and execute hotkeys.

Image Recognition: Locate and interact with on-screen elements, providing resilience against UI changes.

Complex Control Flow: Go beyond simple macros with advanced logic:

Conditional Branching (If/Else): Execute different steps based on the contents of the system clipboard.

Loops: Repeat a sequence of actions a specified number of times.

Workflow Management: Save and load automation scripts as human-readable JSON files, promoting reusability and version control.

Cross-Platform: Engineered to run seamlessly on Windows, macOS, and Linux.

Live Recording: Automatically generate workflows by recording live mouse and keyboard actions.

Tech Stack

Language: Python 3.11

GUI Framework: Tkinter

Core Automation Engine: PyAutoGUI

Image Recognition Engine: OpenCV

Event Listening (Recorder): pynput

Prerequisites

Python 3.11 is required. You can download it from python.org.

Important: During installation on Windows, ensure you check the box that says "Add python.exe to PATH".

Installation & Setup

Follow these steps to set up the project locally. It is strongly recommended to use a virtual environment to manage project dependencies.

1. Clone the Repository:

code
Bash
download
content_copy
expand_less
git clone https://github.com/your-username/visual-workflow-automator.git
cd visual-workflow-automator

2. Create and Activate a Virtual Environment:

On Windows:

code
Bash
download
content_copy
expand_less
python -m venv venv
.\venv\Scripts\activate

On macOS / Linux:

code
Bash
download
content_copy
expand_less
python3 -m venv venv
source venv/bin/activate

(Your terminal prompt should now be prefixed with (venv))

3. Install Dependencies:

A requirements.txt file is included to ensure consistent dependency versions.

code
Bash
download
content_copy
expand_less
pip install -r requirements.txt

Note: How to Create requirements.txt
If you don't have this file, you can generate it after installing the modules manually with this command:
pip freeze > requirements.txt

Platform-Specific Dependencies (Linux)

For users on Debian-based Linux distributions (Ubuntu, Mint), some system-level packages are required for the GUI and screenshot functionalities.

code
Bash
download
content_copy
expand_less
sudo apt-get update
sudo apt-get install python3-tk python3-dev scrot
Usage

Once all dependencies are installed, you can run the application with the following command:

code
Bash
download
content_copy
expand_less
python main.py

(It is recommended to rename your main script file to main.py or a similar standard name.)

The main application window will launch, and you can begin building your automation workflow.

How It Works

Launch the application.

Use the Control Panel on the left to add steps (Mouse, Keyboard, Image, Loop, etc.).

Each new step will open a dialog window to configure its specific parameters.

Your complete workflow will be displayed in the Workflow Steps panel on the right.

Use the Edit and Delete buttons to manage the selected step.

Save your workflow to a .json file for later use or Load an existing one.

Click Run Workflow to execute the automation. You can click Stop at any time to safely terminate the process.

Future Roadmap

Variable System: Introduce variables to store and pass data between steps (e.g., read text from a file, store it in a variable, and type it elsewhere).

Enhanced Wait Conditions: Implement a "Wait for Image" step that pauses the workflow until a specific UI element appears, improving reliability.

Integrated Error Handling: Allow users to define fallback actions if a step fails (e.g., if an image is not found).

License

This project is licensed under the MIT License. See the LICENSE file for details.
