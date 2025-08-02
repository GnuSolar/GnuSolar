#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import sys
import os
import subprocess

if sys.platform == 'darwin':
    def openFolder(path):
        os.system("open \"" + path + "\"")
elif sys.platform == 'win32':
    def openFolder(path):
        os.system("explorer \"" + path + "\"")
else:   # Default Linux
    def openFolder(path):
        os.system("xdg-open \"" + path + "\"")

def openFolderIfExists(path):
    if not path or not os.path.exists(path):
        return

    openFolder(path)
    
def composeEmail(from_adr, to, subject, body, attachments=[]):
    if not from_adr:
        from_adr = ""
    if not to:
        to = ""
    if not subject:
        subject = ""
    if not body:
        body = ""

    cmd = "thunderbird -compose \""
    cmd += "from='" + from_adr + "',"
    cmd += "to='" + to + "',"
    cmd += "subject='" + subject + "',"
    cmd += "body='" + body + "',"
    for att in attachments:
        cmd += "attachment='" + att + "',"
    cmd += "\""
    
    os.system(cmd)

# Place a phone call over SIP
def callSip(number, sipServer):
    global config
    if not number:
        print("empty number")
        return
    # fixup number
    number = number.replace(' ','')
    # build SIP URL
    sip = "sip:" + number + "@" + sipServer
    print("call: " + sip)
    openFolder(sip)


