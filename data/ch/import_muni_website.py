#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# Import static data for Switzerland

import sqlite3
import csv
import requests
import re

con = sqlite3.connect("../masterdata.db")
con.row_factory = sqlite3.Row

cur = con.cursor()

# scrap Wikipedia pages for Municipality websites
# from https://de.wikipedia.org/wiki/Liste_Schweizer_Gemeinden

with open('2023-01-01_Gemeinden_Wikipedia.txt', newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter='|', quotechar='"')

    pat = re.compile("Website")

    for row in reader:
        if len(row) != 7:
            continue
            
        mun_name  = row[1].strip()       # Gemeindename
        wiki_page = row[2].strip()       # Wikipedia Namen
        mun_code  = row[4].strip()       # Gemeindenummer, BFS-Nr
        
        if not mun_code.isnumeric():
            continue

        mun_code = str(int(mun_code))

        # skip if website already inserted
        sql = "SELECT * FROM municipality WHERE code=?"
        res = cur.execute(sql, [mun_code])
        db_row = res.fetchone()
        
        if db_row is None:
            print("Municipality not found, mun_code=" + mun_code)
            continue

        mun_id = db_row["id"]
        website = db_row["website"]
        if website:
            continue

        # fetch the url
        if not wiki_page:
            wiki_page = mun_name
        
        wiki_page = wiki_page.replace(" ", "_")
        wiki_url = "http://de.wikipedia.org/wiki/" + wiki_page
        
        response = requests.get(url=wiki_url)
        text = response.text
        
        m = re.findall("Website:.*?href=\"([^\"]*)", text, re.DOTALL)
        if len(m) != 1:
            print("Website not found for " + wiki_page)
            continue
        website = m[0]
        print(website)
        
        # first check if municipality already exists
        # if not insert it
        sql = "SELECT * FROM municipality WHERE code=?"
        res = cur.execute(sql, [mun_code])
        db_row = res.fetchone()
        
        if db_row is None:
            print("Municipality not found, sql=" + sql)
            continue

        mun_id = db_row[0]
        
        sql = "UPDATE municipality SET website=? WHERE id=?"
        cur.execute(sql, (website, mun_id))
        con.commit()

con.close()
