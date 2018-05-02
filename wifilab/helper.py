#!/usr/bin/python
import subprocess, re, random, string, smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def mac_for_ip(ip, platform):
    """Returns a MAC for a given IP, returns empty string if not found
    LINUX:      arp | grep '192.168.3.1' | awk '{print $3}'
    WINDOWS:    arp -a 192.168.2.222
    """
    if platform == 'win32':
        cmd = "arp -a "+ip
    else:
        cmd = "arp | grep '"+ip+"' | awk '{print $3}'"

    x = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    res = ''
    while True:
      line = x.stdout.readline()
      if line != b'':
        match = re.search('''([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})''', str(line))
        if match:
            res = match.group()
      else:
        break

    return re.sub(r':','-',res)


def generate_secret():
    """Generate Secret
    """
    secret = ''.join(random.choice('abcdefhjkmnprstwxz' + '23456789' + '+=#@$!*()') for _ in range(8))
    return secret


def validate(hu_email, mac_address, expiration, type_name, accept_conditions, conf):
    """Validate user input
    """
    error=""
    trusted_email_addresses = conf['TRUSTED_MAIL_ADDRESSES']

    # Allowed e-mail address?
    match = re.search('''(\@student\.|\@)hu\.nl$''', hu_email)
    if not match:
        error += "Het e-mailadres "+hu_email+" is geen geldig hu-email adres (<iets>@student.hu.nl | <iets>@hu.nl. "

    # Expiration allowed?
    if expiration == 'Onbeperkt' or expiration != '92': # only possible for a few people
        if hu_email not in trusted_email_addresses:
            error += "Het e-mailadres: "+hu_email+" mag geen expiratie waarde: '"+expiration+"' opgeven. "

    # Use Policy accepted?
    if accept_conditions != "on":
        error += "Voorwaarden zijn niet geaccepteerd. "

    # Name device not too long?
    if len(type_name) > 32:
        error += "Naam van het device is te lang (maximaal 32 karakters toegestaan). "

    # Is this a MAC-address?
    match = re.search('''^([0-9A-Fa-f]{2}[-]){5}([0-9A-Fa-f]{2})$''', mac_address)
    if not match:
        error += "Het MAC-adres "+mac_address+" is geen geldig MAC-adres. "

    return error


def send_email(hu_mail, mac_address, secret, conf):
    """Send mail to owner of MAC-address
    """
    error = False
    mail_server = conf['MAIL_SERVER']
    mail_sender = conf['MAIL_SENDER']

    # Create message container - the correct MIME type is multipart/alternative.
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "Toegangscode voor "+mac_address+" tot het HBO-ICT Lab Wi-Fi netwerk."
    msg['From'] = mail_sender
    msg['To'] = hu_mail

    # Create the body of the message (a plain-text and an HTML version).
    text = "Beste student of HU-medewerker,\n\n" \
           "Je hebt een code aangevraagd om toegang te krijgen tot het HBO-ICT Lab Wi-Fi netwerk.\n" \
           "De code voor toegang van het MAC-adres '"+mac_address+"' staat hieronder:\n\n"\
           +secret+"\n\nVeel Plezier!\nDe Labcommissie."
    html = """\
    <html>
      <head></head>
      <body>
        <p>Beste student of HU-medewerker,<br><br>
           Je hebt een code aangevraagd om toegang te krijgen tot het HBO-ICT Lab Wi-Fi netwerk.<br>
           De code voor toegang van het MAC-adres '"""+mac_address+"""' staat hieronder:<br><br>
           <h3 style="font-family:Courier; color:blue; margin-left:10px;">"""+secret+"""</h3>Veel Plezier!<br>De Labcommissie.<br>
        </p>
      </body>
    </html>
    """

    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')
    msg.attach(part1)
    msg.attach(part2)

    s = smtplib.SMTP(mail_server)
    try:
        s.sendmail(mail_sender, hu_mail, msg.as_string())
    except:
        error = True
    s.quit()

    return error


def create_iptables_rule(mac_address, log, platform):
    """Create new Firewall Rule using sudo
    """
    error = False

    match = re.search('''^([0-9A-Fa-f]{2}[-:]){5}([0-9A-Fa-f]{2})$''', mac_address)
    if not match:
        error = True
    else:
        res = match.group()
        mac_address = re.sub(r'-',':',res)
        mac_address.upper()
        command = 'sudo /var/www/rootapp/bin/add_mac_to_iptables.sh I'.split()
        command.append(mac_address)
        log.info("command to be executed: %s",str(command))
        if platform != 'win32':
            p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output, err = p.communicate()
            if p.returncode:
                error = True
                log.error("Could not create iptables rule:"+output+err)

    return error
