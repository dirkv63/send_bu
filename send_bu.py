"""
Script to mail databases as attachment. This is used as Database backup mechanism.
Information from http://naelshiab.com/tutorial-send-email-python/
"""


import logging
import sys
from lib import my_env
from lib import info_layer
# Import smtplib for the actual sending function
import smtplib
# Import the email modules we'll need
from email.mime.multipart import MIMEMultipart
from email import encoders
from email.mime.text import MIMEText
from email.mime.base import MIMEBase

cfg = my_env.init_env("sendmail", __file__)
logging.info("Start application")
sa = info_layer.SqlAlConn(cfg)

msg = MIMEMultipart()

if my_env.is_prod(cfg):
    file_list = 'ProdFiles'
else:
    file_list = 'DevFiles'
dbs = cfg[file_list]
att = []
for k in dbs:
    fileToSend = cfg[file_list][k]
    with open(fileToSend, 'rb') as fp:
        fc = fp.read()
        if sa.file_update(k, fc):
            att.append(k)
            attachment = MIMEBase('application', 'octet-stream')
            attachment.set_payload(fc)
            encoders.encode_base64(attachment)
            attachment.add_header("Content-Disposition", "attachment", filename=k)
            msg.attach(attachment)
logging.debug("Found {c} attachments".format(c=len(att)))

if len(att) == 0:
    subject = "No Backup Files!"
    body = "No files were updated.\nThere are no backupfiles today!"
elif len(att) == 1:
    subject = "1 Backup File: " + att[0]
    body = "Please find attached the single backup file updated since last run."
else:
    subject = "{c} Backup Files: {a}".format(c=len(att), a=", ".join(att))
    body = "Attached are the {c} backup files updated since last run.".format(c=len(att))

gmail_user = cfg['Mail']['gmail_user']
gmail_pwd = cfg['Mail']['gmail_pwd']
recipient = cfg['Mail']['recipient']

msg['Subject'] = subject
msg['From'] = gmail_user
msg['To'] = recipient
body = body
msg.attach(MIMEText(body, 'plain'))

smtp_server = cfg['Mail']['smtp_server']
smtp_port = cfg['Mail']['smtp_port']

if cfg['Main']['sendOK'] == 'Yes':
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(gmail_user, gmail_pwd)
    text = msg.as_string()
    try:
        server.sendmail(gmail_user, recipient, text)
        logging.debug("Mail sent!")
    except:
        e = sys.exc_info()[1]
        ec = sys.exc_info()[0]
        logging.error("Something went wrong, Class: {c}, Message: {m}".format(c=ec, m=e))
        sys.exit()
    server.quit()
logging.info("End Application")
