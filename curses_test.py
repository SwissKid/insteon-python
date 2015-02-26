#!/usr/bin/env python2
import curses, logging, threading
import insteon_api as insteon
from collections import deque

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

hilight = 0
mapping_list = []
lines = insteon.rooms["RoomList"]
def init_draw_list(lines):
	global mapping_list 
	line = 0
	for item in lines:
		mapping_list.append( { "Type" : "Room", "DeviceList" : item["DeviceList"] })
		line += 1
		for device_item in item["DeviceList"]:
			device = insteon.dev_search_id(device_item["DeviceID"])
			mapping_list.append( { "Type" : "Device", "DeviceID" : device_item["DeviceID"], "Status" : "Unknown" })
			line += 1
	return line, mapping_list
def get_dev_statuses(lines):
	global mapping_list
	line = 0
	for item in lines: 
		line += 1
		for device_item in item["DeviceList"]:
			device_status = insteon.dev_status(device_item["DeviceID"])
			device = insteon.dev_search_id(device_item["DeviceID"])
			mapping_list[line] = { "Type" : "Device", "DeviceID" : device_item["DeviceID"], "Status" : str(device_status) }
			draw_list(lines)
			stdscr.refresh()
			line += 1

	
def draw_list(lines):
	line = 0
	y = 2
	for item in lines:
		x = 4
		string = item["RoomName"]
		if line == hilight:
			stdscr.addstr(y, x, string, curses.A_REVERSE)
		else:
			stdscr.addstr(y, x, string)
		y += 1
		line += 1
		for device_item in item["DeviceList"]:
			x = 8
			device_thing = insteon.dev_search_id(device_item["DeviceID"])
			device = device_thing["DeviceName"]
			#mapping_list.append( { "Type" : "Device", "DeviceID" : device_item["DeviceID"] })
			if line >= len(mapping_list):
				logging.error( "What is wrong?")
				logging.error(mapping_list)
			elif line == hilight:
				if mapping_list[line]["Status"] == "Unknown":
					stdscr.addstr(y, x, device , curses.A_REVERSE)
				elif mapping_list[line]["Status"] == "0":
					stdscr.addstr(y, x, device, curses.color_pair(2))
				else:
					stdscr.addstr(y, x, device, curses.color_pair(4))
			else:
				if mapping_list[line]["Status"] == "Unknown":
					stdscr.addstr(y, x, device )
				elif mapping_list[line]["Status"] == "0":
					stdscr.addstr(y, x, device , curses.color_pair(1))
				else:
					stdscr.addstr(y, x, device, curses.color_pair(3))
			line += 1
			y += 1
def threaded_off(device_id):
	global mapping_list
	thread = threading.Thread(target=insteon.device_off, args=(device_id,))
	thread.start()
	mapping_list[hilight]["Status"] = "0"
	logging.error(mapping_list)
	draw_list(lines)	
	stdscr.refresh()
	return thread
def threaded_on(device_id):
	global mapping_list
	thread = threading.Thread(target=insteon.device_on, args=(device_id,))
	thread.start()
	mapping_list[hilight]["Status"] = "100"
	draw_list(lines)	
	stdscr.refresh()
	return thread
def threaded_status(lines):
	thread = threading.Thread(target=get_dev_statuses, args=(lines,))
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
	stdscr.clear()
	insteon.get_rooms()
	threads = deque([])
	stdscr.addstr(2,2, "Loading")
	stdscr.refresh()
	stdscr.erase()
	max_line, mapping_list = init_draw_list(lines)	
	threaded_status(lines)
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
			check_threads(threads)
			logging.error("O hit")
			logging.error("trying to turn on " )
			if mapping_list[hilight]["Type"] == "Device":
				threads.append(threaded_on(mapping_list[hilight]["DeviceID"]))
			elif mapping_list[hilight]["Type"] == "Room":
				for item in mapping_list[hilight]["DeviceList"]:
					threads.append(threaded_on(item["DeviceID"]))
					threaded_status(lines)
		elif key == "o":
			check_threads(threads)
			logging.error("o hit")
			logging.error("trying to turn off " )
			if mapping_list[hilight]["Type"] == "Device":
				threads.append(threaded_off(mapping_list[hilight]["DeviceID"]))
			elif mapping_list[hilight]["Type"] == "Room":
				for item in mapping_list[hilight]["DeviceList"]:
					threads.append(threaded_off(item["DeviceID"]))
					threaded_status(lines)
		elif key == "u" or key == "U": #Update!
			threaded_status(lines)
					
		elif key == "q":
			break
curses.wrapper(main)		
