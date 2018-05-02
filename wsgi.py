# Programma te starten via wsgi.py

import sys
# let op in pycharm bij settings --> project interpreter --> show all (rechtsboven) --> show paths (rechtsonder)
# daar dit pad ook toevoegen!

if sys.platform == 'win32':
    sys.path.append('D:\\HU\labcommissie\\wireless_lab\\PyCharm-WirelessLab\\wifilab')
else:
    sys.path.append('/var/www/rootapp/wifilab')
    sys.path.append('/var/www/rootapp')

from wifilab import app as application
if __name__ == "__main__":
    application.run()

