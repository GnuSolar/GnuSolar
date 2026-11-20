#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# Documents from OpenDocument templates (relatorio): quote, invoices,
# documentation, M+PP.
#
# A template is searched first in config.templatePath, in the folder the
# installer uses for this kind of document (Config.FOLDERS), then in
# data/ch/templates. A template for the type of the project (PROJECT_TYPES)
# comes first: quote_battery.odt before quote.odt. In the template "o" is the
# project, "c" its contacts.
#
# Du or Sie, as chosen for the contact (Contact.formality):
#   <o.owner.greeting>                       Guten Tag Herr Kraft / Hallo Alois
#   <o.owner.byFormality('Ihnen', 'Dir')>    the first text for Sie, the second for Du

import os
from datetime import date

from relatorio.templates.opendocument import Template

from documents import DocumentError

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

# template type => (folder and file of the template in data/ch/templates,
# kind of folder in the project (Config.FOLDERS), numbering or file name)
TEMPLATES = {
    "partial_invoice": (("fin", "partial_invoice.odt"), "invoices", "invoice"),
    "final_invoice":   (("fin", "final_invoice.odt"),   "invoices", "invoice"),
    "small_invoice":   (("fin", "small_invoice.odt"),   "invoices", "invoice"),
    "quote":           (("off", "quote.odt"),           "quotes", "quote"),
    "documentation":   (("doc", "documentation.odt"),   "documentation", "Dokumentation.odt"),
    "mundpp":          (("evu", "MP_PV_Final_20190301_de.ods"), "gridOperator", "MP_PV.ods"),
}


def templateCopyReplace(src, dest, model):
    basic = Template(source='', filepath=src)
    basic_generated = basic.generate(o=model, c=model.contacts).render()

    f = open(dest, 'wb')
    f.write(basic_generated.getvalue())
    f.close()


# The template file for a project of type projectType: <name>_<type> before
# <name>, each first in the installer's template folder, then in defaultDir.
# None if there is none.
def findTemplate(fileName, projectType, defaultDir, config, folderKind):
    stem, ext = os.path.splitext(fileName)
    names = [fileName]
    if projectType:
        names.insert(0, stem + "_" + projectType + ext)
    dirs = [defaultDir]
    if config.templatePath:
        dirs.insert(0, config.getFolderPath(config.templatePath, folderKind))
    for name in names:
        for d in dirs:
            path = os.path.join(d, name)
            if os.path.exists(path):
                return path
    return None


# The template a document of templateType is made from for a project of type
# projectType, None if there is none
def templateFor(templateType, projectType, config):
    (in_dir, in_file), folderKind, out_file = TEMPLATES[templateType]
    defaultDir = os.path.join(DATA_PATH, "ch", "templates", in_dir)
    return findTemplate(in_file, projectType, defaultDir, config, folderKind)


# Where a template comes from: "Vorlagen-Ordner" for the installer's template
# folder, "GnuSolar" for the templates of the program
def templateSource(path):
    if path.startswith(os.path.join(DATA_PATH, "")):
        return "GnuSolar"
    return "Vorlagen-Ordner"


# Create a document of templateType in the folder of the project saved under
# savePath. Returns the path of the new file, raises DocumentError.
def createFromTemplate(templateType, savePath, model, config):
    # another window may have used a quote/invoice number in the meantime
    config.reloadNumbers()

    (in_dir, in_file), folderKind, out_file = TEMPLATES[templateType]
    if out_file == "invoice":
        out_file = config.getNextInvoiceName() + ".odt"
    elif out_file == "quote":
        out_file = config.getNextQuoteName() + ".odt"

    if not savePath:
        raise DocumentError(templateType + ' erstellen', 'Kein Pfad')

    templatePath = templateFor(templateType, model.type, config)
    if not templatePath:
        raise DocumentError(templateType + ' Vorlage nicht gefunden',
                            'def Pfad = ' + os.path.join(DATA_PATH, "ch", "templates", in_dir, in_file))

    projectDir = os.path.dirname(savePath)
    if not os.path.isdir(projectDir):
        raise DocumentError(templateType + ' erstellen', 'Pfad nicht gefunden\n' + savePath)

    outDir = config.getFolderPath(projectDir, folderKind)
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
