#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

import sys
import time
import io
import traceback

def excepthook(excType, excValue, tracebackobj):
    """
    Global function to catch unhandled exceptions.
    
    @param excType exception type
    @param excValue exception value
    @param tracebackobj traceback object
    """
    separator = '-' * 80
    timeString = time.strftime("%Y-%m-%d_%H%M%S")
    logFile = "error_" +timeString + ".log"
    notice = \
        """An unhandled exception occurred. Please report the problem\n"""\
        """using the error reporting dialog or via email to <%s>.\n"""\
        """A log has been written to "%s".\n\nError information:\n""" % \
        ("bugs@gnusolar.org", logFile)
    versionInfo="0.0.1"
    
    
    tbinfofile = io.StringIO()
    traceback.print_tb(tracebackobj, None, tbinfofile)
    tbinfofile.seek(0)
    tbinfo = tbinfofile.read()
    errmsg = '%s: \n%s\n' % (str(excType), str(excValue))
    for key, value in excValue.__dict__.items():
        errmsg += str(key) + ":" + str(value) + "\n"
        
    sections = [separator, timeString, separator, errmsg, separator, tbinfo]
    msg = '\n'.join(sections)
    try:
        f = open(logFile, "w")
        f.write(msg)
        f.write(versionInfo)
        f.close()
    except IOError:
        pass
    msg2 = str(notice)+str(msg)+str(versionInfo)

    from PyQt5 import QtWidgets
    from PyQt5.QtWidgets import QMessageBox

    QtWidgets.QMessageBox.critical(None, 'Projects Unhandled Exception', msg2)
    exit(1)

sys.excepthook = excepthook


