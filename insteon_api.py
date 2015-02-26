#!/usr/bin/env python2
import urllib, urllib2, json, pickle
from secrets import API_Key, Client_Secret, Refresh_Token, account_name
account_filename = "accounts/" + account_name + ".pickle"
account_authorization = ""
account_houses = {}
house_data = {}
devices = {}
scenes = {}
rooms = {}
def token_request(data_list):
	opener = urllib2.build_opener()
	request = {'client_id' : API_Key}
	data_list.update(request)
	print data_list
	data_encoded = urllib.urlencode(data_list)	
	print data_encoded
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
	#print account_authorization
	save_account()

def general_get_request(endpoint):
	while True:
		opener = urllib2.build_opener()
		if account_authorization == "":
			refresh_bearer()
		headers = { 
			"Content-Type" : "application/json",
			"Authentication" : "APIKey " + API_Key,
			"Authorization" : "Bearer " + account_authorization
			}
		for item in headers:
			opener.addheaders.append((item , headers[item]))
		try:
			response = opener.open("https://connect.insteon.com/api/v2/" + endpoint)
		except urllib2.HTTPError, e:
			print e.code
			if e.code == 403 or e.code == 401:
				print e.read()
				refresh_token()
			elif e.code == 500:
				break
		else:
			content = response.read()
			dict_return = json.loads(content)
			return dict_return
			break
def account_list():
	return_dict = general_get_request("accounts")
	return return_dict

def get_house(house_id):
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

def populate_devices():
	global devices
	devices = general_get_request("devices?properties=all")
	save_account	

def save_account():
	with open(account_filename, 'w') as f:
		pickle.dump([account_authorization, account_houses, house_data, devices, rooms, scenes], f)

try:
	with open(account_filename) as f:
		account_authorization, account_houses, house_data, devices, rooms, scenes = pickle.load(f)
		print account_authorization, account_houses;
except:
	save_account()



#refresh_bearer()
#account_list()
#house_check()
populate_houses()
populate_devices()
