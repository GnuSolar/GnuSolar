self.fillform_url = "https://www.ag.ch/app/aem/forms/getForm?formId=81d9b9ac-c457-46c2-9ff7-11fe25d19633&mode=prod"
self.fillform_data = {
    # Bauherrschaft
    'Firma_B_13' : '',
    'Name_B_14' : model.owner.lastName,
    'Vorname_B_15' : model.owner.firstName,
    'Strasse_B_16' : model.owner.street,
    'Nummer_B_17' : model.owner.streetNumber,
    'PLZ_B_18' : model.owner.zip,
    'Ort_B_19' : model.owner.city,
    'Telefon_B_20' : model.owner.phone,
    'E-Mail_B_21' : model.owner.email,
    # Eigentümer Liegenschaft
    'Standortidentisch_L_27' : True,
    
    # Standort der Anlage
    'Standortidentisch_A_40' : True,
    
    'Parzellennummer_45' : model.building.plotNumber,
    'Koords1_52' : model.building.swissGridX,
    'Koords2_55' : model.building.swissGridY,
    
    '' : ''
}
