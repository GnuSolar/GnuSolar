#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# Verwaltungskontakte aller schweizer Gemeinden exportieren nach csv

import sqlite3
import csv

con = sqlite3.connect("../masterdata.db")
con.row_factory = sqlite3.Row
cur = con.cursor()

sql = "SELECT municipality.code, municipality.name as mun_name, contact.* FROM contact INNER JOIN municipality ON contact.fk_municipality=municipality.id WHERE municipality.country_code=? ORDER BY code+0"     # Order numerically
res = cur.execute(sql, ["CH"])

count = 0

with open('gemeinde_kontakte.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile, delimiter=',',
                            quotechar='"', quoting=csv.QUOTE_MINIMAL)
    writer.writerow(['BFS-Nummer', 'Gemeindenamen', 'Adresstyp', 'Abteilung', 'E-Mail', 'Telefon', 'Adresse', 'PLZ', 'Ort'])


    for row in cur:
        writer.writerow([row["code"], row["mun_name"], row["type"], row["function"], row["email"], row["phone"], row["address1"], row["zip_code"], row["city"]])
        count += 1
        
print (str(count) + " Gemeinde Kontakte exportiert")

exit()
