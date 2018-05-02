# Flask configuration
# http://exploreflask.com/en/latest/configuration.html

import sys

# Don't forget to modify addresses in lab_form_helper.js
TRUSTED_MAIL_ADDRESSES = [
        "aaa@hu.nl",
        "bbb@hu.nl",
        "ccc@hu.nl",
]

#MAIL_SERVER = "smtp.hu.nl"
MAIL_SERVER = "smtp.kpnmail.nl"
MAIL_SENDER = "noreply@hu.nl"

if sys.platform == 'win32':
    LOG_FILE = "log\lab_captive_portal.log"
    DEBUG = True # Turns on debugging features in Flask
    DATABASE = "lab_captive_portal.db"
    DB_SCHEMA = "res\wifi_lab.sql"
    PLATFORM = "windows"
else:
    LOG_FILE = "/var/log/httpd/wifilab/lab_captive_portal.log"
    DATABASE = "./lab_captive_portal.db"
    DEBUG = False
    DB_SCHEMA = "./res/wifi_lab.sql"
    PLATFORM = "linux"
