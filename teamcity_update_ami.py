### Description
# This updates AWS AMI ID in TeamCity through REST API
#
#
# usage:
# python teamcity_update_ami.py -profile AWS-Ubuntu-Node -ami ami-03ea8eaad408d15dc 
# Or to get current AMI ID:
# python teamcity_update_ami.py -profile AWS-Ubuntu-Node -getCurrentAmi
#
# It expects credentials from a teamcity.txt file in this format:
# teamcity_user=tc_user
# teamcity_password=tc_pss
#

import time
import argparse
import re
#from tenacity import retry, stop_after_attempt, wait_fixed, RetryError
import requests
from requests.auth import HTTPBasicAuth
import lxml.etree as etree

### Global variables
teamcity_credentials_file = "teamcity.txt"
teamcity_url = "http://teamcity-server"

# Enable argument parser
parser = argparse.ArgumentParser()
parser.add_argument("-ami", nargs='?', required=False, help="specify AMI ID")
parser.add_argument("-profile", nargs='?', required=True, help="specify cloud profile")
parser.add_argument("-getCurrentAmi", action='store_true', required=False)
args = parser.parse_args()

### Functions
def load_credentials():
    # Load oauth key
    with open(teamcity_credentials_file, 'r') as f:
        # Read the file
        Teamcity_credentials = f.read().splitlines()
        # Split the line in two credentials
        global username
        global password
        username = Teamcity_credentials[0].split('=')[1]
        password = Teamcity_credentials[1].split('=')[1]
        f.close()

def get_profile_url(profile_name):
    try:
        request = requests.get(teamcity_url + '/httpAuth/app/rest/latest/projects/id:_Root',
                               auth=HTTPBasicAuth(username, password)).text.encode(
                'utf-8')
        tree = etree.fromstring(request)
        for child in tree.findall("./projectFeatures/*[@type='CloudProfile']"):
            for x in child.findall("./properties/*"):
                var = x.get('name'), x.get('value')
                # print var
                if var[0] == "name" and var[1] == profile_name:
                    #print var
                    global profile_id
                    profile_id = child.get('id')
                    print "Profile ID: " + profile_id
        try:
            profile_id
        except NameError:
            print "Error. Profile not found. Check profile name"
            raise Exception

        for child in tree.findall("./projectFeatures/*[@type='CloudImage']"):
            for x in child.findall("./properties/*"):
                var = x.get('name'), x.get('value')
                # print var
                if var[0] == "profileId" and var[1] == profile_id:
                    #print var
                    global link
                    link = child.get('href')
                    print "Link: " + teamcity_url + link
                    return link
    except:
        print request.content


def modify_property(propertyName, value):
    if not args.getCurrentAmi:
        try:
            request = requests.get(teamcity_url + link, auth=HTTPBasicAuth(username, password)).text.encode(
                'utf-8')
            object = etree.fromstring(request)
            text = etree.tostring(object, pretty_print=True)
            headers = {'Content-Type': 'application/xml'}
            # Modify attribute to a new one with RegEx
            var = '<property name="' + propertyName + '" value="' + value + '"/>'
            payload = re.sub(r'<property name="' + propertyName + '" value=\"[\s\S]*?/>', var, text)
            r = requests.put(teamcity_url + link, auth=HTTPBasicAuth(username, password), data=payload,
                             headers=headers)
            #print r.text
        except Exception, e:
            print "Update failed: " + str(e)
            print r.content

def get_ami_in_use(link):
    try:
        request = requests.get(teamcity_url + link,
                               auth=HTTPBasicAuth(username, password)).text.encode(
                'utf-8')
        tree = etree.fromstring(request)
        for child in tree.findall("./properties/*"):
            var = child.get('name'), child.get('value')
            if var[0] == "amazon-id":
                #return child.get('value')
                global currentAmi
                currentAmi = child.get('value')
                print "Current AMI ID: " + currentAmi
    except:
        print "Failed to obtain current AMI id"
        raise Exception

def compare_amis(newAmi):
    if not args.getCurrentAmi:
        if currentAmi == newAmi:
            print "AMI update OK"
        else:
            print "AMI ids don't match. Update failed."
            raise Exception

def clean_up_unauthorized_agents():
    if not args.getCurrentAmi:
        suburl = "/app/rest/latest/agents?locator=authorized:no"
        request = requests.get(teamcity_url + suburl,
                               auth=HTTPBasicAuth(username, password)).text.encode(
                            'utf-8')
        tree = etree.fromstring(request)
        print "Doing clean up..."
        try:
            for child in tree.findall("*"):
                print "Deleting unauthorized agent " + child.get('name')
                href = child.get('href')
                r = requests.delete(teamcity_url + href,
                           auth=HTTPBasicAuth(username, password))
                print r.content
        except:
            pass

if __name__ == "__main__":
    load_credentials()
    get_profile_url(args.profile)
    modify_property('amazon-id', args.ami)
    modify_property('source-id', args.ami)
    get_ami_in_use(link)
    clean_up_unauthorized_agents()
    compare_amis(args.ami)