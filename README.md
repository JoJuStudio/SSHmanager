# SSH Manager

A simple graphical SSH connection manager built with PyQt6. This is a starting
implementation based on the project description in `goal.txt`.

## Features

- Sidebar showing folders and saved connections
- Tabbed area for launching terminals
- Dialog for adding new connections
- Connections saved to `~/.sshmanager/connections.json`

## Requirements

- Python 3.10+
- PyQt6

Install dependencies with:

```bash
pip install -r requirements.txt
```

## Running

```bash
python -m sshmanager.main
```

This launches a window where you can add SSH connections. Double-click a
connection to open a terminal tab. The tab runs the system ``ssh`` command
through a simple embedded terminal widget.
