#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# Documents from OpenDocument templates (relatorio): quote, invoices,
# documentation, M+PP.
#
# A template is searched first in config.templatePath, then in
# data/ch/templates. In the template "o" is the project, "c" its contacts.

import os
from datetime import date

from relatorio.templates.opendocument import Template

from documents import DocumentError

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

# template type => template file, output folder in the project, numbering
TEMPLATES = {
    "partial_invoice": ("fin" + os.sep + "partial_invoice.odt", "fin", "invoice"),
    "final_invoice":   ("fin" + os.sep + "final_invoice.odt",   "fin", "invoice"),
    "small_invoice":   ("fin" + os.sep + "small_invoice.odt",   "fin", "invoice"),
    "quote":           ("off" + os.sep + "quote.odt",           "off", "quote"),
    "documentation":   ("doc" + os.sep + "documentation.odt",   "doc", "Dokumentation.odt"),
    "mundpp":          ("evu" + os.sep + "MP_PV_Final_20190301_de.ods", "evu", "MP_PV.ods"),
}


def templateCopyReplace(src, dest, model):
    basic = Template(source='', filepath=src)
    basic_generated = basic.generate(o=model, c=model.contacts).render()

    f = open(dest, 'wb')
    f.write(basic_generated.getvalue())
    f.close()


# Create a document of templateType in the folder of the project saved under
# savePath. Returns the path of the new file, raises DocumentError.
def createFromTemplate(templateType, savePath, model, config):
    # another window may have used a quote/invoice number in the meantime
    config.reloadNumbers()

    in_path, out_dir, out_file = TEMPLATES[templateType]
    if out_file == "invoice":
        out_file = config.getNextInvoiceName() + ".odt"
    elif out_file == "quote":
        out_file = config.getNextQuoteName() + ".odt"

    if not savePath:
        raise DocumentError(templateType + ' erstellen', 'Kein Pfad')

    defaultPath = DATA_PATH + os.sep + "ch" + os.sep + "templates" + os.sep + in_path
    localPath = config.templatePath + os.sep + in_path
    # first search template in  "local", config path
    if os.path.exists(localPath):
        templatePath = localPath
    # then default
    elif os.path.exists(defaultPath):
        templatePath = defaultPath
    else:
        raise DocumentError(templateType + ' Vorlage nicht gefunden', 'def Pfad = ' + defaultPath)

    projectDir = os.path.dirname(savePath)
    if not os.path.isdir(projectDir):
        raise DocumentError(templateType + ' erstellen', 'Pfad nicht gefunden\n' + savePath)

    outDir = projectDir + os.sep + out_dir
    outPath = outDir + os.sep + out_file
    if not os.path.isdir(outDir):
        os.makedirs(outDir)

    # dot not overwrite existing files
    if os.path.exists(outPath):
        raise DocumentError(templateType + ' erstellen', 'Datei existiert bereits:\n' + outPath)

    model._invoiceName = config.getNextInvoiceName()
    model._quoteName = config.getNextQuoteName()
    model._todayIso = date.today().isoformat()
    model.owner = model.contacts.owner      # backwards compatibility
    model.config = config       # stays on the model, the TAG scripts need it
    try:
        templateCopyReplace(templatePath, outPath, model)
    finally:
        del model.owner
        del model._invoiceName
        del model._quoteName
        del model._todayIso

    # the number is used only now that the file exists
    if templateType == "quote":
        config.useQuoteNumber()
    elif templateType.endswith("_invoice"):
        config.useInvoiceNumber()

    return outPath
