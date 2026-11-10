#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import unittest
from datetime import date

from model.ModelNode import ModelNode
from model import values


class Wheel(ModelNode):
    def __init__(self, top):
        self._top = top
        self.id = None
        self.size = None


class Engine(ModelNode):
    def __init__(self, top):
        self._top = top
        self.power = None


class Car(ModelNode):
    _parts = {"wheels": Wheel}
    _types = {"built": "date", "weight": "number"}
    _always = ("wheels",)

    def __init__(self, top):
        self._top = top
        self.name = None
        self.built = None
        self.weight = None
        self.engine = Engine(top)
        self.wheels = []
        self.ext = {}


class ModelNodeTest(unittest.TestCase):

    def test_roundtrip(self):
        data = {"name": "A", "built": 1426939200, "engine": {"power": 55},
                "wheels": [{"id": "1", "size": 15}, {"id": "2", "size": 16}]}
        car = Car(None)
        car.fromDict(data)
        self.assertIsInstance(car.wheels[1], Wheel)
        self.assertEqual(car.wheels[1].size, 16)
        self.assertEqual(car.engine.power, 55)
        self.assertEqual(car.toDict(), data)

    def test_unknown_fields_are_kept(self):
        data = {"name": "A", "colour": "red", "wheels": [{"id": "1", "tyre": {"brand": "X"}}],
                "engine": {"power": 55, "turbo": True}, "ext": {"some.plugin": {"v": 1, "x": [1, 2]}}}
        car = Car(None)
        car.fromDict(data)
        self.assertEqual(car.toDict(), data)
        self.assertEqual(car.get("colour"), "red")

    def test_empty_values_are_left_out(self):
        car = Car(None)
        self.assertEqual(car.toDict(), {"wheels": []})
        car.fromDict({"name": None, "wheels": [], "engine": None})
        self.assertEqual(car.toDict(), {"wheels": []})

    def test_get_set(self):
        car = Car(None)
        car.set("name", "B")
        car.set("from", 5)
        self.assertEqual(car.name, "B")
        self.assertEqual(car.get("from"), 5)
        self.assertEqual(car.toDict(), {"name": "B", "from": 5, "wheels": []})
        car.set("from", None)
        self.assertEqual(car.toDict(), {"name": "B", "wheels": []})

    def test_parts(self):
        car = Car(None)
        wheel = car.addPart("wheels", size=17)
        self.assertEqual(len(wheel.id), 36)
        self.assertIs(wheel._top, car)
        self.assertIs(wheel._parent, car)
        self.assertTrue(car.removePart(wheel))
        self.assertEqual(car.wheels, [])

    def test_link(self):
        car = Car(None)
        car.fromDict({"wheels": [{"id": "1"}]})
        car.link(car)
        self.assertIs(car.wheels[0]._top, car)
        self.assertIs(car.engine._parent, car)

    def test_field_type(self):
        car = Car(None)
        self.assertEqual(car.fieldType("built"), "date")
        self.assertEqual(car.fieldType("name"), "text")


class ValuesTest(unittest.TestCase):

    def test_dates(self):
        # the examples of doc/file_format.md
        self.assertEqual(values.dayToTimestamp(date(2026, 11, 10)), 1794312000)
        self.assertEqual(values.textToDate("2015-03-21"), 1426939200)
        self.assertEqual(values.textToDate("21.03.2015"), 1426939200)
        self.assertEqual(values.dateToText(1426939200), "2015-03-21")
        self.assertIsNone(values.textToDate(" "))
        self.assertEqual(values.dateToText(None), "")
        for text in ("2021", "other", "2022-09-27/2023-06-28", "2015-13-01"):
            with self.assertRaises(ValueError):
                values.textToDate(text)

    def test_numbers(self):
        self.assertEqual(values.textToNumber("12,34"), 12.34)
        self.assertEqual(values.textToNumber(" 12.34 "), 12.34)
        self.assertEqual(values.textToNumber("18'450.50"), 18450.5)
        self.assertEqual(values.textToNumber("40"), 40)
        self.assertIsInstance(values.textToNumber("40"), int)
        self.assertIsNone(values.textToNumber(""))
        self.assertEqual(values.numberToText(12.0), "12")
        self.assertEqual(values.numberToText(10.56), "10.56")
        self.assertEqual(values.numberToText(None), "")
        with self.assertRaises(ValueError):
            values.textToNumber("abc")

    def test_field_types(self):
        self.assertEqual(values.fromText("date", "2015-03-21"), 1426939200)
        self.assertEqual(values.fromText("int", "3"), 3)
        self.assertEqual(values.fromText("list", "L1, L2,L3"), ["L1", "L2", "L3"])
        self.assertEqual(values.toText("list", ["N", "PE"]), "N, PE")
        self.assertIsNone(values.fromText("text", ""))
        with self.assertRaises(ValueError):
            values.fromText("int", "3.5")


if __name__ == "__main__":
    unittest.main()
