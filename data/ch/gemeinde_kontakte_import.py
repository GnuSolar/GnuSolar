#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# Gemeindekontakte der schweizer Gemeinden importieren

import sqlite3
import csv
import re

con = sqlite3.connect("../master.db")
con.row_factory = sqlite3.Row
cur = con.cursor()

updated = 0
inserted = 0

# import municipalities and zip_codes
with open('gemeinde_kontakte.csv', newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter=',', quotechar='"')

    # skip header
    next(reader)

    for row in reader:
        code = row[0].strip()       
        mun_name = row[1].strip()       
        role = row[2].strip()     
        company = row[3].strip()     
        email = row[4].strip()     
        phone = row[5].strip()     
        address1 = row[6].strip()     
        zip_code = row[7].strip()     
        city = row[8].strip()     

        # split address into street and streetnumber
        street = address1
        streetNumber = ""
        if address1 != "":
            pat = re.compile('(.*)\W+(\d\d?\d?\w?)', re.DOTALL)
            m = pat.match(address1)
            if m:
                street = m.group(1).strip()
                streetNumber = m.group(2).strip()

        # first get the municipality
        sql = "SELECT * FROM municipality WHERE code=?"
        res = cur.execute(sql, [code])
        db_row = res.fetchone()
        
        if db_row is None:
            print("Municipality not found, code=" + code + ", name=" + name )
            continue

        mun_id = db_row["id"]

        # now get the contact
        sql = "SELECT * FROM address WHERE role=? AND fk_municipality=?"
        res = cur.execute(sql, [role, mun_id])
        db_row = res.fetchone()

        if db_row is None:
            # insert it
            sql = "INSERT INTO address (fk_municipality, role, company, email, phone, street, streetNumber, zip, city) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
            cur.execute(sql, (mun_id, role, company, email, phone, street, streetNumber, zip_code, city))
            inserted += 1
        else:
            # or update it
            contact_id = db_row["id"]
            sql = "UPDATE address SET fk_municipality=?, role=?, company=?, email=?, phone=?, street=?, streetNumber=?, zip=?, city=? WHERE id=?"
            cur.execute(sql, (mun_id, role, company, email, phone, street, streetNumber, zip_code, city, contact_id))
            updated += 1
            

print(str(updated) + " Gemeinde Kontakte aktualisiert")
print(str(inserted) + " Gemeinde Kontakte eingefügt")

con.commit()
con.close()

