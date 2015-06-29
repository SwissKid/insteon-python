#!/usr/bin/env python2
import curses, logging, threading, time
import insteon_api as insteon
from collections import deque
#logging.basicConfig(level=logging.DEBUG)

stdscr = curses.initscr()

curses.noecho()
curses.cbreak()
curses.curs_set(0)
curses.start_color()
curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
curses.init_pair(2, curses.COLOR_RED, curses.COLOR_WHITE)
curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)
curses.init_pair(4, curses.COLOR_GREEN, curses.COLOR_WHITE)
stdscr.keypad(True)

check_time = 30
hilight = 0
mapping_list = []
remote_only_devcat = [0]
lines = []

def init_lines():
	global lines
	tobepopped = []
	pre_lines = insteon.rooms["RoomList"]
	for r_index,room in enumerate(pre_lines):
		for d_index,device in enumerate(room["DeviceList"]):
			device_info = insteon.dev_search_id(device["DeviceID"])
			if device_info["DevCat"] in remote_only_devcat:
				tobepopped.append((r_index,d_index))
			pre_lines[r_index]["DeviceList"][d_index] = device_info
	for poppers in tobepopped:
		pre_lines[poppers[0]]["DeviceList"].pop(poppers[1])
	lines = pre_lines
			
def init_draw_list():
	global mapping_list 
	line = 0
	mapping_list.append( {"Type": "Heading", "Name": "Rooms", "Status": "Heading"})
	for item in lines:
		mapping_list.append( { "Type" : "Room", "Name": item["RoomName"], "DeviceList" : item["DeviceList"], "Status": "None" })
		line += 1
		for device in item["DeviceList"]:
			mapping_list.append( { "Type" : "Device", "Name": device["DeviceName"], "DeviceID" : device["DeviceID"], "Status" : "Unknown" })
			line += 1
	mapping_list.append( {"Type": "Heading", "Name": "Scenes", "Status": "Heading"})
	for item in insteon.scenes["SceneList"]:
		mapping_list.append({ "Type" : "Scene", "Name": item["SceneName"], "SceneID": item["SceneID"], "Status": "None" })
	return mapping_list


def draw_list():
	line = 0
	y = 2
	for item in mapping_list:
		string = item["Name"]
		if item["Type"] in ["Heading"]:
			x = 4
		elif item["Type"] in [ "Room", "Scene"]:
			x = 6
		elif item["Type"] in [ "Device" ]:
			x = 8
		#if item["Type"] == "Heading":
		#	y+=1
		#	line += 1
		if line == hilight:
			if item["Status"].isdigit():
				if int(item["Status"]) > 0:
					stdscr.addstr(y, x, string, curses.color_pair(4))
				elif int(item["Status"]) == 0:
					stdscr.addstr(y, x, string, curses.color_pair(2))
			else:
				stdscr.addstr(y, x, string, curses.A_REVERSE)
		else:
			if item["Status"].isdigit():
				if int(item["Status"]) > 0:
					stdscr.addstr(y, x, string, curses.color_pair(3))
				elif int(item["Status"]) == 0:
					stdscr.addstr(y, x, string, curses.color_pair(1))
			else:
				stdscr.addstr(y, x, string )
		y += 1
		line += 1


def get_dev_statuses():
	line = 0
	for item in mapping_list: 
		if item["Type"] == "Device":
			logging.debug("Getting info for %s", item["Name"])
			device_status(item["DeviceID"], line)
		line += 1

def delay_status(device_id):
	line = hilight
	time.sleep(10)
	device_status(device_id,line)
	
def device_status(device_id, line):
	global mapping_list
	device_status = insteon.dev_status(device_id)
	mapping_list[line]["Status"] = str(device_status)
	draw_list()
	stdscr.refresh()

def check_clock():
	while True:
		get_dev_statuses()
		time.sleep(check_time)
	
	
	
def threaded_off(device_id):
	global mapping_list
	thread = threading.Thread(target=insteon.device_off, args=(device_id,))
	thread.daemon = True
	thread.start()
	mapping_list[hilight]["Status"] = "0"
	#logging.error(mapping_list)
	draw_list()	
	stdscr.refresh()
	thread2 = threading.Thread(target=delay_status, args=(device_id,))
	thread2.daemon = True
	thread2.start()
	return thread
def threaded_on(device_id):
	global mapping_list
	thread = threading.Thread(target=insteon.device_on, args=(device_id,))
	thread.daemon = True
	thread.start()
	mapping_list[hilight]["Status"] = "100"
	draw_list()	
	stdscr.refresh()
	thread2 = threading.Thread(target=delay_status, args=(device_id,))
	thread2.daemon = True
	thread2.start()
	return thread
def threaded_status(lines):
	thread = threading.Thread(target=get_dev_statuses)
	thread.daemon = True
	thread.start()
	return thread
def check_threads(threads):
	while True:
		if len(threads) == 0:
			break
		if threads[0].is_alive():
			break
		threads.popleft()	
def main(stdscr):
	global hilight, mapping_list
	init_lines()
	stdscr.clear()
	insteon.populate_rooms()
	threads = deque([])
	stdscr.addstr(2,2, "Loading")
	stdscr.refresh()
	stdscr.erase()
	mapping_list = init_draw_list()	
	max_line = len(mapping_list) - 1

	#Auto check the devices every so often
	thread = threading.Thread(target=check_clock, args=())
	thread.daemon = True
	thread.start()


	while True:
		draw_list()	
		stdscr.refresh()
		key = stdscr.getkey()
		if key == "KEY_UP":
			check_threads(threads)
			if hilight > 0:
				hilight -= 1
		elif key == "KEY_DOWN":
			check_threads(threads)
			if hilight < max_line:
				hilight += 1
		elif key == "O":
			#check_threads(threads)
			#logging.error("O hit")
			#logging.error("trying to turn on " )
			if mapping_list[hilight]["Type"] == "Device":
				threads.append(threaded_on(mapping_list[hilight]["DeviceID"]))
			elif mapping_list[hilight]["Type"] == "Room":
				for item in mapping_list[hilight]["DeviceList"]:
					threads.append(threaded_on(item["DeviceID"]))
					threaded_status(lines)
			elif mapping_list[hilight]["Type"] == "Scene":
				insteon.scene_on(mapping_list[hilight]["SceneID"])
		elif key == "o":
			check_threads(threads)
			#logging.error("o hit")
			#logging.error("trying to turn off " )
			if mapping_list[hilight]["Type"] == "Device":
				threads.append(threaded_off(mapping_list[hilight]["DeviceID"]))
			elif mapping_list[hilight]["Type"] == "Room":
				for item in mapping_list[hilight]["DeviceList"]:
					threads.append(threaded_off(item["DeviceID"]))
					threaded_status(lines)
			elif mapping_list[hilight]["Type"] == "Scene":
				insteon.scene_on(mapping_list[hilight]["SceneID"])
		elif key == "u" or key == "U": #Update!
			threaded_status(lines)
					
		elif key == "q":
			break
curses.wrapper(main)		
