#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# Import static data for Switzerland

import sqlite3
import csv

con = sqlite3.connect("../masterdata.db")

cur = con.cursor()

# import all power companies
sql = "DELETE FROM power_company"
cur.execute(sql)

sql = "DELETE FROM sqlite_sequence WHERE name='power_company'"
cur.execute(sql)

with open('power_companies.csv', newline='') as csvfile:
	reader = csv.reader(csvfile, delimiter=',', quotechar='"')
	#skip first row
	next(reader)
	for row in reader:
		sql = "INSERT INTO power_company (vse_id, name, zip_code, city) VALUES (?, ?, ?, ?)"
		cur.execute(sql, (row[0], row[1], row[2], row[3]))

# import all cities, zip_codes

sql = "DELETE FROM city"
cur.execute(sql)
sql = "DELETE FROM sqlite_sequence WHERE name='city'"
cur.execute(sql)

sql = "DELETE FROM zip_code"
cur.execute(sql)
sql = "DELETE FROM sqlite_sequence WHERE name='zip_code'"
cur.execute(sql)

with open('cities.csv', newline='') as csvfile:
	reader = csv.reader(csvfile, delimiter=',', quotechar='"')
	#skip first row
	next(reader)
	for row in reader:
		zip_code = row[0]
		city = row[1]
		canton = row[2]
		city_id = 0
		
		# first check if city already in table
		sql = "SELECT * FROM city WHERE country_code=? AND name=?"
		res = cur.execute(sql, ('CH', city))
		db_row = res.fetchone()
		if db_row is None:
			sql = "INSERT INTO city (country_code, name, canton_code) VALUES (?, ?, ?)"
			cur.execute(sql, ('CH', city, canton))
			city_id = cur.lastrowid
		else:
			city_id = db_row[0]
		
		# now insert zip_coe
		sql = "INSERT INTO zip_code (fk_city, zip_code) VALUES (?, ?)"
		cur.execute(sql, (city_id, zip_code))


con.commit()
con.close()
