#!/usr/bin/python3

## Demo program to show how to use the py3buddy module with DBus and integrate
## with Pidgin
##
## Uses python3-gobject-base and python3-pydbus (package names from Fedora)
##
## Copyright 2017-2018 - Armijn Hemel for Tjaldur Software Governance Solutions
## SPDX-Identifier: GPL-3.0

import sys, os, argparse, configparser
import py3buddy
import pydbus, gi


## wrap an iBuddy inside a DBus service
class IBuddyDbusService(object):
	"""
	<node>
	<interface name='nl.tjaldur.IBuddy'>
	<method name='ExecuteBuddyCommand'>
	<arg type='s' name='command' direction='in'/>
	</method>
	</interface>
	</node>
        """

	def __init__(self,ibuddy):
		self.ibuddy = ibuddy

	def ExecuteBuddyCommand(self, command):
		self.ibuddy.executecommand(command)
		self.ibuddy.reset()

def main(argv):
	parser = argparse.ArgumentParser()

	## options for the commandline
	parser.add_argument("-c", "--config", action="store", dest="cfg", help="path to configuration file", metavar="FILE")
	args = parser.parse_args()

	## first some sanity checks for the configuration file
	if args.cfg == None:
		parser.error("Configuration file missing")

	if not os.path.exists(args.cfg):
		parser.error("Configuration file does not exist")

	## then parse the configuration file
	config = configparser.ConfigParser()

	configfile = open(args.cfg, 'r')

	try:
		config.readfp(configfile)
	except Exception:
		print("Cannot read configuration file", file=sys.stderr)
		sys.exit(1)

	buddy_config = {}
	for section in config.sections():
		if section == 'ibuddy':
			try:
				productid = int(config.get(section, 'productid'))
				buddy_config['productid'] = productid
			except:
				pass

			buddy_config['reset_position'] = False
			try:
				reset_position_val = config.get(section, 'reset_position')
				if reset_position_val == 'yes':
					buddy_config['reset_position'] = True
			except:
				pass
		if section == 'twitter':
			pass

	## This is very ugly, but the only way (I know) to expose the iBuddy to the
	## method processing the message from Pidgin
	#global ibuddy

	## initialize an iBuddy and check if a device was found and is accessible
	ibuddy = py3buddy.iBuddy(buddy_config)
	if ibuddy.dev == None:
		print("No iBuddy found, or iBuddy not accessible", file=sys.stderr)
		sys.exit(1)

	bus = pydbus.SessionBus()
	bus.publish("nl.tjaldur.IBuddy", IBuddyDbusService(ibuddy))

	gi.repository.GObject.MainLoop().run()

	## finally reset the i-buddy again
	ibuddy.reset()

if __name__ == "__main__":
	main(sys.argv)
