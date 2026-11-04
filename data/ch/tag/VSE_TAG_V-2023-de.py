self.fillxlsx_sheet = 'VSE TAG'
self.fillxlsx_data = {
# Header
    'L4' : model.powerCompany.name,             # Netzbetreiber (VNB)
#    'L5' : '',                                 # VNB Objekt-Nr
#    'L6' : '',                                 # VNB TAG / Projekt-Nr.

# Eigentümer
    'F10' : model.contacts.owner.lastName,
    'AK10' : model.contacts.owner.firstName,
    'F11' : model.contacts.owner.street,
    'AA11' : model.contacts.owner.streetNumber,
    'AI11' : model.contacts.owner.zip,
    'AP11' : model.contacts.owner.city,
    'F12' : model.contacts.owner.phone,
    'U12' : model.contacts.owner.email,

# Standort der Anlage
    'F14' : model.building.street,
    'AA14' : model.building.streetNumber,
#    'AL14' : '',                               # Gebäudeart
    'F15' : model.building.zip,
    'M15' : model.building.city,
    'G16' : model.municipality.name,
    'W16' : model.building.plotNumber,
#    'AF15' : True,                             # Gebäude neu
    'AK15' : True,                              # Gebäude bestehend
#    'AF16' : True,                             # Gebäude anders
#    'AI16' : '',
    'G17' : model.building.meterNumberOld,      # Zähler-Nr.
    'Z17' : model.building.mainFuseSize,        # Netzanschluss (HAK) A
#    'AF17' : True,                             # Netzanschluss neu
    'AK17' : True,                              # Netzanschluss bestehend

# einreichendes Unternehmen
    'F19' : model.config.installer_company,
    'F20' : model.config.installer_street,
    'AA20' : model.config.installer_streetNumber,
    'AI20' : model.config.installer_zip,
    'AP20' : model.config.installer_city,
    'F21' : model.config.installer_phone,
    'U21' : model.config.installer_email,
    'K22' : model.config.installer_firstName + " " + model.config.installer_lastName,    # Sachbearbeiter
    'AS22' : model.progress.launch or self.turnOnIso,    # Voraussichtliche Inbetriebnahme

# Anschlussgesuch für folgende Geräte
#    'B24' : True,                              # Elektrische Wärme/WP/Kälte
    'P24' : True,                               # Energieerzeugungsanlage
#    'AC24' : True,                             # Anlage mit Netzrückwirkung
#    'AM24' : True,                             # Energiespeicher
#    'AT24' : True,                             # Ladeinfrastruktur für Elektrofahrzeuge

# Energieerzeugungsanlage (EEA), rows 42-45, 46 Weitere/Andere
    'B38' : True,                               # Neuanlage
#    'J38' : True,                              # Änderung / Erweiterung
    'A42' : 'Photovoltaik',                     # Art der Erzeugung (drop down)
#    'K42' : '',                                # Gerätehersteller
    'Q42' : model.plant.inverterDesc,           # Gerätetyp
    'W42' : 'Netzparallelbetrieb',              # Art des Betriebs (drop down)
    'AB42' : '3-phasig',                        # Phasen (drop down)
#    'AE42' : '',                               # Absicherung [A]
#    'AH42' : '',                               # Anläufe pro Stunde
#    'AK42' : '',                               # Anlaufstrom [A]
    'AN42' : 1,                                 # Anzahl EEE
    'AQ42' : fillxlsx.number(model.plant.totalPowerAc),          # AC Leistung EEE [kVA]
    'AT42' : fillxlsx.number(model.plant.totalPowerDc),          # DC Leistung [kWp]
    'AW42' : 1,                                 # cos phi
    'AZ42' : fillxlsx.number(model.plant.totalPowerAc),          # AC Leistung total [kVA]
#    'BC42' : '',                               # Einspeisebegrenzung [kW]
    'AZ49' : fillxlsx.number(model.plant.totalPowerAc),          # max. Leistungsabgabe ins Verteilnetz [kW]
#    'Q50' : '',                                # Bemerkung Installateur
#    'AD53' : True,                             # Notstrom zur Synchronisation
#    'AN53' : True,                             # Notstrom als EEE
    'AD54' : True,                              # Umschaltung Inselbetrieb Nein
#    'AI54' : True,                             # Umschaltung Inselbetrieb Ja
    'AD55' : True,                              # Systemdienstleistung Nein
#    'AI55' : True,                             # Systemdienstleistung Ja
#    'AR55' : '',                               # Anbieter

# Unterschrift des einreichenden Unternehmens
#    'A128' : '',                               # Bemerkungen
    'F136' : self.todayIso,                     # Datum
    '' : ''
}

# cells to put the signature image (config.installer_signature) on : scale,
# bigger than the cells, so it overlaps them like a real signature
self.fillxlsx_signature = {'AG136:BG138' : 2.0}
