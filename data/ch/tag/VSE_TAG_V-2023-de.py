# model.plant is what the current order installs, model.existing what was
# installed before it and is still there.
new = model.plant
old = model.existing
kW = lambda watt: None if watt is None else watt / 1000

hasPv = new.has("pv_array") or new.has("inverter")
batteries = new.devices("battery")
chargers = new.devices("charger")
heatPumps = new.devices("heat_pump") + new.devices("heating_rod")

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
    'B24' : bool(heatPumps) or None,            # Elektrische Wärme/WP/Kälte
    'P24' : hasPv or None,                      # Energieerzeugungsanlage
#    'AC24' : True,                             # Anlage mit Netzrückwirkung
    'AM24' : bool(batteries) or None,           # Energiespeicher
    'AT24' : bool(chargers) or None,            # Ladeinfrastruktur für Elektrofahrzeuge

# Unterschrift des einreichenden Unternehmens
#    'A128' : '',                               # Bemerkungen
    'F136' : self.todayIso,                     # Datum
    '' : ''
}

# Elektrische Wärme / Wärmepumpen / Kälteanlagen, rows 30-33, 34 Weitere/Andere
if heatPumps:
    self.fillxlsx_data.update({
        'A27' : not (old.has("heat_pump") or old.has("heating_rod")) or None,     # Neuanlage
        'I27' : old.has("heat_pump") or old.has("heating_rod") or None,           # Änderung / Erweiterung
    })
    for row, device in zip(range(30, 34), heatPumps):
        self.fillxlsx_data.update({
#            'A%d' % row : '',                              # Art des Gerätes (drop down)
            'K%d' % row : device.getManufacturer(),         # Gerätehersteller
            'S%d' % row : device.getModel(),                # Gerätetyp
            'AV%d' % row : kW(device.getSpec("powerElectric")),     # Leistungsaufnahme bei Volllast [kW]
        })

# Energieerzeugungsanlage (EEA), rows 42-45, 46 Weitere/Andere
if hasPv:
    self.fillxlsx_data.update({
        'B38' : not old.has("pv_array") or None,    # Neuanlage
        'J38' : old.has("pv_array") or None,        # Änderung / Erweiterung
        'A42' : 'Photovoltaik',                     # Art der Erzeugung (drop down)
#        'K42' : '',                                # Gerätehersteller
        'Q42' : new.inverterDesc,                   # Gerätetyp
        'W42' : 'Netzparallelbetrieb',              # Art des Betriebs (drop down)
        'AB42' : '3-phasig',                        # Phasen (drop down)
#        'AE42' : '',                               # Absicherung [A]
#        'AH42' : '',                               # Anläufe pro Stunde
#        'AK42' : '',                               # Anlaufstrom [A]
        'AN42' : 1,                                 # Anzahl EEE
        'AQ42' : fillxlsx.number(new.totalPowerAc),         # AC Leistung EEE [kVA]
        'AT42' : fillxlsx.number(new.totalPowerDc),         # DC Leistung [kWp]
        'AW42' : 1,                                 # cos phi
        'AZ42' : fillxlsx.number(new.totalPowerAc),         # AC Leistung total [kVA]
#        'BC42' : '',                               # Einspeisebegrenzung [kW]
        'AZ49' : fillxlsx.number(new.totalPowerAc),         # max. Leistungsabgabe ins Verteilnetz [kW]
#        'Q50' : '',                                # Bemerkung Installateur
#        'AD53' : True,                             # Notstrom zur Synchronisation
#        'AN53' : True,                             # Notstrom als EEE
        'AD54' : True,                              # Umschaltung Inselbetrieb Nein
#        'AI54' : True,                             # Umschaltung Inselbetrieb Ja
        'AD55' : True,                              # Systemdienstleistung Nein
#        'AI55' : True,                             # Systemdienstleistung Ja
#        'AR55' : '',                               # Anbieter
    })

# Elektrischer Energiespeicher, rows 86-89, 90 Weitere/Andere
if batteries:
    self.fillxlsx_data.update({
        'B83' : not old.has("battery") or None,     # Neuanlage
        'J83' : old.has("battery") or None,         # Änderung / Erweiterung
        'M92' : fillxlsx.number(new.batteryPower),          # Gesamtleistung der Anlage [kW]
        'AG92' : fillxlsx.number(new.batteryCapacity),      # Gesamtkapazität der Anlage [kWh]
    })
    for nr, device in enumerate(batteries[:4]):
        row = 86 + nr
        count = device.count or 1
        coupling = device.get("coupling")
        self.fillxlsx_data.update({
            'A%d' % row : 'Elektrischer Energiespeicher %d' % (nr + 1),    # Art des Gerätes (drop down)
            'K%d' % row : device.getManufacturer(),         # Gerätehersteller
            'R%d' % row : device.getModel(),                # Gerätetyp
#            'Z%d' % row : 'Keine Ladung aus dem Netz, keine Entladung ins Netz',   # Betriebsart (drop down)
            'AH%d' % row : {                                # Integration in der Installation (drop down)
                'ac' : 'AC (im AC Teil der Installation)',
                'dc_generator' : 'DC (im DC Teil der Installation)',
                'dc_link' : 'DC (im DC Teil der Installation)'}.get(coupling),
            'AP%d' % row : '3-phasig',                      # Phasen (drop down)
#            'AT%d' % row : '',                             # Absicherung [A]
#            'AW%d' % row : '',                             # Nennstrom [A]
            'AY%d' % row : kW(device.getSpec("powerCharge") and device.getSpec("powerCharge") * count),         # Ladeleistung [kVA]
            'BB%d' % row : kW(device.getSpec("powerDischarge") and device.getSpec("powerDischarge") * count),   # Entladeleistung [kVA]
            'BE%d' % row : kW(device.getSpec("capacity") and device.getSpec("capacity") * count),               # Speicherkapazität [kWh]
        })

# Ladeinfrastruktur für Elektrofahrzeuge, rows 104-107, 108 Weitere/Andere
if chargers:
    self.fillxlsx_data.update({
        'B101' : not old.has("charger") or None,    # Neuanlage
        'J101' : old.has("charger") or None,        # Änderung / Erweiterung
    })
    for nr, device in enumerate(chargers[:3]):
        row = 104 + nr
        count = device.count or 1
        power = device.getSpec("powerAc")
        self.fillxlsx_data.update({
            'A%d' % row : 'Ladeanlage %d' % (nr + 1),       # Art des Gerätes (drop down)
            'K%d' % row : device.getManufacturer(),         # Gerätehersteller
            'Q%d' % row : device.getModel(),                # Gerätetyp
            'X%d' % row : 'bidirektional → Kategorie Speicher' if device.getSpec("canDischarge") else 'unidirektional',
            'AD%d' % row : 'AC-Ladung',                     # Ladeart des Fahrzeugs (drop down)
            'AK%d' % row : {1: '1-phasig', 2: '2-phasig', 3: '3-phasig'}.get(device.getSpec("phases")),
            'AN%d' % row : count,                           # Anzahl Ladestationen
            'AT%d' % row : kW(power),                       # Max. Leistung je Ladestation [kVA]
            'AW%d' % row : kW(power and power * count),     # Gesamtleistung Ladeanlage [kVA]
            'AZ%d' % row : 'Ja' if device.get("loadManagement") else 'Nein',      # Integration in Lastmanagement lokal
        })

# cells to put the signature image (config.installer_signature) on : scale,
# bigger than the cells, so it overlaps them like a real signature
self.fillxlsx_signature = {'AG136:BG138' : 2.0}
