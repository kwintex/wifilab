#!/bin/sh
/usr/bin/sqlite3 /var/www/rootapp/lab_captive_portal.db .dump > /var/log/httpd/wifilab/daily_dump.sql
/usr/bin/sqlite3 /var/www/rootapp/lab_captive_portal.db -header -column "SELECT mac,email,device FROM wifi_users WHERE status='accepted' AND expiration_date > datetime('now')" > /var/log/httpd/wifilab/daily_active_users.txt

