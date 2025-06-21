# SSH Manager

A simple graphical SSH connection manager built with PyQt5. Connections are
loaded directly from Bitwarden and no data is stored locally.

## Features

- Sidebar showing folders and saved connections
- Tabbed area for launching terminals embedded via KDE Konsole
- Opens a local terminal tab at startup
- `Ctrl+T` opens a new empty terminal tab
- Bitwarden integration loads connection configs from items stored in
  the `SSH` folder via the Bitwarden CLI
- No local configuration file is written

## Requirements

- Python 3.10+
- PyQt5
- argon2-cffi
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

This launches a window listing the connections found in Bitwarden. Double-click
a connection to open a terminal tab. Each tab embeds the Konsole KPart. The
application clears the terminal and sends the ``ssh`` command from Python,
rather than launching it inside the C++ helper.

### Bitwarden integration

Click the **Login** button and enter your Bitwarden email address and master
password. An optional server URL can be provided if you're using a self-hosted
Vaultwarden instance. The application interacts with the ``bw`` command line
tool to retrieve items. Once authenticated, connections are loaded from items
placed in a folder named `SSH`. Only the item's login **username** and **URI**
fields are used.

The application does not store your Bitwarden session. Only the email and
server address are saved using the system keyring so the login dialog can be
pre-filled on the next launch. The underlying ``bw`` CLI configuration is kept
separate, so existing command line logins are unaffected.
If a ``BW_SESSION`` environment variable is set from another ``bw``
session, it is cleared during login so the application remains fully
independent of any terminal usage.

Each item name becomes the connection label. Only the URL and username are
stored, and the default SSH port 22 is used.
