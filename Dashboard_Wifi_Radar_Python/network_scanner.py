from scapy.all import ARP, Ether, srp
import socket

def scan_network(ip_range="192.168.1.0/24"):
    devices = []

    arp = ARP(pdst=ip_range)
    ether = Ether(dst="ff:ff:ff:ff:ff:ff")
    packet = ether / arp

    result = srp(packet, timeout=2, verbose=False)[0]

    for sent, received in result:
        try:
            name = socket.gethostbyaddr(received.psrc)[0]
        except:
            name = "Desconocido"

        last_octet = int(received.psrc.split(".")[-1])

        # Distancia estimada (solo demostración)
        distance = round((last_octet / 254) * 30, 2)  # metros aprox

        devices.append({
            "ip": received.psrc,
            "mac": received.hwsrc,
            "name": name,
            "distance": distance,
            "zone": "Norte" if last_octet % 2 == 0 else "Sur"
        })

    return devices
