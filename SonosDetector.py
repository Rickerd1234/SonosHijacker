import requests
import xmltodict
import nmap
import threading

nm = nmap.PortScanner()

def deviceScan(local_ip):
	results = nm.scan(hosts=local_ip+"/24", arguments="-sn")['scan']
	clients = []
	for data in results.values():
		addresses = data['addresses']
		if addresses["ipv4"] == local_ip:
			continue

		if len(data['vendor'].values()):
			vendor = list(data['vendor'].values())[0]
		else:
			vendor = "N/A"

		try:
			clients.append({'ip':addresses['ipv4'], 'mac':addresses['mac'], 'vendor':vendor})
		except KeyError:
			continue

	return clients

def updateDevices(local_ip, devices):
	results = nm.scan(hosts=local_ip+"/24", arguments="-sn")['scan']
	for data in results.values():
		addresses = data['addresses']
		if addresses["ipv4"] == local_ip:
			continue

		if len(data['vendor'].values()):
			vendor = list(data['vendor'].values())[0]
		else:
			vendor = "N/A"

		try:
			device = {'ip':addresses['ipv4'], 'mac':addresses['mac'], 'vendor':vendor}
		except KeyError:
			continue

		try:
			index = [dev['ip'] for dev in devices].index(device['ip'])
		except:
			index = -1

		if index > -1:
			devices[index] = device
		else:
			devices.append(device)
	devices.sort(key=lambda x: int(x["ip"].rsplit(".")[-1]))
	print("Updated Devices")

def threadedUpdateDevices(local_ip, devices):
	threading.Thread(target=updateDevices, args=[local_ip, devices]).start()

def printDevices(devices):
	# get devices and print results
	print("Available devices in the network:")
	print("INDEX    IP" + " "*18 + "MAC" + " "*18 + "VENDOR")
	for ind, client in enumerate(devices):
		print("{:5}    {:16}    {:17}    {}".format(ind, client['ip'], client['mac'], client['vendor']))


def getSonosIPs(devices):
	sonos_list = []
	for client in devices:
		if "sonos" in client['vendor'].lower():
			sonos_list += [client['ip']]
	return sonos_list

def printSonosDevices(sonos_list):
	print("Detected Sonos devices in the network:")
	print("IP" + " "*14)	
	for ip in sonos_list:
		print("{:16}".format(ip))


def getSpeakerInfo(ip):
	try:
		xml = requests.get("http://" + ip + ":1400/status/zp").content.decode("utf-8")
		return xmltodict.parse(xml)['ZPSupportInfo']['ZPInfo']
	except:
		return {"ZoneName": "Unknown Device"}

def getSonosInfo(ips):
	sonos_info = {}
	for ip in ips:
		sonos_info[ip] = getSpeakerInfo(ip)
	return sonos_info


def printSonosInfo(sonos_info):
	print("Detected Sonos devices in the network:")
	print("INDEX    IP" + " "*18 + "NAME")
	for ind, (ip, speaker_info) in enumerate(sonos_info.items()):
		print("{:5}    {:16}    {}".format(ind, ip, speaker_info['ZoneName']))