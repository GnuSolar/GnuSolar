self.fillform_url = "https://www.ag.ch/app/aem/forms/getForm?formId=81d9b9ac-c457-46c2-9ff7-11fe25d19633&mode=prod"
self.fillform_data = {
    # Bauherrschaft
    'Firma_B_13' : model.owner.company,
    'Name_B_14' : model.owner.lastName,
    'Vorname_B_15' : model.owner.firstName,
    'Strasse_B_16' : model.owner.street,
    'Nummer_B_17' : model.owner.streetNumber,
    'PLZ_B_18' : model.owner.zip,
    'Ort_B_19' : model.owner.city,
    'Telefon_B_20' : model.owner.getAnyPhone(),
    'E-Mail_B_21' : model.owner.email,

    # Eigentümer Liegenschaft
    'Standortidentisch_L_27' : True,
    "Firma_L_28" : "",
    "Name_L_29" : "",
    "Vorname_L_30" : "",
    "Strasse_L_31" : "",
    "Nummer_L_32" : "",
    "PLZ_L_33" : "",
    "Ort_L_34" : "",
    "Telefon_L_35" : "",
    "E-Mail_L_36" : "",
    
    # Standort der Anlage
    'Standortidentisch_A_40' : True,
    "Strasse_A_41" : "",
    "Nr_A_42" : "",
    "PLZ_A_43" : "",
    "Ort_A_44" : "",
    'Parzellennummer_45' : model.building.plotNumber,
    'Koords1_52' : model.building.swissGridX,
    'Koords2_55' : model.building.swissGridY,
    'Bauzone_J_N_57' : True,    # TODO: Radiobutton

    "Solarthermieanlage_63" : False,
    "Auswahl_Kollektor_64" : False,
    "Gesamtflaeche_SW_67" : "",
    "Heizung_69" : "",
    "Warmwasser_70" : "",
    "Photovoltanikanlage_72" : True,
    "Gesamtflaeche_PV_73" : model.plant.totalArea,
    "Gesamtleistung_PV_75" : model.plant.totalPowerDc,
    "Aufdachanlage_83" : False,
    "Indachanlage_84" : False,
    "Fassadenanlage_85" : False,
    "Anlagekosten_90" : model.plant.totalCost,
    "Nebenkosten_92" : "0",
    "Auswahl_F1_99" : True,       # Radiobutton Denkmalschutz
    "Optionsfeldliste_147" : True,      # Radiobutton Angaben vollständig
    "Wohnort_150" : model.config.installer_city,
    "DateField12_151" : self.todayIso,
    "Unterschrift_152" : model.config.installer_firstName + " " + model.config.installer_lastName
}

# constructionType
if model.plant.constructionType == "builton":
    self.fillform_data["Aufdachanlage_83"] = True

if model.plant.constructionType == "integrated":
    self.fillform_data["Indachanlage_84"] = True
    
if model.plant.constructionType == "facade":
    self.fillform_data["Fassadenanlage_85"] = True
    
