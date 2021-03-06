#############################################################################
# Licensed Materials - Property of HCL*
# (C) Copyright HCL Technologies Ltd. 2017, 2020 All rights reserved.
# * Trademark of HCL Technologies Limited
#############################################################################
import requests
import uuid
from .prop import readProps

import logging
from httplib import HTTPConnection
#HTTPConnection.debuglevel = 1

logging.basicConfig() # you need to initialize logging, otherwise you will not see anything from requests
#logging.getLogger().setLevel(logging.DEBUG)
requests_log = logging.getLogger("requests.packages.urllib3")
#requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True


class WAConn:
	reqId = str(uuid.uuid4())
	config = {}
	prefix = ''
	hostIdx = 0
	
	def __init__(self, propFile, pref):
		self.config = readProps(propFile)
		self.prefix = pref
		
	def __str__(self):
		return 'WAConn (%s, %s)' % (self.config, self.prefix)
		
	def request(self, method, uri, headers=None, params=None, json=None, data=None):

		headers = headers or {}
		if 'Content-Type' not in headers:
			headers['Content-Type'] = 'application/json'
		if 'Accept' not in headers:
			headers['Accept'] = 'application/json'
		if 'How-Many' not in headers:
			headers['How-Many'] = '500'
		if 'Request-Id' not in headers:
			headers['Request-Id'] = self.reqId

		retry = True
		hosts = self.config['hosts']
		retries = 0
		resp = None
		while retry and retries < len(hosts):
			retry = False
			url = hosts[self.hostIdx] + self.prefix + uri
			print 'Connecting to %s for %s' % (url, method)
			try:
				resp = requests.request(method, url, json=json, data=data, headers=headers, auth=(self.config['user'],self.config['pwd']), verify=self.config['verify'])
			except requests.exceptions.ConnectionError, error:
				print 'Connection error: '+ str(error)
				retry = True
				self.hostIdx+=1
				if self.hostIdx >= len(hosts):
					self.hostIdx=0
				retries+=1

		print 'Result: %d' % resp.status_code
		if not resp.ok:
			json = resp.json()
			if json and json['messages']:
				print "Error from server:"
				for m in json['messages']:
					print " %s" % (m)
		else:
			resp.raise_for_status()
			
		return resp

	def put(self, uri, json=None, data=None, headers=None):
		return self.request('PUT', uri, headers=headers, json=json, data=data)

	def post(self, uri, json=None, headers=None):
		return self.request('POST', uri, headers=headers, json=json)
		
	def get(self, uri, params=None):
		return self.request('GET', uri, params=params)
	

				