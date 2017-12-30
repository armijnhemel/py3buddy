#!/usr/bin/python3

## A simple program to control the Tenx Technology, Inc. iBuddy
## which was sold as a figurine for MSN Messenger to respond to smileys
## sent in MSN Messenger.
##
## It can perform a few actions, such as flashing some LEDs, wiggle and flap its
## wings. It is a really silly device, but it has its uses.
##
## A lot of the information about the protocol is documented in several
## places on the Internet, in drivers (both in Linux kernel space and
## user space for various programs).
##
## iBuddy protocol specific parts were inspired by:
##
## * https://github.com/tietomaakari/ibuddy-lkm (kernel module for Linux)
## * https://github.com/ewall/pybuddy/ (user space)
##
## This program mostly served its purpose for me to play with pyusb during
## the 2017 end of year.
##
## Copyright 2017 - Armijn Hemel for Tjaldur Software Governance Solutions
## SPDX-Identifier: GPL-3.0

## See https://github.com/pyusb/pyusb/blob/master/docs/tutorial.rst
## for some of the explanations of the USB part

import usb.core, usb.util
import sys, os, time, argparse, configparser

## The iBuddy works as follows (according to other people's code):
## * a setup message is sent every time
## * during initialization a reset message is sent
## * commands start with the same 7 byte sequence
## * a reset command at the end to clear everything
##
## The tricky part is that in Python 3 you cannot simply send
## strings, as those are UTF-8 and then things will not work
## as expected. That's why for Python 3 you need to use actual bytes.
##
## The device has a few capabilities that can be set:
## * heart LED
## * head LED (RGB)
## * wings (flap flap)
## * motor (wiggle)
##
## These options need be set in a single byte that is then appended to
## the earlier mentioned message bytes. The bits are as follows:
## * heart LED (bit 7)
## * head LED (bits 4,5,6)
## * wings (bits 2,3)
## * motor (bits 0,1)
##
## To set a capability the relevant bits need to be turnde off. The easiest
## way to do this is by XORing with the message byte, of which the initial value
## is 0xff.
## For example to enable the heart LED bit 7 needs to be 0, so
## XOR with 128 (0b10000000):
##
## hex(0xff ^ 128) = 0x7f
##
## heart LED: 0 is on, 1 is off
## head LED: R is bit 4, G is bit 5, B is bit 6, 0 is on, 1 is off
## wings: 1 is wings high, 2 is wings low (could have been done in 1 bit)
## motor: 0: center (but only after 'turn right', 1: turn left, 2: turn right,
##        3: turn center a bit (but only after 'turn right')
## the setup message
setupbytes = [0x22, 0x09, 0x00, 0x02, 0x01, 0x00, 0x00, 0x00]
setupmsg = bytes(setupbytes)

## the message bytes. Each message apart from the setup message
## starts with this particular sequence.
messagebytes = [0x55, 0x53, 0x42, 0x43, 0x00, 0x40, 0x02]

## the reset message
resetbytes = messagebytes + [0xff]
resetmsg = bytes(resetbytes)

class iBuddy:
	## First find the iBuddy. There apparently also have been iBuddy products
	## with other product IDs, such as 0x0001
	def __init__(self, buddy_config):
		self.dev = None
		if not 'productid' in buddy_config:
			return None
		self.dev = usb.core.find(idVendor=0x1130, idProduct=buddy_config['productid'])

		## check if the device was found. If not, exit.
		if self.dev is None:
			raise ValueError('Device not found')
			return None

		## first remove all the kernel drivers. Probably better to do this
		## with a udev blacklist rule?
		try:
			if self.dev.is_kernel_driver_active(0) is True:
				self.dev.detach_kernel_driver(0)
		except usb.core.USBError as e:
			return None

		try:
			if self.dev.is_kernel_driver_active(1) is True:
				self.dev.detach_kernel_driver(1)
		except usb.core.USBError as e:
			return None

		## there is just one configuration in the iBuddy, so use it
		## (is this necessary?)
		#self.dev.set_configuration()

		## then grab the active configuration (a bit superfluous here though)
		#self.cfg = self.dev.get_active_configuration()
	def reset(self):
		## method to explicitely reset the iBuddy
		self.dev.ctrl_transfer(0x21, 0x09, 2, 1, setupmsg)
		self.dev.ctrl_transfer(0x21, 0x09, 2, 1, resetmsg)
	def demo(self):
		self.reset()
		## demo commands copied from pybuddy
		msgs = [
		[0x55, 0x53, 0x42, 0x43, 0x0, 0x40, 0x2, 0xea],
		[0x55, 0x53, 0x42, 0x43, 0x0, 0x40, 0x2, 0x55],
		[0x55, 0x53, 0x42, 0x43, 0x0, 0x40, 0x2, 0xba],
		[0x55, 0x53, 0x42, 0x43, 0x0, 0x40, 0x2, 0x25],
		[0x55, 0x53, 0x42, 0x43, 0x0, 0x40, 0x2, 0xca],
		[0x55, 0x53, 0x42, 0x43, 0x0, 0x40, 0x2, 0x15],
		[0x55, 0x53, 0x42, 0x43, 0x0, 0x40, 0x2, 0x8a],
		]
		for i in msgs:
			retval = self.dev.ctrl_transfer(0x21, 0x09, 2, 1, setupmsg)
			msg = bytes(i)
			retval = self.dev.ctrl_transfer(0x21, 0x09, 2, 1, msg)
			time.sleep(0.1)
		self.reset()

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

	## initialize an iBuddy and check if a device was found and is accessible
	ibuddy = iBuddy(buddy_config)
	if ibuddy.dev == None:
		print("No iBuddy found, or iBuddy not accessible", file=sys.stderr)
		sys.exit(1)
	ibuddy.demo()

if __name__ == "__main__":
	main(sys.argv)
