#!/usr/bin/env python2
import curses, logging, threading
import insteon_api as insteon
from collections import deque

stdscr = curses.initscr()

curses.noecho()
curses.cbreak()
curses.curs_set(0)
stdscr.keypad(True)

def draw_list(lines, hilight):
	line = 1
	y = 2
	mapping_list = []
	for item in lines:
		x = 4
		string = item["RoomName"]
		if line == hilight:
			stdscr.addstr(y, x, string, curses.A_REVERSE)
		else:
			stdscr.addstr(y, x, string)
		mapping_list.append( { "Type" : "Room", "DeviceList" : item["DeviceList"] })
		y += 1
		line += 1
		for device_item in item["DeviceList"]:
			x = 8
			device_thing = insteon.dev_search_id(device_item["DeviceID"])
			device = device_thing["DeviceName"]
			mapping_list.append( { "Type" : "Device", "DeviceID" : device_item["DeviceID"] })
			if line == hilight:
				stdscr.addstr(y, x, device, curses.A_REVERSE)
			else:
				stdscr.addstr(y, x, device)
			line += 1
			y += 1
	return y, mapping_list
def threaded_off(device_id):
	thread = threading.Thread(target=insteon.device_off, args=(device_id,))
	thread.start()
	return thread
def threaded_on(device_id):
	thread = threading.Thread(target=insteon.device_on, args=(device_id,))
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
	stdscr.clear()
	insteon.get_rooms()
	lines = insteon.rooms["RoomList"]
	threads = deque([])
	hilight = 1
	while True:
		max_line, mapping_list = draw_list(lines, hilight)	
		stdscr.refresh()
		key = stdscr.getkey()
		if key == "KEY_UP":
			check_threads(threads)
			if hilight > 1:
				hilight -= 1
		elif key == "KEY_DOWN":
			check_threads(threads)
			if hilight < max_line:
				hilight += 1
		elif key == "O":
			check_threads(threads)
			logging.error("O hit")
			selected = mapping_list[hilight - 1] 
			logging.error("trying to turn on " )
			logging.error(selected)
			if selected["Type"] == "Device":
				threads.append(threaded_on(selected["DeviceID"]))
			elif selected["Type"] == "Room":
				for item in selected["DeviceList"]:
					threads.append(threaded_on(item["DeviceID"]))
		elif key == "o":
			check_threads(threads)
			logging.error("o hit")
			selected = mapping_list[hilight - 1] 
			logging.error("trying to turn off " )
			logging.error(selected)
			if selected["Type"] == "Device":
				threads.append(threaded_off(selected["DeviceID"]))
			elif selected["Type"] == "Room":
				for item in selected["DeviceList"]:
					threads.append(threaded_off(item["DeviceID"]))
		elif key == "q":
			check_threads(threads)
			break
curses.wrapper(main)		
	
