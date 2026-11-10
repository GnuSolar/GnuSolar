#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# A version 2 project with invented data, as GnuSolar wrote it until 2026.

def contact(role, **values):
    ret = {key: None for key in (
        "accountBank", "accountBic", "accountIban", "accountIid", "accountOwner", "address1", "address2", "city",
        "company", "country", "department", "email", "email2", "firstName", "floor", "lastName", "middleName",
        "mobile", "nickName", "phone", "phone2", "room", "street", "streetNumber", "title", "zip")}
    ret["role"] = role
    ret.update(values)
    return ret


def project():
    progress = {key: None for key in (
        "inquiryReceived", "roofMeasure", "roofMeasured", "quote1Sent", "quote2Sent", "quote3Sent", "quote4Sent",
        "orderReceived", "orderRejected", "tagSent", "tagReceived", "iaSent", "iaReceived", "bauSent",
        "bauReceived", "partialInvoiceSent", "partialInvoiceReceived", "partialInvoice2Sent",
        "partialInvoice2Received", "materialOrdered", "materialReceived", "constructionStart", "constructionSort",
        "constructionFixed", "launch", "documentationCreated", "documentationPlaced", "finalInvoiceSent",
        "finalInvoiceReceived", "siNaDcOrdered", "siNaDcReceived", "siNaAcOrdered", "siNaAcReceived",
        "eivComplete", "eivPayed", "archived", "inactiv")}
    progress.update({
        "inquiryReceived": "2026-03-01", "roofMeasured": "2026-03-10", "quote1Sent": "2026-03-20",
        "quote2Sent": "2026-04-02", "orderReceived": "2026-04-15", "tagSent": "2026-04-20",
        "tagReceived": "2026-05-10", "bauSent": "2026-04-21", "partialInvoiceSent": "2026-06-01",
        "partialInvoiceReceived": "2026-06-20", "constructionStart": "2026-06-02", "constructionFixed": True,
        "launch": "2026-06-20", "finalInvoiceSent": "2026-06-25", "eivComplete": "2026-07-01", "eivPayed": "2027",
        "iaSent": "2026-05-01/2026-06-01", "bauReceived": "other", "materialOrdered": "",
    })
    return {
        "building": {
            "areZoneCode": "11", "areZoneName": "Wohnzonen", "buildingId": "190335642", "buildingState": "existing",
            "city": "Musterwil", "country": None, "mainFuseSize": "40", "meterNumberNew": "87654321",
            "meterNumberOld": "12345678", "municipalityCode": "4264", "municipalityName": "Musterwil",
            "plotNumber": "1060", "region": None, "street": "Kirchweg", "streetNumber": "26",
            "swissGridX": "632561.2", "swissGridY": "265432.8", "zip": "4314"},
        "comment": "Hund im Garten",
        "contacts": {"contacts": {
            "installer_ac": contact("installer_ac"),
            "owner": contact("owner", title="Herr", firstName="Hans", lastName="Muster", street="Kirchweg",
                             streetNumber="26", zip="4314", city="Musterwil", phone="061 000 00 00", phone2="",
                             mobile="079 000 00 00", email="hans@example.ch", accountOwner="Hans Muster",
                             accountBank="Musterbank", accountIban="CH00 0000 0000 0000 0000 0", accountIid="80808"),
        }},
        "municipality": {
            "buildingContact": contact("mun_building", company="Bauverwaltung", email="bau@example.ch"),
            "code": "4264", "countryCode": "CH", "districtCode": None, "fkFormBuilding": 2, "fkPowerCompany": 402,
            "id": 1215, "mainContact": contact("mun_main", company="Gemeinde Musterwil", phone="061 111 11 11"),
            "name": "Musterwil", "stateCode": "AG", "website": "https://www.example.ch"},
        "plant": {"constructionType": "builton", "inverterDesc": "Fronius Symo 10.0-3-M", "panelDesc": "JA Solar 440",
                  "totalArea": "47,9", "totalCost": "18450.00", "totalPanelCount": "24", "totalPowerAc": "10",
                  "totalPowerDc": "10.56"},
        "powerCompany": {
            "address1": "Kirchweg 1", "address2": None, "city": "Musterwil", "fkContactTag": 12, "fkFormIa": None,
            "fkFormTag": 4, "id": 402, "mainContact": contact("pow_main"), "name": "Elektra Musterwil",
            "tagContact": contact("pow_tag", company="Netz AG", email="tag@example.ch"), "vseId": None,
            "zipCode": 4314},
        "progress": progress,
        "state": "Running",
    }
