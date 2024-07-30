owner = model.contacts.owner
building = model.building

self.fillpdf_data = {
    'Seite 1' : False,  # ?
    '21' : '',          # ?
    '1' : '',           # Projekt-Nr.
    '2' : '',           # GVZ-Nr.
    '4' : model.plant.totalArea,
    
    # Kunde
    'pa.gvz.5' : str(owner.lastName) + " " + str(owner.firstName),
    'pa.gvz.6' : str(owner.street) + " " + str(owner.streetNumber),
    'pa.gvz.7' : str(owner.zip) + " " + str(owner.city),
    'pa.gvz.8' : str(owner.phone),
    
    # Aufstellort der PV-Anlage
    'pa.gvz.9' : str(building.street) + " " + str(building.streetNumber),
    'pa.gvz.10' : str(building.zip) + " " + str(building.city),
    
    # Erstellt durch
    'pa.gvz.11' : config.installer_company,
    '12' : config.installer_street + " " + config.installer_streetNumber,
    '13' : config.installer_zip + " " + config.installer_city,
    '14' : config.installer_phone,
    
    # Rest
    '15' : self.todayIso,
    '16' : '',          # ?
    '17' : '',
    '18' : '',
    '19' : '',
    'info' : '',        # ?
    'text' : '',        # ?
    '22' : False        # ?
}
