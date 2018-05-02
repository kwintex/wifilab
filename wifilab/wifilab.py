#!/usr/bin/python
"""
Captive Portal for Wi-Fi Lab HBO-ICT
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, request
from helper import *
from sqlite_db import *

app = Flask(__name__)
app.config.from_object('config')


handler = RotatingFileHandler(app.config["LOG_FILE"], maxBytes=10000, backupCount=1)
handler.setLevel(logging.INFO)
handler.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s in %(module)s: %(message)s'))
app.logger.addHandler(handler)
app.logger.info("Python Version being used (major version number): %s",sys.version_info[0])

db=app.config['DATABASE']
init_db(db, app.config['DB_SCHEMA'], app.logger)

@app.errorhandler(404)
def page_not_found(e):
    # Catch all chained to index.html
    return home()


# index.html, home page
@app.route("/", methods = ['GET'])
def home():
    ip=request.remote_addr
    mac_address=mac_for_ip(ip, app.config['PLATFORM'])
    app.logger.info("Client connected with IP: %s and MAC: %s", ip, mac_address)
    return render_template('index.html', mac=mac_address)


# new request posted, check, insert in db + present code-form page
@app.route("/code/", methods = ['POST'])
def code_post():

    # Initialization
    success = True
    secret = generate_secret()
    res = request.form
    expiration = res['expiration']
    hu_email = res['hu_email']
    mac_address = str(res['mac_address']).upper()
    type_name = res['type_name']
    accept_conditions = res['accept_conditions']

    # Check information posted
    error = validate(mac_address=mac_address, hu_email=hu_email, expiration=expiration, type_name=type_name, accept_conditions=accept_conditions, conf=app.config)
    if error:
        success = False

    # Check current database, already active and not expired?
    res = query_db("""
        SELECT * FROM wifi_users 
        WHERE mac=? AND expiration_date > datetime('now', 'localtime') AND status='accepted'
    """, (mac_address,), one=True, db_file=db)
    if res:
        success=False
        error += "Het MAC-adres: "+mac_address+" wordt al geaccepteerd in dit netwerk. "

    # Check current database, already pending (less than 15 minutes ago)?
    res = query_db("""
        SELECT * FROM wifi_users 
        WHERE mac=? AND datetime(creation_date, '+15 Minute') > datetime('now', 'localtime') AND status='pending'
    """, (mac_address,), one=True, db_file=db)
    if res:
        success=False
        error += "Er is al een code voor het MAC-adres: "+mac_address+" verzonden. Probeer het evt. over 15 min. opnieuw. "

    # Show Secret-Template (and insert into database / send e-mail / create iptables rule) or Show Error-Template
    if success:
        if send_email(hu_email, mac_address, secret, conf=app.config):
            success=False
            error += "De e-mail naar: "+hu_email+" kon niet verzonden worden."
    if success:
        if expiration == "Onbeperkt":
            expiration_days = "7305" # 20 years
        else:
            expiration_days = "92" # 3 months
        query_db("""
            INSERT INTO wifi_users (mac, status, expiration_date, email, device, code) 
            VALUES (?,'pending', datetime('now', '+"""+expiration_days+""" Day'),?,?,?)
        """, (mac_address, hu_email, type_name, secret), one=True, db_file=db)
    if success:
        return render_template('code.html', mac = mac_address)
    else:
        return render_template('result_error.html', mac=mac_address, error = error)


# existing request, present code-form page
@app.route("/code/", methods = ['GET'])
def code_get():
    return render_template('code.html')


# succeeded or failed. Either way, present result to user
@app.route("/result/", methods = ['POST'])
def result():
    success = True
    error = "Onbekend."
    result = request.form
    secret = result['secret']
    mac_address = result['mac_address']
    expiration_date = ""
    device = ""

    nr = query_update_db("""
        UPDATE wifi_users SET status='accepted' 
        WHERE code=? AND mac=? AND datetime(creation_date, '+15 Minute') > datetime('now', 'localtime');
    """, (secret, mac_address), db_file=db)
    if nr !=1:
        success = False
        error = "Je code en/of MAC-adres werden niet (binnen een kwartier na uitgifte) gevonden in de database. "
    else:
        res = query_db("""
            SELECT expiration_date, device FROM wifi_users 
            WHERE mac=? AND expiration_date > datetime('now', 'localtime') AND status='accepted'
        """, (mac_address,), one=True, db_file=db)
        expiration_date = res[0]
        device = res[1]
        if create_iptables_rule(mac_address, app.logger, app.config['PLATFORM']):
            success=False
            error += "Voor het MAC-adres: "+mac_address+" kon geen nieuwe firewall regel worden aangemaakt."

    if success:
        return render_template('result_succes.html', mac=mac_address, expire=expiration_date[0:10], device=device)
    else:
        return render_template('result_error.html', mac=mac_address, error = error)

