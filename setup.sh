#!/usr/bin/env bash
# Simple setup script to compile the Konsole wrapper library.
# Run this after installing the required Qt and KF5 development packages.
set -e

# Compile the helper library used to embed Konsole via KParts.

mkdir -p sshmanager
g++ -fPIC -shared konsole_embed.cpp -o sshmanager/libkonsole_embed.so \
  -I/usr/include/x86_64-linux-gnu/qt5/QtWidgets \
  -I/usr/include/x86_64-linux-gnu/qt5/QtGui \
  -I/usr/include/x86_64-linux-gnu/qt5/QtCore \
  -I/usr/include/x86_64-linux-gnu/qt5 \
  -I/usr/include/KF5/KParts -I/usr/include/KF5 \
  -I/usr/include/KF5/KCoreAddons -I/usr/include/KF5/KXmlGui \
  -lKF5Parts -lKF5XmlGui -lKF5CoreAddons -lQt5Widgets -lQt5Gui -lQt5Core

# Optional: install Python dependencies
# pip install -r requirements.txt
