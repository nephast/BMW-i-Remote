#! /usr/bin/env python
#
# Use the BMW ConnectedDrive API using credentials from credentials.json
# You can see what should be in there by looking at credentials.json.sample.
#
# Based on the excellent work by Terence Eden:
# https://github.com/edent/BMW-i-Remote

import json
import requests
import time

#   API Gateway
ROOT_URL     = "https://b2vapi.bmwgroup.com/webapi"
API_ROOT_URL = ROOT_URL + '/v1' 

# What are we pretending to be? Not sure if this is important.
# Might be tied to OAuth consumer (auth_basic) credentials.
USER_AGENT = "MCVApp/1.5.2 (iPhone; iOS 9.1; Scale/2.00)"
# USER_AGENT = "Dalvik/2.1.0 (Linux; U; Android 5.1.1; Nexus 6 Build/LMY48Y)"

#   Constants
KM_TO_MILES  = 0.621371
EFFICIENCY = 0.01609344

# Not quite using this yet.
class ConnectedDriveException(Exception):
    pass

class ConnectedDrive(object):
    """
    A wrapper for the BMW ConnectedDrive API used by mobile apps.

    Caches credentials in credentials_file, so needs both read
    and write access to it.
    """
    def __init__(self, credentials_file='credentials.json'):
        self.credentials_file = credentials_file
        with open(self.credentials_file,"r") as cf:
            credentials = json.load(cf)
        self.username = credentials["username"]
        self.password = credentials["password"]
        self.auth_basic = credentials["auth_basic"]
        self.access_token = credentials["access_token"]
        self.token_expiry = credentials["token_expiry"]
        #	If the access_token has expired, generate a new one and use that
        if (time.time() > self.token_expiry):
            self.generateCredentials()
      
    def generateCredentials(self):
        """
        If previous token has expired, create a new one from basics.
        """
        headers = {
            "Authorization": "Basic " + self.auth_basic, 
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": USER_AGENT
        }

        data = { 
            "grant_type": "password",
            "username": self.username, 
            "password": self.password,
            "scope": "remote_services vehicle_data"
        }

        r = requests.post(ROOT_URL + "/oauth/token/",  data=data, headers=headers)
        json_data = r.json()
        
        #   Get the access token
        self.access_token = json_data["access_token"]
        self.token_expiry = time.time() + json_data["expires_in"]
        self.saveCredentials()


    def saveCredentials(self):
    	"""
    	Save current state to the JSON file.
    	"""
        credentials = {
            "username": self.username,
            "password": self.password,
            "auth_basic": self.auth_basic,
            "access_token": self.access_token,
            "token_expiry": self.token_expiry
        }
        # Open a file for writing
        with open(self.credentials_file, "w") as credentials_file:
            json.dump(credentials, credentials_file, indent=4)                                    


    def call(self, path):
    	"""
    	Call the API at the given path.

    	Argument should be relative to the API base URL, e.g:
    	
    	    print c.call('/user/vehicles/')

    	"""
    	# 
        if (time.time() > self.token_expiry):
            self.generateCredentials()

        headers = {"Authorization": "Bearer " + self.access_token, 
                   "User-Agent":USER_AGENT}

        r = requests.get(API_ROOT_URL + path,  headers=headers)
        return r.json()
       

# A simple test example
def main():
	c = ConnectedDrive()

	print "\nVehicle info"
	resp = c.call('/user/vehicles/')
	car = resp['vehicles'][0]
	for k,v in car.items():
		print "  ",k, " : ", v

	print "\nVehicle status"
	status = c.call("/user/vehicles/{}/status".format(car['vin']))['vehicleStatus']
	for k,v in status.items():
		print "  ", k, " : ", v


if __name__ == '__main__':
	main()

