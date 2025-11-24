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
