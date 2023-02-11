#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# Import static data for Switzerland

import sqlite3
import csv

con = sqlite3.connect("../masterdata.db")

cur = con.cursor()

# remove all data, reset sequences
sql = "DELETE FROM power_company"
cur.execute(sql)
sql = "DELETE FROM sqlite_sequence WHERE name='power_company'"
cur.execute(sql)

sql = "DELETE FROM municipality"
cur.execute(sql)
sql = "DELETE FROM sqlite_sequence WHERE name='municipality'"
cur.execute(sql)

sql = "DELETE FROM zip_code"
cur.execute(sql)
sql = "DELETE FROM sqlite_sequence WHERE name='zip_code'"
cur.execute(sql)

# import municipalities and zip_codes
with open('2023-01-01_Ortschaften.csv', newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter=',', quotechar='"')

    # skip first row
    next(reader)

    for row in reader:
        zip_name = row[0].strip()       # Ortschaftsname
        zip_code = row[1].strip()       # PLZ
        mun_name = row[3].strip()       # Gemeindename mun short for municipality
        mun_code = row[4].strip()       # Gemeindenummer, BFS-Nr
        district_code = row[5].strip()   # Kantonskürzel
        
        mun_id = 0

        # first check if municipality already exists
        # if not insert it
        sql = "SELECT * FROM municipality WHERE code=?"
        res = cur.execute(sql, [mun_code])
        db_row = res.fetchone()
        if db_row is None:
            sql = "INSERT INTO municipality (country_code, district_code, code, name) VALUES (?, ?, ?, ?)"
            cur.execute(sql, ("CH", district_code, mun_code, mun_name))
            mun_id = cur.lastrowid
        else:
            mun_id = db_row[0]
        
        sql = "INSERT INTO zip_code (fk_municipality, zip_code, name) VALUES (?, ?, ?)"
        cur.execute(sql, (mun_id, zip_code, zip_name))


# import power companies

with open('2022-10-21_EVU_Gemeinde.csv', newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter=',', quotechar='"')
    #skip first three rows

    next(reader)
    next(reader)
    next(reader)

    for row in reader:
        pc_name = row[0].strip()
        pc_street = row[1].strip()
        pc_zip_code = row[2].strip()
        pc_city = row[3].strip()
        mun_nr = row[4].strip()
        mun_name = row[5].strip()
        
        pc_id = 0
        mun_id = 0

        # first check if power company already in table
        # if not insert it
        sql = "SELECT * FROM power_company WHERE name=?"
        res = cur.execute(sql, [pc_name])
        db_row = res.fetchone()
        if db_row is None:
            sql = "INSERT INTO power_company (name, address1, zip_code, city) VALUES (?, ?, ?, ?)"
            cur.execute(sql, (pc_name, pc_street, pc_zip_code, pc_city))
            pc_id = cur.lastrowid
        else:
            pc_id = db_row[0]
        
        # now search for municipality
        sql = "SELECT * FROM municipality WHERE code=?"
        res = cur.execute(sql, [mun_nr])
        db_row = res.fetchone()
        if db_row is None:
            print("Municipality not found code=%s name=%s" % (mun_nr, mun_name))
            continue
        else:
            mun_id = db_row[0]
        
        sql = "UPDATE municipality SET fk_power_company=? WHERE id=?"
        cur.execute(sql, (pc_id, mun_id))


con.commit()
con.close()
