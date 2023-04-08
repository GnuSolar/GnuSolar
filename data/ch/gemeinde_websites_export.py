#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# Hompage aller schweizer Gemeinden exportieren nach csv

import sqlite3
import csv

con = sqlite3.connect("../masterdata.db")
con.row_factory = sqlite3.Row
cur = con.cursor()

sql = "SELECT * FROM municipality WHERE country_code=? ORDER BY code+0"     # Order numerically
res = cur.execute(sql, ["CH"])

count = 0

with open('gemeinde_websites.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile, delimiter=',',
                            quotechar='"', quoting=csv.QUOTE_MINIMAL)
    writer.writerow(['BFS-Nummer', 'Gemeindenamen', 'Website'])


    for row in cur:
        writer.writerow([row["code"], row["name"], row["website"]])
        count += 1
        
print (str(count) + " Gemeinde Webseiten exportiert")

exit()
