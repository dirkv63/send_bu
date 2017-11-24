"""
Script to mail databases as attachment. This is used as Database backup mechanism.
Information from http://naelshiab.com/tutorial-send-email-python/
"""


import logging
import sys
from lib import my_env

# Import smtplib for the actual sending function
import smtplib
# Import the email modules we'll need
from email.mime.multipart import MIMEMultipart
from email import encoders
from email.mime.text import MIMEText
from email.mime.base import MIMEBase

cfg = my_env.init_env("sendmail", __file__)
logging.info("Start application")

gmail_user = cfg['Mail']['gmail_user']
gmail_pwd = cfg['Mail']['gmail_pwd']
recipient = cfg['Mail']['recipient']
msg = MIMEMultipart()
msg['Subject'] = 'Backup Files'
msg['From'] = gmail_user
msg['To'] = recipient
body = 'Hi there,\nAttached are the backup files...'
msg.attach(MIMEText(body, 'plain'))

if my_env.is_prod(cfg):
    db_list = 'ProdDB'
else:
    db_list = 'DevDB'
dbs = cfg[db_list]
for k in dbs:
    fileToSend = cfg[db_list][k]
    fp = open(fileToSend, 'rb')
    attachment = MIMEBase('application', 'octet-stream')
    attachment.set_payload(fp.read())
    fp.close()
    encoders.encode_base64(attachment)
    attachment.add_header("Content-Disposition", "attachment", filename=k)
    msg.attach(attachment)

smtp_server = cfg['Mail']['smtp_server']
smtp_port = cfg['Mail']['smtp_port']
server = smtplib.SMTP(smtp_server, smtp_port)
server.starttls()
server.login(gmail_user, gmail_pwd)
text = msg.as_string() 
try:
    server.sendmail(gmail_user, recipient, text)
    print("Mail sent!")
except:
    e = sys.exc_info()[1] 
    ec = sys.exc_info()[0] 
    print("Something went wrong, Class: {c}, Message: {m}".format(c=ec, m=e))
    sys.exit()
server.quit()
