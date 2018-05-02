#!/usr/bin/python
"""
This script has multiple modules:
- delete old "pending"-status entries in the database (creation_date older than 1 week)
- delete old "accepted" and "expired" entries in the database (older then 2 year)
- delete expired mac-addresses from iptables PREROUTING chain being part of the mangle table.
- send back-up of the database by mail if it is the first day of the month

Script should run every day using crontab with root capabilities:
cat << EOF >  /etc/cron.daily/iptable_maintenance
#!/bin/sh
/usr/bin/python /var/www/rootapp/bin/iptables_maintenance.py
EOF
chmod 755 /var/www/rootapp/bin/iptables_maintenance.py
chown root:root /var/www/rootapp/bin/iptables_maintenance.py
"""

import os
import sys
import re
from datetime import datetime
import sqlite3
import logging
import subprocess
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.encoders import encode_base64
from mimetypes import guess_type


if sys.platform == 'win32':
   sys.exit(1)

DATABASE="/var/www/rootapp/lab_captive_portal.db"
IPTABLES_ALTER="/var/www/rootapp/bin/add_mac_to_iptables.sh"
MAIL_TO="mymail@hu.nl"
MAIL_FROM=MAIL_TO
MAIL_SERVER="smtp.kpnmail.nl"
#MAIL_SERVER="smtp.hu.nl"
LOG_DIR= "/var/log/httpd/wifilab/"
LOG_FILE= LOG_DIR + "lab_maintenance.log"
DUMP_FILE= LOG_DIR + "daily_dump.sql"
ACTIVE_USERS_FILE= LOG_DIR + "daily_active_users.txt"

formatter = logging.Formatter('[%(asctime)s] %(levelname)s in %(module)s: %(message)s')
hdlr = logging.FileHandler(LOG_FILE)
hdlr.setFormatter(formatter)
logger = logging.getLogger('maintenance')
logger.addHandler(hdlr)
logger.setLevel(logging.INFO)
logger.info('Maintenance started.')

con=''
cur=''
if os.path.exists(DATABASE):
        con = sqlite3.connect(DATABASE)
        cur = con.cursor()
else:
    logger.warning('Database: '+DATABASE+' not found.')
    exit(1)

# delete old "pending"-status entries in the database (creation_date older than 1 week)
cur.execute("""DELETE FROM wifi_users WHERE status='pending' AND datetime(creation_date, '+7 Day') < datetime('now')""")
con.commit()
logger.info(str(cur.rowcount)+' rows deleted in database (old pending states)')


# delete old "expired" entries in the database (older then 2 year)
cur.execute("""DELETE FROM wifi_users WHERE datetime(expiration_date, '+2 Year') < datetime('now')""")
con.commit()
logger.info(str(cur.rowcount)+' rows deleted in database (old accepted, but expired states)')


# delete expired mac-addresses from iptables PREROUTING chain being part of the mangle table.
# set status="expired" if deletion succeeded
res = cur.execute("""
SELECT id, mac FROM wifi_users WHERE status='accepted' AND expiration_date < datetime('now')
""")
rows = res.fetchall()
logger.info(str(len(rows))+' accepted, but expired entries in the database.')
for row in rows:
    id = row[0]
    mac_address = re.sub(r'-',':', row[1])

    command = (IPTABLES_ALTER+' D').split()
    command.append(mac_address)
    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error = p.communicate()
    if p.returncode:
        logger.warning('MAC-address '+str(mac_address)+' with ID '+str(id)+' Could not be deleted (list: /usr/sbin/iptables -t mangle -L PREROUTING): '+str(error))
    else:
        cur.execute("""UPDATE wifi_users SET status='expired' WHERE id=?""",(id,))
        con.commit()
        logger.info('MAC-address '+str(mac_address)+' with ID '+str(id)+' was deleted from iptables. Status=expired')

con.close()

# send back-up of the database by mail if it is the first day of the month

# command = ("/usr/bin/sqlite3 "+DATABASE+" .dump > "+DUMP_FILE).split()
# print(command)
# p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
# output, error = p.communicate()
# if p.returncode:
#     logger.warning('SQLite3 dump could not be created'+str(error))
#
# command = ("/usr/bin/sqlite3 "+DATABASE+""" -header -column "SELECT mac,email,device FROM wifi_users WHERE status='accepted' AND expiration_date > datetime('now')" >  """+ACTIVE_USERS_FILE).split()
# print(command)
# p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
# output, error = p.communicate()
# if p.returncode:
#     logger.warning('SQLite3 active user file could not be created'+str(error))

today="{:%Y-%m-%d}".format(datetime.today())
first_of_month = "{:%Y-%m-%d}".format(datetime.today().replace(day=1))

if today == first_of_month:
    msg = MIMEMultipart()
    msg['Subject'] = "HBO-ICT Lab Wi-Fi - Reporting"
    msg['From'] = MAIL_FROM
    msg['To'] = MAIL_TO

    # Create the body of the message (a plain-text and an HTML version).
    text = "HBO-ICT Lab Wi-Fi - In de bijlagen de reporting van deze maand: "+first_of_month
    msg.preamble = text
    attachment = MIMEText(text)
    msg.attach(attachment)

    files=[ACTIVE_USERS_FILE,DUMP_FILE]
    for file in files:
        fp = open(file, 'rt')
        attachment = MIMEText(fp.read())
        fp.close()
        encode_base64(attachment)
        attachment.add_header('Content-Disposition', 'attachment', filename=os.path.basename(file))
        msg.attach(attachment)

    s = smtplib.SMTP(MAIL_SERVER)
    try:
        s.sendmail(MAIL_FROM, MAIL_TO, msg.as_string())
    except:
        logger.warning('Mail kon niet verzonden worden')
    s.quit()
