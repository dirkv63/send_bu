"""
Script to mail databases as attachment. This is used as Database backup mechanism.
Information from http://naelshiab.com/tutorial-send-email-python/
Converted to script to send backups to pcloud.
"""


import datetime
import logging
import os
import platform
import zipfile
from lib import my_env
from lib import info_layer
from lib import pcloud_handler
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

cfg = my_env.init_env("sendmail", __file__)
logging.info("Start application")
computer_name = platform.node()
sa = info_layer.SqlAlConn(cfg)
pc = pcloud_handler.PcloudHandler(cfg)

msg = MIMEMultipart()

if my_env.is_prod(cfg):
    file_list = 'ProdFiles'
else:
    file_list = 'DevFiles'
dbs = cfg[file_list]
files = []
msg_arr = []
zipdir = cfg["Main"]["zipdir"]
for k in dbs:
    fileToSend = cfg[file_list][k]
    try:
        with open(fileToSend, 'rb') as fp:
            fc = fp.read()
            if sa.file_update(k, fc):
                # zip file before sending
                zipfn = k + str(datetime.datetime.today().weekday())
                zipffp = os.path.join(zipdir, zipfn)
                (fp, fn) = os.path.split(fileToSend)
                # Change Dir to file directory, otherwise zip includes full path to the file.
                os.chdir(fp)
                try:
                    zipf = zipfile.ZipFile(zipffp, 'w', zipfile.ZIP_DEFLATED)
                    zipf.write(fn)
                    zipf.close()
                    files.append(k)
                    # Send file to Cloud Server
                    res = pc.upload(zipffp)
                except PermissionError:
                    res = "Permission denied on {fn}".format(fn=fileToSend)
                    logging.error(res)
                    sa.file_remove(k)
                msg_arr.append(res)
    except FileNotFoundError:
        logmsg = "Cannot find file {fts} for evaluation".format(fts=fileToSend)
        msg_arr.append(logmsg)
        logging.error(logmsg)
pc.logout()

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
