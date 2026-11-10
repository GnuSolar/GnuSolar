#!/usr/bin/python
# -*- coding: utf-8 -*-

# Values of the model and their text in forms and documents.
#
# The model holds numbers as numbers and every date as a Unix timestamp
# (doc/file_format.md, section 3). A calendar day is 12:00 UTC of that day.
# Forms show a day as 2015-03-21 and take that or 21.03.2015.

import re
import json
import calendar
from datetime import date, datetime, timezone

_ISO = re.compile(r"^(\d{4})-(\d{1,2})-(\d{1,2})$")
_DMY = re.compile(r"^(\d{1,2})\.\s*(\d{1,2})\.\s*(\d{4})$")


# timestamp of a calendar day (datetime.date)
def dayToTimestamp(day):
    return calendar.timegm((day.year, day.month, day.day, 12, 0, 0))


# the calendar day (datetime.date) of a timestamp
def timestampToDay(timestamp):
    return datetime.fromtimestamp(timestamp, timezone.utc).date()


def today():
    return dayToTimestamp(date.today())


# "2015-03-21" for a timestamp, "" for None
def dateToText(timestamp):
    if timestamp is None:
        return ""
    return timestampToDay(timestamp).isoformat()


# Timestamp of "2015-03-21" or "21.03.2015", None for an empty text.
# Raises ValueError for anything else.
def textToDate(text):
    text = (text or "").strip()
    if not text:
        return None
    m = _ISO.match(text)
    if m:
        return dayToTimestamp(date(int(m.group(1)), int(m.group(2)), int(m.group(3))))
    m = _DMY.match(text)
    if m:
        return dayToTimestamp(date(int(m.group(3)), int(m.group(2)), int(m.group(1))))
    raise ValueError("kein Datum: " + text)


# "12.34" for 12.34, "12" for 12.0, "" for None
def numberToText(number):
    if number is None:
        return ""
    if isinstance(number, bool):
        return str(number)
    if isinstance(number, float):
        number = round(number, 6)
        if number == int(number):
            return str(int(number))
    return str(number)


# 12.34 for "12.34", "12,34" and "12'340.5"; None for an empty text.
# Raises ValueError for anything else.
def textToNumber(text):
    text = (text or "").strip().replace("'", "").replace("’", "")
    if not text:
        return None
    if "," in text and "." not in text:
        text = text.replace(",", ".")
    number = float(text)
    if number != number or number in (float("inf"), float("-inf")):
        raise ValueError("keine Zahl: " + text)
    return int(number) if number == int(number) and "." not in text else number


def textToInt(text):
    number = textToNumber(text)
    if number is None:
        return None
    if number != int(number):
        raise ValueError("keine ganze Zahl: " + str(text))
    return int(number)


# "0,0; 12000,0; 12000,6500" for [[0, 0], [12000, 0], [12000, 6500]]
def pointsToText(points):
    return "; ".join(", ".join(numberToText(v) for v in point) for point in points or [])


def textToPoints(text):
    points = []
    for part in (text or "").split(";"):
        if not part.strip():
            continue
        point = [textToNumber(v) for v in part.split(",")]
        if len(point) < 2 or None in point:
            raise ValueError("kein Punkt: " + part.strip())
        points.append(point)
    return points


# text of a value of a field type (ModelNode._types)
def toText(fieldType, value):
    if value is None:
        return ""
    if fieldType == "points":
        return pointsToText(value)
    if fieldType == "json":
        return json.dumps(value, indent=2, ensure_ascii=False) if value not in ({}, []) else ""
    if fieldType == "date":
        return dateToText(value)
    if fieldType in ("int", "number"):
        return numberToText(value)
    if fieldType == "list":
        return ", ".join(str(v) for v in value)
    return str(value)


# value of a field type from its text. Raises ValueError.
def fromText(fieldType, text):
    if fieldType == "date":
        return textToDate(text)
    if fieldType == "int":
        return textToInt(text)
    if fieldType == "number":
        return textToNumber(text)
    if fieldType == "list":
        return [part.strip() for part in (text or "").split(",") if part.strip()]
    if fieldType == "points":
        return textToPoints(text)
    if fieldType == "json":
        if not (text or "").strip():
            return None
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError("kein JSON: " + str(e))
    text = text or ""
    return text if text.strip() else None
