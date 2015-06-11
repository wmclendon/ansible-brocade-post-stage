#!/usr/bin/python

DOCUMENTATION = '''
---
module: brocade_generate_ssh_key
short_description: Generate SSH Key on Brocade Switch
description:
	- Generates SSH Key on Brocade Switch
author: Will McLendon
'''

import os, errno
import logging
from pexpect import *
from time import sleep


EXAMPLES = '''
# Example Playbook:
---
- name: Brocade ICCX6450 Switch Post Staging
  hosts: icx6450s
  vars:
    username: ansible
    password: password
    logfileDirectory: "/tmp/log"
  connection: local
  gather_facts: no

  tasks:
    - name: Generate SSH Key
      brocade_generate_ssh_key:
         host="{{ inventory_hostname }}"
         username="{{ username }}"
         password="{{ password }}"
         logfileDirectory="{{ logfileDirectory }}"

- name: Brocade ICCX6610 Switch Post Staging
  hosts: icx6610s
  vars:
    username: ansible
    password: password
    logfileDirectory: "/tmp/log"
  connection: local
  gather_facts: no

  tasks:
    - name: Generate SSH Key
      brocade_generate_ssh_key:
         host="{{ inventory_hostname }}"
         username="{{ username }}"
         password="{{ password }}"
         logfileDirectory="{{ logfileDirectory }}"
'''
def createDir(d):
	try:
		os.makedirs(d)
	except OSError as exc:
		if exc.errno == errno.EEXIST and os.path.isdir(d):
			pass
		else: raise

def brocade_generate_ssh_key(module):
	hostname = module.params['host']
	username = module.params['username']
	password = module.params['password']


	# For now the log file is mandatory and always created for debugging and verification.
	# To do list includes making it optional
	# It looks like since Ansible copies the script into a temp folder the absolute path is required for the directory
	# There is probably a more "ansible" way set a directory but this works ok for now
	logfileDirectory = module.params['logfileDirectory']
	createDir(logfileDirectory)
	logfile = logfileDirectory + '/' + hostname + '--post-stage-log.log'

	results = {}
	results['changed'] = False	#default to False, no changes made
	try:
		# Telnet to device:
		child = spawn ('telnet ' + hostname)

		child.expect('.*ogin Name:.*')
		child.logfile = open(logfile,'w')
		child.sendline(username)
		child.expect('.*assword:.*')
		child.sendline(password)
		child.expect('.*#.*')
		logging.info('Logged into ' + hostname + ', executing crypto key generate')
		# we are now logged in, can run a command now

		# Enter config mode and generate crypto key, then exit config mode:
		child.sendline('config t')
		child.expect('.*\(config\).*')
		child.sendline('crypto key zeroize')
		child.expect('.*\(config\).*')
		child.sendline('crypto key generate')
		child.expect('(.*Key pair is successfully create.*)|(.*ey already exist.*)')
		child.expect('.*(config).*')
		child.sendline('end')
		child.expect('.*#.*')
		sleep(5)
		logging.info('Crypto key generated, now copying over bootrom...')
		child.sendline('logout')
		child.close()
		sleep(5)

		# if we get here, all work completed successfully, mark as Changed
		results['changed'] = True
	except EOF, err:
		results['failed'] = True
		msg = "EOF error -- unable to connect to {}".format(module.params['host'])
		results['msg'] = msg
		logging.info('EOF Error on {}'.format(module.params['host']))
		logging.info(err)
		module.fail_json(msg='ERROR -- Unable to connect to {}'.format(module.params['host']))
	except TIMEOUT, err:
		results['failed'] = True
		msg = "TIMEOUT error -- did not get expected values returned on {}".format(module.params['host'])
		results['msg'] = msg
		logging.info('TIMEOUT Error on {}'.format(module.params['host']))
		logging.info(err)
		module.fail_json(msg='ERROR - Did not get expected values returned on {}'.format(module.params['host']))
	return results



def main():
	module = AnsibleModule(
		argument_spec = dict(
			host=dict(required=True),
			username=dict(required=True),
			password=dict(required=True),
			logfileDirectory=dict(required=True)
		)
	)

	logging.info("Connecting to switch: {}".format(module.params['host']))
	results = brocade_generate_ssh_key(module)

	module.exit_json(**results)

from ansible.module_utils.basic import *
main()


