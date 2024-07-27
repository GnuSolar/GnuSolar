#!/bin/bash

pyuic5 Ui/MainWindow.ui -o Ui/MainWindow.py
pyuic5 Ui/Preferences.ui -o Ui/Preferences.py
pyuic5 Ui/GnuSolar.ui -o Ui/GnuSolar.py

pyuic5 Ui/Contact.ui -o Ui/Contact.py
pyuic5 Ui/PvProject.ui -o Ui/PvProject.py
pyuic5 Ui/Building.ui -o Ui/Building.py
