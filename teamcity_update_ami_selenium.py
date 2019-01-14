### Description
# This updates AWS AMI ID in TeamCity. As there is no way to do this through API,
# it uses a good-old Selenium browser emulation
#
# Uncomment pyvirtualdisplay to run this stuff in Linux docker container.
# Run it in something like this Docker image:
# https://hub.docker.com/r/markadams/chromium-xvfb-py2/
#
# script usage:
# python teamcity_update_ami.py -ami ami-03ea8eaad408d15dc -profile AWS-BuildNode-Ubuntu
# # Or to get current AMI ID:
# python teamcity_update_ami.py -profile AWS-BuildNode-Ubuntu -getCurrentAmi
#

import time
from splinter import Browser
#from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import argparse
import re
from tenacity import retry, stop_after_attempt, wait_fixed, RetryError

### Global variables
teamcity_credentials_file = "teamcity.txt"
teamcity_url = "http://"

# Enable argument parser
parser = argparse.ArgumentParser()
parser.add_argument("-ami", nargs='?', required=False, help="specify AMI ID")
parser.add_argument("-profile", nargs='?', required=True, help="specify cloud profile")
parser.add_argument("-getCurrentAmi", action='store_true', required=False)
args = parser.parse_args()

### Functions
def load_credentials(type):
    # Load oauth key
    with open(teamcity_credentials_file, 'r') as f:
        # Read the file
        Teamcity_credentials = f.read().splitlines()
        # Split the line in two credentials
        teamcity_user = Teamcity_credentials[0].split('=')[1]
        teamcity_password = Teamcity_credentials[1].split('=')[1]
        f.close()
    if type == 'user':
        return teamcity_user
    elif type == 'password':
        return teamcity_password

@retry(stop=stop_after_attempt(3), wait=wait_fixed(5))
def update_ami(user,password,ami_id):
    if args.ami:
        print "updating TeamCity profile " + args.profile + " with AMI ID: " + args.ami
        # Initiliase virtual browser
        #display = Display(visible=0, size=(1366, 768))
        #display.start()
        #browser = webdriver.Chrome()
        #browser.set_window_size(1366, 768)
        try:
            with Browser('chrome') as browser:
                # Open Login page
                url = teamcity_url
                browser.visit(url)
                browser.find_by_id('username').fill(user)
                browser.find_by_id('password').fill(password)
                button = browser.find_by_name('submitLogin')
                button.first.click()
                if browser.is_text_present('Projects', wait_time=10):
                    # Open Cloud Profile page
                    url = teamcity_url + "admin/editProject.html?projectId=_Root&tab=clouds"
                    browser.visit(url)
                    button = browser.find_by_text(args.profile)
                    button.first.click()
                    # Wait until AWS config is fetched
                    while browser.is_text_present('Fetching', wait_time=1):
                        print "Fetching AWS config"
                        if not browser.is_text_present('Fetching', wait_time=1):
                            break
                    browser.find_by_xpath('//*[@id="amazonImagesTable"]/tbody/tr[2]/td[7]/a').click()
                    time.sleep(3)
                    #button.first.click()
                    browser.find_by_id('-ufd-teamcity-ui-amazon-id').fill("Public AMI")
                    browser.find_by_id('-ufd-teamcity-ui-amazon-id').fill(Keys.ENTER)
                    browser.find_by_id('-ufd-teamcity-ui-amazon-id').fill(Keys.TAB)
                    browser.find_by_id('amazon-id-custom').fill(ami_id)
                    button = browser.find_by_id('addImageButton')
                    button.first.click()
                    if browser.is_text_present('The changes are not yet saved.', wait_time=None):
                        print "Save button found"
                        button = browser.find_by_name('save')
                        button.first.click()
                    else:
                        print "no changes made"
                    if browser.is_text_present('You removed the following sources'):
                        button = browser.find_by_id('removeImageConfirmButton')
                        button.first.click()
                        print("Terminating active agents")
                    else:
                        print("No active agents running. Good.")
                    print "Finished updating AMI ID"
        except:
            raise Exception

@retry(stop=stop_after_attempt(3), wait=wait_fixed(5))
def get_ami_in_use(user,password):
    if args.getCurrentAmi:
        # Initiliase virtual browser
        #display = Display(visible=0, size=(1366, 768))
        #display.start()
        #browser = webdriver.Chrome()
        #browser.set_window_size(1366, 768)
        try:
            with Browser('chrome') as browser:
                # Open Login page
                url = teamcity_url
                browser.visit(url)
                browser.find_by_id('username').fill(user)
                browser.find_by_id('password').fill(password)
                button = browser.find_by_name('submitLogin')
                button.first.click()
                if browser.is_text_present('Projects', wait_time=10):
                    # Open Cloud Profile page
                    url = teamcity_url + "admin/editProject.html?projectId=_Root&tab=clouds"
                    browser.visit(url)
                    button = browser.find_by_text(args.profile)
                    button.first.click()
                    # Wait until AWS config is fetched
                    while browser.is_text_present('Fetching', wait_time=1):
                        #rint "Fetching AWS config"
                        if not browser.is_text_present('Fetching', wait_time=1):
                            break
                    element = browser.find_by_id('amazonImagesTable')
                    ami_in_use = re.findall("Id: (.*)", element.text)
                    print ami_in_use[0]
        except:
            raise Exception


### Start of functions
#print load_credentials("user")
#print load_credentials("password")
update_ami(load_credentials("user"),load_credentials("password"),args.ami)
get_ami_in_use(load_credentials("user"),load_credentials("password"))
