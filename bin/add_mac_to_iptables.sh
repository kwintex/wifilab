#!/usr/bin/bash
operation=$1
mac=$2

# sudo chown root:root /var/www/rootapp/bin/add_mac_to_iptables.sh
# sudo chmod 700 /var/www/rootapp/bin/add_mac_to_iptables.sh
# sudo visudo, add line:
# apache  ALL=(ALL) NOPASSWD: /var/www/rootapp/bin/add_mac_to_iptables.sh
#
# Script seems pretty strange, but using CentOS7 this is the only way that survives a reboot
#

if [ $# -eq 2 ]; then
    if [ "${operation}" == "I" ]; then
        /usr/bin/firewall-cmd --permanent --direct --passthrough ipv4 -I PREROUTING -t mangle -m mac --mac-source ${mac} -j MARK --set-mark 2
        /usr/bin/firewall-cmd --reload
    elif [ "${operation}" == "D" ]; then
        /usr/bin/firewall-cmd --permanent --direct --remove-passthrough ipv4 -I PREROUTING -t mangle -m mac --mac-source ${mac} -j MARK --set-mark 2
        /usr/bin/firewall-cmd --direct --passthrough ipv4 -D PREROUTING -t mangle -m mac --mac-source ${mac} -j MARK --set-mark 2
        systemctl restart firewalld
    else
        echo usage: $0 "<[I|D] <mac-address>"
        exit 1
    fi
else
    echo usage: $0 "<[I|D] <mac-address>"
    echo example: $0 I 00:0c:29:12:d0:c3 \(to add this mac-address to the beginning of the chain\).
    echo example: $0 D 00:0c:29:12:d0:c3 \(to delete this mac-address from the chain\).
    exit 1
fi
