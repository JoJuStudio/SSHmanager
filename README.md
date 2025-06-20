# SSH Manager

A simple graphical SSH connection manager built with PyQt5. This is a starting
implementation based on the project description in `goal.txt`.

## Features

- Sidebar showing folders and saved connections
- Tabbed area for launching terminals embedded via KDE Konsole
- Opens a local terminal tab at startup
- Dialog for adding new connections, including folder, SSH key, and optional initial command
- Context menu to edit or delete connections
- Connections saved to `~/.sshmanager/connections.json`
- `Ctrl+T` opens a new empty terminal tab
- Bitwarden integration loads connection configs from Bitwarden items stored in
  the `SSH` folder (requires the Bitwarden CLI)

## Requirements

- Python 3.10+
- PyQt5
- Qt5 development packages and `libkf5parts-dev` to build the Konsole wrapper

Install Python dependencies with:

```bash
pip install -r requirements.txt
```

## Running

```bash
python -m sshmanager.main
```

### Building the Konsole wrapper

After installing the Qt and KF5 development packages, run the provided setup
script to compile `libkonsole_embed.so` inside the `sshmanager` package:

```bash
./setup.sh
```

The script simply runs the `g++` command shown below. You only need to run it
once unless you modify `konsole_embed.cpp`.

```bash
g++ -fPIC -shared konsole_embed.cpp -o sshmanager/libkonsole_embed.so \
  -I/usr/include/x86_64-linux-gnu/qt5/QtWidgets \
  -I/usr/include/x86_64-linux-gnu/qt5/QtGui \
  -I/usr/include/x86_64-linux-gnu/qt5/QtCore \
  -I/usr/include/x86_64-linux-gnu/qt5 \
  -I/usr/include/KF5/KParts -I/usr/include/KF5 \
  -I/usr/include/KF5/KCoreAddons -I/usr/include/KF5/KXmlGui \
  -lKF5Parts -lKF5XmlGui -lKF5CoreAddons -lQt5Widgets -lQt5Gui -lQt5Core
```

This launches a window where you can add SSH connections. Double-click a
connection to open a terminal tab. Each tab embeds the Konsole KPart. The
application clears the terminal and sends the ``ssh`` command from Python,
rather than launching it inside the C++ helper.

### Bitwarden integration

The [Bitwarden CLI](https://bitwarden.com/help/cli/) must be installed and you
must be logged in (`bw login` and `bw unlock`). Connection information can be
stored inside Bitwarden items placed in a folder named `SSH`. The item's
**notes/description** field should contain JSON describing the connection, for
example:

```json
{
  "label": "Prod Server",
  "host": "server.example.com",
  "username": "alice",
  "port": 22,
  "key_path": "~/.ssh/id_rsa",
  "initial_cmd": "uptime"
}
```

When you enter the item name or ID in the connection dialog and click
**Fetch**, these fields will be populated from the stored JSON.
