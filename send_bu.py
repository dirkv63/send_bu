"""
Script to mail databases as attachment. This is used as Database backup mechanism.
Information from http://naelshiab.com/tutorial-send-email-python/
"""


import datetime
import logging
import platform
from lib import my_env
from lib import info_layer
from lib import ftp_handler
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

cfg = my_env.init_env("sendmail", __file__)
logging.info("Start application")
computer_name = platform.node()
sa = info_layer.SqlAlConn(cfg)
ftp = ftp_handler.ftp_handler(cfg)

msg = MIMEMultipart()

if my_env.is_prod(cfg):
    file_list = 'ProdFiles'
else:
    file_list = 'DevFiles'
dbs = cfg[file_list]
files = []
msg_arr = []
for k in dbs:
    fileToSend = cfg[file_list][k]
    with open(fileToSend, 'rb') as fp:
        fc = fp.read()
        if sa.file_update(k, fc):
            files.append(k)
            # Send file to FTP Server
            res = ftp.load_file(fileToSend, k + str(datetime.datetime.today().weekday()))
            msg_arr.append(res)

if len(files) == 0:
    subject = "No Backup Files!"
    body = "No files were updated.\nThere are no backup files today!\n"
elif len(files) == 1:
    subject = "1 Backup File: " + files[0]
    body = "One single backup file updated since last run.\n"
else:
    subject = "{c} Backup Files: {a}".format(c=len(files), a=", ".join(files))
    body = "{c} backup files updated since last run.\n".format(c=len(files))
subject = "{c} - {s}".format(c=computer_name, s=subject)

gmail_user = cfg['Mail']['gmail_user']
gmail_pwd = cfg['Mail']['gmail_pwd']
recipient = cfg['Mail']['recipient']

msg['Subject'] = subject
msg['From'] = gmail_user
msg['To'] = recipient
body = body + "\n".join(msg_arr)
msg.attach(MIMEText(body, 'plain'))

smtp_server = cfg['Mail']['smtp_server']
smtp_port = cfg['Mail']['smtp_port']

if cfg['Main']['sendOK'] == 'Yes':
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(gmail_user, gmail_pwd)
    text = msg.as_string()
    server.sendmail(gmail_user, recipient, text)
    logging.debug("Mail sent!")
    server.quit()
logging.info("End Application")
