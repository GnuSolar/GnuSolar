#!/usr/bin/python3

from selenium import webdriver
browser = webdriver.Firefox()

browser.get("https://www.ag.ch/app/aem/forms/getForm?formId=81d9b9ac-c457-46c2-9ff7-11fe25d19633&mode=prod")

element = browser.find_element("name", "Name_B_14")
element.send_keys("Hello")


element = browser.find_element("name", "Standortidentisch_L_27")
element.click()

element = browser.find_element("name", "Bauzone_J_N_57")
element.click()
