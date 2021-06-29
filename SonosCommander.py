from os import listdir
from os.path import isfile, join
import socket

PATH = "./commands/"
COMMANDS = {}


def refreshCommands():
	global COMMANDS
	onlyfiles = [f for f in listdir(PATH) if isfile(join(PATH, f))]

	for file_name in onlyfiles:
		file = open(PATH + file_name, "r")
		COMMANDS[file_name.replace(".txt", "")] = file.read()
		file.close()

def getCommands():
	return COMMANDS.keys()

def sendHTTP(http, ip):
	s = socket.socket()
	s.connect((ip, 1400))
	s.send(bytes(http, "utf-8"))
	s.detach()


def sendCommand(command, params, ip):
	if command == "setvolume":
		params["cl"] = 321 + len(params["volume"])
	elif command == "playuri":
		params["cl"] = 1193 + len(params["uri"])
	elif command == "seektime":
		params["cl"] = 288 + len(params["time"])
	elif command == "seekqueue":
		params["cl"] = 288 + len(params["index"])
	elif command == "addplaylisttoqueue":
		params["cl"] = 1475 + len(params["title"])
	params["ip"] = ip

	data = COMMANDS[command].format(**params)
	return sendHTTP(data, ip)