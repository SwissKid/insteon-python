#!/usr/bin/env python2
import curses, logging, threading, time
import insteon_api as insteon
from collections import deque
##Set logging level
logging.basicConfig(level=logging.DEBUG)

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
	pre_lines = insteon.scenes["SceneList"]
	#for s_index,scene in enumerate(pre_lines):
	#	for d_index,device in enumerate(scene["DeviceList"]):
	#		device_info = insteon.dev_search_id(device["DeviceID"])
	#		if device_info["DevCat"] in remote_only_devcat:
	#			tobepopped.append((s_index,d_index))
	#		pre_lines[s_index]["DeviceList"][d_index] = device_info
	#for poppers in tobepopped:
	#	pre_lines[poppers[0]]["DeviceList"].pop(poppers[1])
	lines = pre_lines
			
def init_draw_list(lines):
	global mapping_list 
	line = 0
	for item in lines:
		mapping_list.append( { "Type" : "Scene", "SceneID": item["SceneID"], "DeviceList" : item["DeviceList"] })
		line += 1
#		for device in item["DeviceList"]:
#			mapping_list.append( { "Type" : "Device", "DeviceID" : device["DeviceID"], "Status" : "Unknown" })
#			line += 1
	return line - 1, mapping_list


def draw_list(lines):
	line = 0
	y = 2
	for item in lines:
		x = 4
		string = item["SceneName"]
		if line == hilight:
			stdscr.addstr(y, x, string, curses.A_REVERSE)
		else:
			stdscr.addstr(y, x, string)
		y += 1
		line += 1
#		for device_item in item["DeviceList"]:
#			x = 8
#			device = device_item["DeviceName"]
#			if line >= len(mapping_list):
#				logging.error( "What is wrong?")
#				logging.error(mapping_list)
#			elif line == hilight:
#				if mapping_list[line]["Status"] == "Unknown":
#					stdscr.addstr(y, x, device , curses.A_REVERSE)
#				elif mapping_list[line]["Status"] == "0":
#					stdscr.addstr(y, x, device, curses.color_pair(2))
#				else:
#					stdscr.addstr(y, x, device, curses.color_pair(4))
#			else:
#				if mapping_list[line]["Status"] == "Unknown":
#					logging.error("Y is %s, X is %s, and device is %s", y, x, device)
#					stdscr.addstr(y, x, device )
#				elif mapping_list[line]["Status"] == "0":
#					stdscr.addstr(y, x, device , curses.color_pair(1))
#				else:
#					stdscr.addstr(y, x, device, curses.color_pair(3))
#			line += 1
#			y += 1


def get_dev_statuses(lines):
	line = 0
	for item in lines: 
		line += 1
		for device_item in item["DeviceList"]:
			device_status(device_item["DeviceID"], line)
			line += 1

def delay_status(device_item):
	global mapping_list
	line = hilight
	time.sleep(10)
	device_status(device_item,line)
	
def device_status(device_id, line):
	global mapping_list
	device_status = insteon.dev_status(device_id)
	mapping_list[line] = { "Type" : "Device", "DeviceID" : device_id, "Status" : str(device_status) }
	draw_list(lines)
	stdscr.refresh()

def check_clock():
	while True:
		get_dev_statuses(lines)
		time.sleep(check_time)
	
	
	
def threaded_off(device_id):
	global mapping_list
	thread = threading.Thread(target=insteon.device_off, args=(device_id,))
	thread.daemon = True
	thread.start()
	mapping_list[hilight]["Status"] = "0"
	#logging.error(mapping_list)
	draw_list(lines)	
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
	draw_list(lines)	
	stdscr.refresh()
	thread2 = threading.Thread(target=delay_status, args=(device_id,))
	thread2.daemon = True
	thread2.start()
	return thread
def threaded_status(lines):
	thread = threading.Thread(target=get_dev_statuses, args=(lines,))
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
	insteon.populate_scenes()
	threads = deque([])
	stdscr.addstr(2,2, "Loading")
	stdscr.refresh()
	stdscr.erase()
	max_line, mapping_list = init_draw_list(lines)	

	#Auto check the devices every so often
	#thread = threading.Thread(target=check_clock, args=())
	#thread.daemon = True
	#thread.start()


	while True:
		draw_list(lines)	
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
				#threads.append(threaded_on(mapping_list[hilight]["DeviceID"]))
				continue
			elif mapping_list[hilight]["Type"] == "Scene":
				logging.error("Turning off scene which is ID %s", mapping_list[hilight]["SceneID"])
				insteon.scene_on(mapping_list[hilight]["SceneID"])
				#for item in mapping_list[hilight]["DeviceList"]:
				#	threads.append(threaded_on(item["DeviceID"]))
				#	threaded_status(lines)
		elif key == "o":
			check_threads(threads)
			#logging.error("o hit")
			#logging.error("trying to turn off " )
			if mapping_list[hilight]["Type"] == "Device":
				#threads.append(threaded_off(mapping_list[hilight]["DeviceID"]))
				continue
			elif mapping_list[hilight]["Type"] == "Scene":
				#threads.append(insteon.scene_off(mapping_list[hilight]["SceneID"]))
				insteon.scene_off(mapping_list[hilight]["SceneID"])
				#for item in mapping_list[hilight]["DeviceList"]:
				#	threads.append(threaded_off(item["DeviceID"]))
				#	threaded_status(lines)
		elif key == "u" or key == "U": #Update!
			threaded_status(lines)
					
		elif key == "q":
			break
curses.wrapper(main)		
