#!/usr/bin/env python
"""This Python Script will activate a script and then 5 seconds deactivate a script
"""
import ciscosparkapi
import requests
import urllib3
import datetime
import time
import json
import os
# Disable Certificate warning
try:
    requests.packages.urllib3.disable_warnings()
except:
    pass
from requests.auth import HTTPBasicAuth
import sys

# Get the absolute path for the directory where this file is located "here"
here = os.path.abspath(os.path.dirname(__file__))

# Get the absolute path for the project / repository root
project_root = os.path.abspath(os.path.join(here, '../..'))

# Extend the system path to include the project root and import the env files
sys.path.insert(0, project_root)
import env_lab
import env_user

spark = ciscosparkapi.CiscoSparkAPI(access_token=env_user.SPARK_ACCESS_TOKEN)

# Details for SDWAN Center Platform API calls from env_lab file
sdwan_host = env_lab.vManage['host']
sdwan_user = env_lab.vManage['username']
sdwan_pass = env_lab.vManage['password']
sdwan_headers = {'content-type': 'application/json'}

snow_url = env_lab.serviceNow['url']
snow_user = env_lab.serviceNow['username']
snow_pass = env_lab.serviceNow['password']

def get_user_sys_id(snow_user):

    # find the ServiceNow user_id for the specified user

    url = snow_url + '/table/sys_user?sysparm_limit=1'
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    response = requests.get(url, auth=(snow_user, snow_pass), headers=headers)
    user_json = response.json()
    return user_json['result'][0]['sys_id']


def create_incident(description, comment, snow_user, severity):

    # This function will create a new incident with the {description}, {comments}, severity for the {user}

    caller_sys_id = get_user_sys_id(snow_user)
    print (caller_sys_id)
    url = snow_url + '/table/incident'
    payload = {'short_description': description,
               'comments': (comment + ', \nIncident created using APIs by caller Kenneth'),
               'caller_id': caller_sys_id,
               'urgency': severity
               }
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    response = requests.post(url, auth=(snow_user, snow_pass), data=json.dumps(payload), headers=headers)
    incident_json = response.json()
    return incident_json['result']['number']


def initalize_connection(ipaddress,username,password):

    """
    This function will initialize a connection to the vManage
    :param ipaddress: This is the IP Address and Port number of vManage
    :param username:  This is the username for vManage (admin in our lab)
    :param password:  This is a password for vManage (admin in our lab)
    These will be set in a file called package_config.ini
    """

    # Disable warnings like unsigned certificates, etc.
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    print('SDWAN Login to ' + sdwan_host + ' as ' + sdwan_user + ' ...')
    url="https://"+sdwan_host+"/j_security_check"

    payload = "j_username="+sdwan_user+"&j_password="+password
    headers = {
        'Content-Type': "application/x-www-form-urlencoded",
        }

    sess=requests.session()

    # Handle exceptions if we cannot connect to the vManage
    try:
        response = sess.request("POST", url, data=payload, headers=headers,verify=False,timeout=10)
    except requests.exceptions.ConnectionError:
        print ("Unable to Connect to "+ipaddress)
        return False

    return sess

def policy_cycle(sdwan_host,session):
    policy_id = "3794f7d2-ecf8-48bd-a912-d9fc0ef3a59b"
    activate_policy_url = "https://%s/dataservice/template/policy/vsmart/activate/PUT_YOUR_POLICY_ID_HERE"%(sdwan_host)
    deactivate_policy_url = "https://%s/dataservice/template/policy/vsmart/deactivate/PUT_YOUR_POLICY_ID_HERE"%(sdwan_host)
    payload = "{\n }"
    headers = {'Content-Type':'application/json'}
    i=0
    while i<2:
        i+=1
        response = session.request("GET",activate_policy_url,verify=False,timeout=10)
        data = response.content
        #print (data)
        t = datetime.datetime.now()
        print ("Policy Activated for 5 seconds @ %s "%t)
        #message = spark.messages.create(env_user.SPARK_ROOM_ID, text='Look No Hands! - Activacte Policy - Kenneth')
        #print(message)
        time.sleep(5)

        response = session.request("GET",deactivate_policy_url,verify=False,timeout=10)
        data = response.content
        #print (data)
        t = datetime.datetime.now()
        print ("Policy Deactivated for 5 seconds @ %s "%t)
        #message = spark.messages.create(env_user.SPARK_ROOM_ID, text='Look No Hands! - Deactivate Policy - Kenneth')
        #print(message)
        time.sleep(5)

session=initalize_connection(sdwan_host,sdwan_user,sdwan_pass)
if session != False:
    print ("Connection to vManage successful")
    policy_cycle(sdwan_host,session)
    comments = 'There has been a policy change on: ' + sdwan_host
    incidentid = create_incident('Policy Change', comments, snow_user, 3)
    print('Incident opened on ServiceNow')
    incidenturl = "https://dev62992.service-now.com/nav_to.do?uri=incident.do?sys_id="+incidentid
    print('incidenturl: ' + incidenturl)
    message = spark.messages.create(env_user.SPARK_ROOM_ID, text=incidenturl)
    print(message)
