# Visual Workflow Automator
![Python](https://img.shields.io/badge/python-3.11-blue.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

A clean, cross-platform desktop application built to automate repetitive GUI tasks visually.  
No code required. Build workflows, configure steps, and run them directly.

---

## Overview
This tool provides a visual editor for creating automation workflows.  
You can combine mouse actions, keyboard inputs, image detection, loops, and conditionals to automate almost any GUI-based process.

Workflows are stored as JSON files, making them easy to version, share, and reuse.

---

## Features

### Visual Workflow Editor
Create automations through an intuitive interface. Add steps, configure them, and execute them.

### Mouse and Keyboard Actions
- Click, move, hold, release  
- Type text  
- Press keys and hotkeys  

### Image Recognition
Locate and interact with UI elements based on screenshots using OpenCV.

### Logic Components
- Conditional branching (If / Else)  
- Loops with configurable counts  

### Workflow Management
- Save and load workflows in JSON format  
- Human-readable and editable  

### Live Recording
Automatically capture mouse and keyboard actions and convert them into workflow steps.

### Cross-Platform Support
Runs on Windows, macOS, and Linux.

---

## Tech Stack
- Python 3.11  
- Tkinter (GUI)  
- PyAutoGUI (automation engine)  
- OpenCV (image detection)  
- pynput (event listening / recorder)

---

## Prerequisites
- Python 3.11  
- On Windows, ensure the option "Add python.exe to PATH" is enabled during installation.

---

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/visual-workflow-automator.git
cd visual-workflow-automator
```
2. Create and Activate a Virtual Environment
On Windows:
code
```bash
python -m venv venv
.\venv\Scripts\activate
```
On macOS / Linux:
code
```bash
python3 -m venv venv
source venv/bin/activate
(Your terminal prompt should now be prefixed with (venv))
```
3. Install Dependencies
A requirements.txt file is included for easy installation of all necessary libraries.
code
```bash
pip install -r requirements.txt
(Note: To generate this file if it's missing, run: pip freeze > requirements.txt after installing the modules manually.)
```
4. System-Specific Dependencies (Linux Only)
For users on Debian-based Linux distributions (Ubuntu, Mint), some system-level packages are required for the GUI and screenshot functionalities.
code
```bash
sudo apt-get update
sudo apt-get install python3-tk python3-dev scrot
```
# How to Run
Once all dependencies are installed, you can launch the application with the following command:
code
```bash
python main.py```
*(It is recommended to rename your main script file to `main.py`)*

---
```
##  Future Roadmap

*   **Variable System:** Introduce variables to store and pass data between steps (e.g., read text from a file, store it in a variable, and type it elsewhere).
*   **Enhanced Wait Conditions:** Implement a "Wait for Image" step that pauses the workflow until a specific UI element appears, improving reliability.
*   **Integrated Error Handling:** Allow users to define fallback actions if a step fails (e.g., if an image is not found).

##  License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
