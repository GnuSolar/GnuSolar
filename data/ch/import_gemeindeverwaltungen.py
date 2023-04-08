#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# Gemeindeverwaltungen importieren

"""
exported from https://www.ch.ch/de/sicherheit-und-recht/behordenadressen/#adressen-der-gemeindeverwaltungen

communes =  __NUXT_JSONP_CACHE__["/de/sicherheit-und-recht/behordenadressen"].fetch["CommunesBlock:0"].communes;

for(i=0; i<communes.length; i++){
  meta = communes[i].metadata;
  
  console.log('"' + meta.agency+'","'+ meta.commune+'","'+ meta.email+'","'+ meta.phoneNumber+'","'+ meta.postalcode+'","'+ meta.streetAddress+'","'+ meta.streetNumber+'","'+ meta.website+'"')
}

"""
import sqlite3
import csv
import requests
import re
import json
import chompjs

con = sqlite3.connect("../masterdata.db")
con.row_factory = sqlite3.Row
cur = con.cursor()

# import municipalities and zip_codes
with open('2023-03-12_Gemeindeverwaltungen.csv', newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter=',', quotechar='"')

    for row in reader:
        agency = row[0].strip()       
        commune = row[1].strip()       
        email = row[2].strip()     
        phoneNumber = row[3].strip()      
        postalcode = row[4].strip()
        streetAddress = row[5].strip()
        streetNumber = row[6].strip()
        website = row[7].strip()

        sql = "SELECT * FROM municipality WHERE name=?"
        res = cur.execute(sql, [commune])
        db_row = res.fetchone()
        
        if db_row is None:
            print("Municipality not found, name=" + commune)
            continue

        mun_id = db_row[0]
        mun_website = db_row[8]

#        if website and mun_website and mun_website.replace("/", "") != website.replace("/", ""):
#            print("website mismatch: " + mun_website + " , " + website)

        sql = "SELECT * FROM contact WHERE type=? AND fk_municipality=?"
        res = cur.execute(sql, ["municipality_main", mun_id])
        db_row = res.fetchone()
        if db_row is None:
            sql = "INSERT INTO contact (fk_municipality, type, function, email, phone, address1, zip_code, city) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
            cur.execute(sql, (mun_id, "municipality_main", agency, email, phoneNumber, streetAddress + " " + streetNumber, postalcode, commune))
            con.commit()

con.commit()
con.close()

