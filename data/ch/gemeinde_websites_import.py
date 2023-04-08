#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# Homepages der schweizer Gemeinden importieren
# Reimport möglich, Gemeinde einträge müssen existiern
# Format der URL:
#   - https bevorzugt
#   - trailing slash
#   - Bei 301 (moved permanently) neu url nehmen
#   - Bei 307 (moved temporarly) neu url nicht nehmen

import sqlite3
import csv

con = sqlite3.connect("../masterdata.db")
con.row_factory = sqlite3.Row
cur = con.cursor()

count = 0

# import municipalities and zip_codes
with open('gemeinde_websites.csv', newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter=',', quotechar='"')

    # skip header
    next(reader)

    for row in reader:
        code = row[0].strip()       
        name = row[1].strip()       
        website = row[2].strip()     

        sql = "SELECT * FROM municipality WHERE code=?"
        res = cur.execute(sql, [code])
        db_row = res.fetchone()
        
        if db_row is None:
            print("Municipality not found, code=" + code + ", name=" + name )
            continue

        mun_id = db_row["id"]

        sql = "UPDATE municipality SET website=? WHERE id=?"
        res = cur.execute(sql, [website, mun_id])
        
        count += 1

print(str(count) + " Gemeinde Webseiten importiert")

con.commit()
con.close()

