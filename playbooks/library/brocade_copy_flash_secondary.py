#!/usr/bin/python

DOCUMENTATION = '''
---
module: brocade_copy_flash_secondary
short_description: Copy Primary Flash image to Secondary Flash on Brocade Switch
description:
	- Copy Primary Flash image to Secondary Flash on Brocade Switch
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
    - name: Copy Flash to Secondary
      brocade_copy_flash_secondary:
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
    - name: Copy Flash to Secondary
      brocade_copy_flash_secondary:
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

def brocade_copy_flash_secondary(module):
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
		child.sendline('copy flash flash secondary')
		child.expect('.*Flash to Flash Don.*',timeout=300)
		child.expect('.*#.*')
		logging.info('copy flash flash completed, saving config')
		child.sendline('write mem')
		child.expect('.*#.*')
		sleep(5)
		logging.info('Post-Staging commands finished on ' + hostname)
		child.sendline('logout')
		child.close()

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
	results = brocade_copy_flash_secondary(module)

	module.exit_json(**results)

from ansible.module_utils.basic import *
main()


