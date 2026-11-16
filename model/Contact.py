#!/usr/bin/python
# -*- coding: utf-8 -*-

# People and companies involved in a site
# (doc/file_format_v3/file_format.md, section 5).
#
# A Contact has an address, channels (phone, email ...) in the order of their
# priority, and bank accounts. The contacts of a site have roles; the
# contacts inside the snapshots of municipality and grid operator have none.
#
# The forms, document templates and form scripts written for file version 2
# use one field per value (contact.phone, contact.street, contact.company).
# These names still work, as properties on top of the version 3 fields.

import sqlite3

from model.ModelNode import ModelNode, newId

ROLES = ("owner", "client", "billing", "tenant", "electrician", "architect", "planner", "roofer", "contact")
CHANNEL_KINDS = ("phone", "mobile", "email", "fax", "web")

# role => caption
ROLE_NAMES = {
    "owner": "Bauherr",
    "client": "Auftraggeber",
    "billing": "Rechnungsempfänger",
    "tenant": "Mieter",
    "electrician": "Elektriker AC",
    "architect": "Architekt",
    "planner": "Planer",
    "roofer": "Dachdecker",
    "contact": "Kontakt",
}


class Address(ModelNode):

    def __init__(self, top=None):
        self._top = top
        self.street = None
        self.streetNumber = None
        self.address1 = None
        self.address2 = None
        self.floor = None
        self.room = None
        self.zip = None
        self.city = None
        self.region = None
        self.country = None


class Contact(ModelNode):

    _types = {"roles": "list", "from": "date", "to": "date", "channels": "json", "bankAccounts": "json",
              "ext": "json"}

    def __init__(self, top=None):
        self._top = top
        self._slots = {}
        self.id = None
        self.roles = []

        # Organizational
        self.organization = None    # company or any other organization
        self.department = None

        # Personal
        self.title = None
        self.firstName = None
        self.middleName = None
        self.lastName = None
        self.nickName = None

        self.address = Address(top)

        # [{"kind": "phone", "value": "061 000 00 00"}, ...]
        self.channels = []

        # [{"owner": ..., "bank": ..., "iban": ..., "bic": ...}, ...]
        self.bankAccounts = []

        # a change of owner: this contact had its roles from .. to
        self.__dict__["from"] = None
        self.to = None
        self.ext = {}

    # True if nothing but the roles is filled in
    def isEmpty(self):
        data = self.toDict()
        return not any(key not in ("id", "roles") for key in data)

    # ---- channels ---------------------------------------------------------

    # The number'th (from 0) channel of a kind. A field which created a
    # channel keeps it while the site is open (_slots), so filling in the
    # second phone before the first doesn't mix them up.
    def _channel(self, kind, number):
        slots = self.__dict__.setdefault("_slots", {})
        present = lambda entry: any(entry is c for c in self.channels)
        entry = slots.get((kind, number))
        if entry is not None and present(entry):
            return entry
        claimed = [e for key, e in slots.items() if key != (kind, number) and present(e)]
        free = [c for c in self.channels if c.get("kind") == kind and not any(c is e for e in claimed)]
        index = number - len([1 for (k, n), e in slots.items() if k == kind and n < number and present(e)])
        if 0 <= index < len(free):
            slots[(kind, number)] = free[index]
            return free[index]
        return None

    def getChannel(self, kind, number=0):
        entry = self._channel(kind, number)
        return (entry.get("value") or "") if entry else ""

    def setChannel(self, kind, number, value):
        value = (value or "").strip()
        entry = self._channel(kind, number)
        if entry is not None:
            if value:
                entry["value"] = value
            else:
                self.channels[:] = [c for c in self.channels if c is not entry]
            return
        if not value:
            return
        entry = {"kind": kind, "value": value}
        # before the channels of the same kind with a higher number, else
        # after the last of the same kind, phones before emails
        pos = len(self.channels)
        later = [e for (k, n), e in self._slots.items() if k == kind and n > number]
        for i, c in enumerate(self.channels):
            known = c.get("kind") in CHANNEL_KINDS
            if any(c is e for e in later) or (known and CHANNEL_KINDS.index(c.get("kind")) > CHANNEL_KINDS.index(kind)):
                pos = i
                break
        self.channels.insert(pos, entry)
        self._slots[(kind, number)] = entry

    # ---- bank account -----------------------------------------------------

    def _getAccount(self, key):
        if not self.bankAccounts:
            return ""
        account = self.bankAccounts[0]
        if key == "iid":
            return ((account.get("ext") or {}).get("ch") or {}).get("iid") or ""
        return account.get(key) or ""

    def _setAccount(self, key, value):
        value = (value or "").strip() or None
        if not self.bankAccounts:
            if value is None:
                return
            self.bankAccounts.append({})
        account = self.bankAccounts[0]
        if key == "iid":
            ns = account.setdefault("ext", {}).setdefault("ch", {"v": 1})
            ns["iid"] = value
            if value is None:
                del ns["iid"]
                if list(ns) == ["v"]:
                    del account["ext"]["ch"]
                if not account["ext"]:
                    del account["ext"]
        elif value is None:
            account.pop(key, None)
        else:
            account[key] = value
        if not account:
            self.bankAccounts.remove(account)

    # ---- master data ------------------------------------------------------

    def fromId(self, contactId):
        from Config import Config
        con = sqlite3.connect(Config.getMasterDbPath())
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        sql = "SELECT * FROM address WHERE id=?"
        res = cur.execute(sql, [contactId])
        db_row = res.fetchone()

        if db_row:
            self.fromDbRow(db_row)

    def fromMunicipalityType(self, munId, contactType):
        from Config import Config
        con = sqlite3.connect(Config.getMasterDbPath())
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        sql = "SELECT * FROM address WHERE fk_municipality=? AND role=?"
        res = cur.execute(sql, [munId, contactType])
        db_row = res.fetchone()

        if db_row:
            self.fromDbRow(db_row)

    def fromDbRow(self, db_row):
        self.company = db_row["company"]
        self.firstName = db_row["firstName"] or None
        self.lastName = db_row["lastName"] or None
        self.channels = []
        self.phone = db_row["phone"]
        self.phone2 = db_row["phone2"]
        self.email = db_row["email"]
        self.email2 = db_row["email2"]
        self.street = db_row["street"]
        self.streetNumber = db_row["streetNumber"]
        self.zip = db_row["zip"]
        self.city = db_row["city"]

    # ---- texts ------------------------------------------------------------

    # get the first phone Number
    def getAnyPhone(self):
        for kind in ("phone", "mobile"):
            for number in (0, 1):
                if self.getChannel(kind, number):
                    return self.getChannel(kind, number)

        return "0800 800 800"       # default to swisscom main number :)

    def getNameCity(self):
        ret = self.company + " " + (self.lastName or "") + " " + (self.firstName or "") + " " + self.city
        ret = ret.strip()
        return ret

    def getNameAddress(self):
        ret = self.company + " " + (self.lastName or "") + " " + (self.firstName or "")
        ret = ret.strip()
        if not ret:
            ret = "No Name"
        return ret

    def getPhoneClean(self):
        return self.cleanPhoneNumber(self.phone)

    def getPhone2Clean(self):
        return self.cleanPhoneNumber(self.phone2)

    def getMobileClean(self):
        return self.cleanPhoneNumber(self.mobile)

    def cleanPhoneNumber(self, number):
        if not number:
            return ""
        number = number.replace("/", "")
        number = number.replace(" ", "")
        number = number.replace("+41", "0")
        number = number.strip()
        return number

    def exportVCard(self):
        ret = ""
        ret += "BEGIN:VCARD\n"
        ret += "VERSION:3.0\n"
        ret += "FN:"+self.getNameCity()+"\n"
        ret += "N:"+self.getNameCity()+";;;;\n"
        ret += "ORG:Solar;Owner\n"
        if self.email:
            ret += "EMAIL:"+self.email+"\n"
        if self.email2:
            ret += "EMAIL:"+self.email2+"\n"
        if self.phone:
            ret += "TEL;TYPE=voice:"+self.phone+"\n"
        if self.phone2:
            ret += "TEL;TYPE=voice:"+self.phone2+"\n"
        if self.mobile:
            ret += "TEL;TYPE=voice:"+self.mobile+"\n"
        ret += "END:VCARD\n"

        return ret

    # caption of the roles
    def getRoleName(self):
        if not self.roles:
            return "None"
        return ", ".join(ROLE_NAMES.get(role, str(role)) for role in self.roles)

    # ---- names of file version 2 -------------------------------------------

    # the first role, with its version 2 name
    @property
    def role(self):
        if not self.roles:
            return None
        return {"electrician": "installer_ac"}.get(self.roles[0], self.roles[0])

    @property
    def company(self):
        return self.organization or ""

    @company.setter
    def company(self, value):
        self.organization = (value or "").strip() or None


def _addressProperty(key):
    def getter(self):
        return self.address.get(key) or ""

    def setter(self, value):
        self.address.set(key, (value or "").strip() or None)
    return property(getter, setter)


def _channelProperty(kind, number):
    return property(lambda self: self.getChannel(kind, number),
                    lambda self, value: self.setChannel(kind, number, value))


def _accountProperty(key):
    return property(lambda self: self._getAccount(key), lambda self, value: self._setAccount(key, value))


for _key in ("street", "streetNumber", "address1", "address2", "floor", "room", "zip", "city", "country"):
    setattr(Contact, _key, _addressProperty(_key))
for _name, _kind, _number in (("phone", "phone", 0), ("phone2", "phone", 1), ("mobile", "mobile", 0),
                              ("email", "email", 0), ("email2", "email", 1)):
    setattr(Contact, _name, _channelProperty(_kind, _number))
for _name, _key in (("accountOwner", "owner"), ("accountBank", "bank"), ("accountIban", "iban"),
                    ("accountBic", "bic"), ("accountIid", "iid")):
    setattr(Contact, _name, _accountProperty(_key))


# The contacts of a site: a list of Contact. Owner and electrician are
# always there for forms and documents; while they are empty they are not
# saved.
class ContactList(list):

    def __init__(self, top=None):
        super().__init__()
        self._top = top

    # the first contact with a role, None if there is none
    def withRole(self, role):
        for contact in self:
            if role in contact.roles and not contact.to:
                return contact
        return None

    def _mandatory(self, role):
        contact = self.withRole(role)
        if contact is None:
            contact = self.addContact(role)
        return contact

    # owner of the photovoltaic system
    @property
    def owner(self):
        return self._mandatory("owner")

    # electrician of the AC side
    @property
    def installer_ac(self):
        return self._mandatory("electrician")

    # add a new contact with a role
    def addContact(self, role):
        contact = Contact(self._top)
        contact.id = newId()
        contact.roles = [role]
        contact._parent = self._top
        self.append(contact)
        return contact

    def canRemove(self, contact):
        return contact in self

    def removeContact(self, contact):
        self.remove(contact)
