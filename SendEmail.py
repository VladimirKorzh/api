#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'Alex Petrenko'

import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email import Encoders

class SendEmail():
    def __init__(self):
        self.username = "info@it4medicine.com"
        self.password = ""
        self.fromuser = "info@it4medicine.com"
        self.touser = "zayats.andrey@gmail.com, marketing@nurse-mobile.com"

    def send(self, msgbody="", msgtype="html", fromuser="", touser="", subject="Nurse mobile", attachment=""):
    # type = html or plant
        if fromuser == "":
            fromuser = self.fromuser
        if touser == "":
            touser = self.touser

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = fromuser
        msg['To'] = touser

        part1 = MIMEText(msgbody, msgtype)
        msg.attach(part1)

        if attachment:
            part2 = MIMEBase('application', "octet-stream")
            part2.set_payload(open(attachment, "rb").read())
            Encoders.encode_base64(part2)
            part2.add_header('Content-Disposition', 'attachment; filename="' + attachment + '"')
            msg.attach(part2)

        # Sending the mail
        server = smtplib.SMTP('smtp.gmail.com:587')
        server.starttls()
        server.login(self.username,self.password)
        server.sendmail(fromuser , touser, msg.as_string())
        server.quit()

if __name__ == '__main__':
    from HtmlPdfReport import HtmlPdfReport
    hpr = HtmlPdfReport()
    hpr.temp_pdf = "templates/attachment.pdf"
    hpr.header = "О Нас"
    hpr.content = "Мобильная Медсестра — полезное приложение, которое следит за твоим курсом лечения. Напомнит о приеме лекарств, сохранит историю болезни, свяжет с доктором, поликлиникой или лабораторией."
    hpr.footer = "Хочешь получить приложение первым? Заходи к нам!"
    hpr.gen_pdf()
    SendEmail().send(msgbody="<h2>Мобильная Медсестра — надежный помощник на вашем пути к выздоровлению</h2>", msgtype="html", subject="Report from Nurse Mobile", attachment="templates/attachment.pdf")
