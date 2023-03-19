#!/usr/bin/env python3
#-*- coding: utf-8 -*-

from os.path import dirname, join

from relatorio.templates.opendocument import Template

class Invoice:
    def __init__(self):
        self.id = "Hello my friend"
        self.text = "Hello again"

inv = Invoice()    

basic = Template(source='', filepath='template.odt')
basic_generated = basic.generate(o=inv).render()

f = open('output.odt', 'wb')
f.write(basic_generated.getvalue())
f.close()
