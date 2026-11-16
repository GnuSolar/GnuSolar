#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# The installer's own contacts, kept in the user database (Config.getUserDbPath())
# apart from any project: electricians, roofers, architects, suppliers, ...
#
#   store = ContactStore(path)
#   for contactId, label in store.list("muster"): ...
#   contact = store.load(contactId)
#   contactId = store.save(contact)      # inserts when contact._id is None
#   store.delete(contactId)
#
# The table "address" has one column per field of model.Contact. Columns of
# fields added to Contact later are added to an existing database when it is
# opened, so no data is lost.

import sqlite3

from model.Contact import Contact


# the fields of a Contact, which are the columns of the table
FIELDS = [k for k in Contact().__dict__ if not k.startswith("_")]

# fields the search looks in
SEARCH_FIELDS = ["company", "firstName", "lastName", "nickName", "street", "zip", "city",
                 "email", "email2", "phone", "phone2", "mobile"]


# the text of a contact in the list: company, last and first name, city
def label(contact):
    parts = [contact.company, contact.lastName, contact.firstName, contact.city]
    text = " ".join(p.strip() for p in parts if p and p.strip())
    return text or "(ohne Namen)"


class ContactStore:

    def __init__(self, path):
        self.path = path
        self.con = sqlite3.connect(path)
        self.con.row_factory = sqlite3.Row
        self._createTable()

    def _createTable(self):
        columns = ", ".join('"%s" TEXT' % f for f in FIELDS)
        self.con.execute('CREATE TABLE IF NOT EXISTS "address" ("id" INTEGER PRIMARY KEY AUTOINCREMENT, %s)' % columns)
        existing = {row["name"] for row in self.con.execute('PRAGMA table_info("address")')}
        for field in FIELDS:
            if field not in existing:
                self.con.execute('ALTER TABLE "address" ADD COLUMN "%s" TEXT' % field)
        self.con.commit()

    def close(self):
        self.con.close()

    # (id, label) of the contacts whose fields contain every word of search,
    # sorted by label
    def list(self, search=""):
        sql = 'SELECT * FROM "address"'
        params = []
        conditions = []
        for word in search.split():
            fields = " OR ".join('IFNULL("%s", \'\') LIKE ?' % f for f in SEARCH_FIELDS)
            conditions.append("(" + fields + ")")
            params += ["%" + word + "%"] * len(SEARCH_FIELDS)
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        result = []
        for row in self.con.execute(sql, params):
            result.append((row["id"], label(self._toContact(row))))
        result.sort(key=lambda r: r[1].lower())
        return result

    # the contact with this id, or None
    def load(self, contactId):
        row = self.con.execute('SELECT * FROM "address" WHERE "id"=?', [contactId]).fetchone()
        return self._toContact(row) if row else None

    # fill an existing Contact object with the contact of this id
    def loadInto(self, contact, contactId):
        loaded = self.load(contactId)
        if loaded is None:
            return False
        for field in FIELDS:
            setattr(contact, field, getattr(loaded, field))
        contact._id = loaded._id
        return True

    # store the contact, returns its id. Empty texts are stored as NULL.
    def save(self, contact):
        values = [getattr(contact, f, None) or None for f in FIELDS]
        contactId = getattr(contact, "_id", None)
        if contactId is None:
            columns = ", ".join('"%s"' % f for f in FIELDS)
            marks = ", ".join("?" for f in FIELDS)
            cur = self.con.execute('INSERT INTO "address" (%s) VALUES (%s)' % (columns, marks), values)
            contact._id = cur.lastrowid
        else:
            assignments = ", ".join('"%s"=?' % f for f in FIELDS)
            self.con.execute('UPDATE "address" SET %s WHERE "id"=?' % assignments, values + [contactId])
        self.con.commit()
        return contact._id

    def delete(self, contactId):
        self.con.execute('DELETE FROM "address" WHERE "id"=?', [contactId])
        self.con.commit()

    def _toContact(self, row):
        contact = Contact()
        keys = row.keys()
        for field in FIELDS:
            if field in keys:
                setattr(contact, field, row[field])
        contact._id = row["id"]
        return contact
