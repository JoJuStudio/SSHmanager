#!/usr/bin/env bash
# Simple setup script to compile the Konsole wrapper library.
# Run this after installing the required Qt and KF5 development packages.
set -e

# Compile the helper library used to embed Konsole via KParts. The build now
# relies on `pkg-config` so it works across distributions (Debian, Fedora,
# etc.). Ensure the relevant `*-devel` packages are installed.

mkdir -p sshmanager
PKG_MODULES="Qt5Widgets Qt5Gui Qt5Core KF5Parts KF5XmlGui KF5CoreAddons"
g++ -fPIC -shared konsole_embed.cpp -o sshmanager/libkonsole_embed.so \
  $(pkg-config --cflags ${PKG_MODULES}) \
  $(pkg-config --libs ${PKG_MODULES})

# Optional: install Python dependencies
# pip install -r requirements.txt
