'''
Created on Aug 14, 2016

@author: shanrandhawa
'''

from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE
from smtplib import SMTP_SSL
import textwrap

import appconfig


class EmailSendService():

    def __init__(self):
        self.smtp = SMTP_SSL()
        self.smtp.connect('smtp.gmail.com', 465)
        self.smtp.ehlo()

    def build_message(self, sender_email, recipient_emails, msg_body, subject, files=[], file_names={}, reply_to_email=None):

        msg_body = textwrap.fill(msg_body, 700)

        message = MIMEMultipart()
        message.attach(MIMEText(msg_body, 'html'))
        for fil in files:
            with open(fil.name) as f:
                message.attach(MIMEApplication(
                    f.read(),
                    Content_Disposition='attachment; filename="%s"' % file_names.get(f.name),
                    Name=file_names.get(f.name)
                ))

        message['From'] = sender_email
        message['Subject'] = subject
        message['To'] = COMMASPACE.join(recipient_emails)
        if reply_to_email:
            message.add_header('reply-to', reply_to_email)

        return message

    def send_email(self, message, sender_email, sender_password, recipient_emails, sender_email_name=None):

        self.smtp.login(sender_email, sender_password)
        self.smtp.sendmail(sender_email_name if sender_email_name else sender_email,
                           recipient_emails + [appconfig.BCC_EMAIL_ADDRESS], message.as_string())
        self.smtp.close()

