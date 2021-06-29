from SonosCommander import *
import multiprocessing as mp
import time


def runRoutine(targets, routine):
	steps = len(routine)
	
	if steps == 0:
		print("ERR: NO STEPS")
		return

	i = 0
	while True:
		command, params = routine[i]

		for ip, info in targets.items():
			params["uuid"] = info["LocalUID"]
			sendCommand(command, params, ip)

		i = (i + 1) % steps
		time.sleep(5/steps)


def startRoutine(targets, routine):
	process = mp.Process(target=runRoutine, args=[targets, routine])
	process.start()
	return process


def stopRoutine(process):
	process.terminate()

refreshCommands()