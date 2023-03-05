self.fillform_url = "https://www.ag.ch/app/aem/forms/getForm?formId=81d9b9ac-c457-46c2-9ff7-11fe25d19633&mode=prod"


"""
    Bauzone nach Bundesamt für Raumentwicklung(ARE):
    11 - Wohnzonen
    12 - Arbeitszonen
    13 - Mischzonen
    14 - Zentrumszonen
    15 - Zonen für öffentliche Nutzungen
    16 - eingeschränkte Bauzonen
"""

kernzone_ja = False
kernzone_nein = False
gewerbezone_ja = False
gewerbezone_nein = False
zoneCode = int(model.building.areZoneCode)
if zoneCode == 14 or zoneCode == 15:
    kernzone_ja = True
if zoneCode == 11 or zoneCode == 12:
    kernzone_nein = True
if zoneCode == 12:
    gewerbezone_ja = True
else:
    gewerbezone_nein = True

self.fillform_data = {
    # Bauherrschaft
    'name::Firma_B_13' : model.owner.company,
    'name::Name_B_14' : model.owner.lastName,
    'name::Vorname_B_15' : model.owner.firstName,
    'name::Strasse_B_16' : model.owner.street,
    'name::Nummer_B_17' : model.owner.streetNumber,
    'name::PLZ_B_18' : model.owner.zip,
    'name::Ort_B_19' : model.owner.city,
    'name::Telefon_B_20' : model.owner.getAnyPhone(),
    'name::E-Mail_B_21' : model.owner.email,

    # Eigentümer Liegenschaft
    'name::Standortidentisch_L_27' : True,
    "name::Firma_L_28" : "",
    "name::Name_L_29" : "",
    "name::Vorname_L_30" : "",
    "name::Strasse_L_31" : "",
    "name::Nummer_L_32" : "",
    "name::PLZ_L_33" : "",
    "name::Ort_L_34" : "",
    "name::Telefon_L_35" : "",
    "name::E-Mail_L_36" : "",
    
    # Standort der Anlage
    'name::Standortidentisch_A_40' : True,
    "name::Strasse_A_41" : "",
    "name::Nr_A_42" : "",
    "name::PLZ_A_43" : "",
    "name::Ort_A_44" : "",
    'name::Parzellennummer_45' : model.building.plotNumber,
    'name::Koords1_52' : model.building.swissGridX,
    'name::Koords2_55' : model.building.swissGridY,
    "css selector::input[name='Bauzone_J_N_57'][aria-label='Ja']" : True,
    "css selector::input[name='Bauzone_J_N_57'][aria-label='Nein']" : False,

    "name::Solarthermieanlage_63" : False,
    "name::Auswahl_Kollektor_64" : False,
    "name::Gesamtflaeche_SW_67" : "",
    "name::Heizung_69" : "",
    "name::Warmwasser_70" : "",
    "name::Photovoltanikanlage_72" : True,
    "name::Gesamtflaeche_PV_73" : model.plant.totalArea,
    "name::Gesamtleistung_PV_75" : model.plant.totalPowerDc,
    "css selector::input[name='Auswahl_Netzb_78'][aria-label='Ja']" : False,
    "css selector::input[name='Auswahl_Netzb_78'][aria-label='Nein']" : True,
    "name::Aufdachanlage_83" : False,
    "name::Indachanlage_84" : False,
    "name::Fassadenanlage_85" : False,
    "name::Anlagekosten_90" : model.plant.totalCost,
    "name::Nebenkosten_92" : "0",
    "css selector::input[name='Auswahl_F1_99'][aria-label='Ja']" : kernzone_ja,       # Denkmal, Dorf, Kernzone?
    "css selector::input[name='Auswahl_F1_99'][aria-label='Nein']" : kernzone_nein,
    "css selector::input[name='Auswahl_F2_105'][aria-label='Ja']" : gewerbezone_ja,       # Industrie-, Arbeits- oder Gewerbezone
    "css selector::input[name='Auswahl_F2_105'][aria-label='Nein']" : gewerbezone_nein,
    "css selector::input[name='Auswahl_F3_116'][aria-label='Ja']" : True,       # gestalterische Vorgaben
    "css selector::input[name='Auswahl_F3_116'][aria-label='Nein']" : False,
    "name::Optionsfeldliste_147" : True,      # Radiobutton Angaben vollständig
    "name::Wohnort_150" : model.config.installer_city,
    "name::DateField12_151" : self.todayIso,
    "name::Unterschrift_152" : model.config.installer_firstName + " " + model.config.installer_lastName
}

# constructionType
if model.plant.constructionType == "builton":
    self.fillform_data["name::Aufdachanlage_83"] = True

if model.plant.constructionType == "integrated":
    self.fillform_data["name::Indachanlage_84"] = True
    
if model.plant.constructionType == "facade":
    self.fillform_data["name::Fassadenanlage_85"] = True
