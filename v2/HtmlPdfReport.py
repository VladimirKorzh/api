#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'Alex Petrenko'

from tornado import template
import pdfkit

class HtmlPdfReport():
    def __init__(self):
        self.temp_dir = "templates"
        self.temp_html = "report.html"
        self.temp_pdf = "outfile.pdf"
        self.header = "Header"
        self.content = "Some text"
        self.footer = "Footer"

    def gen_html(self, header="", content="", footer=""):
        if header == "":
            header = self.header
        if content == "":
            content=self.content
        if footer == "":
            footer=self.footer

        loader = template.Loader(self.temp_dir)
        tempload = loader.load(self.temp_html)
        string = tempload.generate(content = content, header=header, footer=footer)
        result = string.decode('utf-8')
        return result

    def gen_pdf(self, type = "string", input_file = "", string = ""):

        if type == "file":
            with open(input_file, 'r') as f:
                result = f.read().decode('utf-8')
        if type == "string":
            if string:
                result = string
            else:
                result = self.gen_html()

        pdfkit.from_string(result, self.temp_pdf)

if __name__ == '__main__':
    hpr = HtmlPdfReport()
    hpr.header = "Ground control to Major TOM!"
    hpr.content = "Ground control to major Tom\nTake your protein pills and put your helmet on\n(Ten) Ground control (Nine) to major Tom (Eight)\n(Seven, six) Commencing countdown (Five), engines on (Four)\n(Three, two) Check ignition (One) and may god's love (Liftoff) be with you\nThis is ground control to major Tom, you've really made the grade\nAnd the papers want to know whose shirts you wear\nNow it's time to leave the capsule if you dare"
    hpr.footer = "Fuck you!"
    hpr.gen_pdf()
