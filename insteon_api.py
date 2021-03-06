#!/usr/bin/env python2
import os, urllib, urllib2, json, pickle, logging
from secrets import API_Key, Client_Secret, Refresh_Token, account_name
account_filename = os.environ["HOME"]+ "/.local/share/insteon-python/accounts/" + account_name + ".pickle"

account_authorization = ""
account_houses = {}
house_data = {}
devices = {}
scenes = {}
rooms = {}
dev_categories = []
def token_request(data_list):
	opener = urllib2.build_opener()
	request = {'client_id' : API_Key}
	data_list.update(request)
	#print data_list
	data_encoded = urllib.urlencode(data_list)	
	#print data_encoded
	response = opener.open("https://connect.insteon.com/api/v2/oauth2/token", data_encoded)
	content = response.read()
	dict_return = json.loads(content)
	return dict_return

def refresh_bearer(): 
	global account_authorization
	data_list = {
		'refresh_token' : Refresh_Token,
		'grant_type' : 'refresh_token'}
	response = token_request(data_list)
	account_authorization = response["access_token"]
	logging.debug(account_authorization)
	save_account()

def general_get_request(endpoint):
	while True:
		#opener = urllib2.build_opener()
		if account_authorization == "":
			refresh_bearer()
		#for item in headers:
			#opener.addheaders.append((item , headers[item]))
		try:
			headers = { 
				"Content-Type" : "application/json",
				"Authentication" : "APIKey " + API_Key,
				"Authorization" : "Bearer " + account_authorization
				}
			request = urllib2.Request(url = "https://connect.insteon.com/api/v2/" + endpoint,  headers = headers)
			response = urllib2.urlopen(request)
		except urllib2.HTTPError, e:
			logging.error(e.code)
			if e.code == 403 or e.code == 401:
				logging.error( e.read())
				refresh_bearer()
			elif e.code == 500:
				break
		else:
			content = response.read()
			dict_return = json.loads(content)
			return dict_return
			break
#I think their accounts endpoint is extra broke
def account_list():
	return_dict = general_get_request("accounts")
	return return_dict

#Houses Endpoint	
def get_house(house_id1):
        global rooms, devices, scenes
        house_id = str(house_id1)
	basic_info = general_get_request("houses/" + house_id)
	rooms = general_get_request("houses/" + house_id + "/rooms")
	devices = general_get_request("houses/" + house_id + "/devices")
	scenes = general_get_request("houses/" + house_id + "/scenes")
	new_dict = { 
		"basic" : basic_info,
		"rooms" : rooms,
		"devices" : devices,
		"scenes" : scenes
		}
	return new_dict
	
def get_houses():
	return_dict = general_get_request("houses")
	return return_dict
	
def house_check():
	global account_houses
	account_houses = get_houses()
	save_account()

def populate_houses():
	global house_data
	if account_houses == {}:
		house_check()
	for item in account_houses['HouseList']:
		house_id = str(item['HouseID'])
		house_data[house_id] = get_house(house_id)
		house_data[house_id]['Name'] = item['HouseName']
	save_account()
def populate_all():
        if len(account_houses['HouseList']) == 1:
            get_house(account_houses['HouseList'][0]['HouseID'])
	populate_rooms()
	populate_devices()

#Devices Endpoint
def populate_devices():
	global devices
	devices = general_get_request("devices?properties=all")
	for index,device in enumerate(devices["DeviceList"]):
		for category in dev_categories:
			if device["DevCat"] == int(category["Device Category"],16) and device["SubCat"] == int(category["Device Sub-Category"],16):
				devices["DeviceList"][index]["DeviceTypeName"]=category["Name"]
				devices["DeviceList"][index]["SKU"]=category["SKU"]
				break
	save_account()



			
def device_command(device_id, command_string, data_list={}):
	#opener = urllib2.build_opener()
	if account_authorization == "":
		refresh_bearer()
	headers = { 
		"Content-Type" : "application/json",
		"Authentication" : "APIKey " + API_Key,
		"Authorization" : "Bearer " + account_authorization
		}
	#for item in headers:
	#	opener.addheaders.append((item , headers[item]))
	request = {
		'device_id' : device_id,
		'command': command_string
		  }
	data_list.update(request)
	data_encoded = urllib.urlencode(data_list)	
	loop = True
	while True:
		try:
			request = urllib2.Request("https://connect.insteon.com/api/v2/commands", data = json.dumps(data_list), headers = headers)
			response = urllib2.urlopen(request)
		except urllib2.HTTPError, e:
			logging.error( e.code)
			logging.error( e.read())
			if e.code == 403 or e.code == 401:
				print e.read()
				refresh_bearer()
				continue
			break
		break
	if response:
		content = response.read()
		dict_return = json.loads(content)
		command_id = dict_return["id"]
	while True:
		command_return = general_get_request("commands/" + str(command_id))
		status = command_return["status"]
		if "succeeded" in status:
			break
		#print "WHY IS IT WRONG: " + status + "!!!!!"


	#print command_return
	return command_return["response"]

def dev_status(device_id):
	dict_return = device_command(device_id, "get_status")
	#print dict_return
	if dict_return["level"] == 100:
		device_status = "On"
	elif dict_return["level"] == 0:
		device_status = "Off"
	else:
		device_status = str(dict_return["level"]) + "% On"
	#print device_status
	return dict_return["level"]

##Test thing to see about the status of each device:
def list_device_status():
	if devices == {}:
		populate_devices()
	for item in devices["DeviceList"]:
		#Check if it's a multi-device device (like keypads and outlets)
		name = item["DeviceName"]
		device_id = item["DeviceID"]
		#if item["GroupList"] == []:
		print name
		dev_status(device_id)
			#print "balls"
			
	#	else:
	#		#device is not that, the ones i know about are keypads and outlets
	#		print name + " is not a device we are checking"
	#		device_item = ""
	#		category = hex(item["DevCat"])
	#		subcategory = hex(item["SubCat"])
	#		for device_item in dev_categories: 
	#			if category in device_item['Device Sub-Category'] and subcategory in device_item['Device Sub-Category']:
	#				device = device_item
	#		if device_item['SKU'] == "2663-222": #On Off Outlet
	#			print "on/off outlet"

def device_off(device_id):
	device_command(device_id, "off")
def device_on(device_id, level=0):
	if level == 0:
		for device in devices["DeviceList"]:
			if device_id == device["DeviceID"]:
				#print "Finding level"
				if "DimLevel" in device:
					prelevel = device["DimLevel"]
					level  = (( prelevel + 1) * 100 )/ 255
				else:
					level = 100
	if level < 10: #It doesn't work correctly under 10. Who knows why....
		level = 10
	device_command(device_id, "on", {"level": level })

def dev_search_id(device_id):
	for device in devices["DeviceList"]:
		if device_id == device["DeviceID"]:
			return device


#Room Endpoint
def populate_rooms():
	global rooms
	rooms = general_get_request("rooms?properties=all")
	save_account()

def room_listing():
	for item in rooms["RoomList"]:
		print item["RoomName"]
		for item2 in item["DeviceList"]:
			device = dev_search_id(item2["DeviceID"])
			print "\t" + device["DeviceName"]

#def room_off(room_id):
#	for item in rooms["RoomList"]:
#		if item["RoomID"] == room_id:
#			for device in item["DeviceList"]:
#				device_off(device["DeviceID"])
#
#def room_on(room_id):
#	for item in rooms["RoomList"]:
#		if item["RoomID"] == room_id:
#			for device in item["DeviceList"]:
#				device_on(device["DeviceID"])
	
#Scenes Endpoint
def populate_scenes():
	global scenes
	scenes = general_get_request("scenes?properties=all")
	save_account()
def scene_listing():
	for item in scenes["SceneList"]:
		print item["SceneName"]
		for item2 in item["DeviceList"]:
			device = dev_search_id(item2["DeviceID"])
			print "\t" + device["DeviceName"]
def scene_command(scene_id, command_string, data_list={}):
	#opener = urllib2.build_opener()
	if account_authorization == "":
		refresh_bearer()
	headers = { 
		"Content-Type" : "application/json",
		"Authentication" : "APIKey " + API_Key,
		"Authorization" : "Bearer " + account_authorization
		}
	#for item in headers:
	#	opener.addheaders.append((item , headers[item]))
	request = {
		'scene_id' : scene_id,
		'command': command_string
		  }
	data_list.update(request)
	data_encoded = urllib.urlencode(data_list)	
	loop = True
	while True:
		try:
			request = urllib2.Request("https://connect.insteon.com/api/v2/commands", data = json.dumps(data_list), headers = headers)
			response = urllib2.urlopen(request)
		except urllib2.HTTPError, e:
			logging.error( e.code)
			logging.error( e.read())
			if e.code == 403 or e.code == 401:
				print e.read()
				refresh_bearer()
			continue
		break
	content = response.read()
	dict_return = json.loads(content)
	command_id = dict_return["id"]
	while True:
		command_return = general_get_request("commands/" + str(command_id))
		status = command_return["status"]
		if "succeeded" in status:
			break
		#print "WHY IS IT WRONG: " + status + "!!!!!"


	#print command_return
	return command_return["status"]
def scene_off(scene_id):
	scene_command(scene_id, "off")
def scene_on(scene_id, level=0):
	scene_command(scene_id, "on")


##Dealing with the files
def save_account():
	with open(account_filename, 'w') as f:
		pickle.dump([account_authorization, account_houses, house_data, devices, rooms, scenes], f)

try:
	with open(account_filename) as f:
		account_authorization, account_houses, house_data, devices, rooms, scenes = pickle.load(f)
		#print account_authorization, account_houses;
except:
        populate_houses()
        populate_all()
        save_account()

try: 
	with open('device_categories.json') as data_file:
		data = json.load(data_file)
		dev_categories = data['Device Category List']
except:
	with open(os.environ["HOME"] + '/.local/insteon-python/device_categories.json') as data_file:
		data = json.load(data_file)
		dev_categories = data['Device Category List']



#refresh_bearer()
#account_list()
#house_check()
#populate_houses()
#populate_devices()
#house_check()
#list_device_status()

#for device in devices["DeviceList"]:
#	if "Bedroom Lamp" in device["DeviceName"]:
#		device_on(device["DeviceID"], 5)
#get_scenes()
#scene_listing()
# vim: set shiftwidth=4 : #
