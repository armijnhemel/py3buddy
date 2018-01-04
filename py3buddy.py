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
import sys, os, time

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
## To set a capability the relevant bits need to be turned off. The easiest
## way to do this is by distracting integers. The initial value is 0xff (255).
##
## For example to enable the heart LED bit 7 needs to be 0, so
## distract 128 (0b10000000):
##
## hex(0xff - 128) = 0x7f
##
## For this to work the easiest the bits have first to be brought to a known state
## (all 1).
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

## some convenience dicts for colours
NOCOLOUR = {'red': False, 'blue': False, 'green': False}
RED = {'red': True, 'blue': False, 'green': False}
BLUE = {'red': False, 'blue': True, 'green': False}
GREEN = {'red': False, 'blue': False, 'green': True}
CYAN = {'red': False, 'blue': True, 'green': True}
YELLOW = {'red': True, 'blue': False, 'green': True}
PURPLE = {'red': True, 'blue': True, 'green': False}
WHITE = {'red': True, 'blue': True, 'green': True}

## a list of all colours
allcolours = [NOCOLOUR, RED, BLUE, GREEN, CYAN, YELLOW, PURPLE, WHITE]

## a list of macros for sleep, in seconds
ULTRASHORTSLEEP = 0.05
SHORTSLEEP = 0.1
SLEEP = 1
LONGSLEEP = 10
GLACIAL = 100

## a list of valid commands for the macro language
validcmds = set(['ULTRASHORTSLEEP', 'SHORTSLEEP', 'SLEEP', 'LONGSLEEP', 'GLACIAL', 'RESET', 'GO',
                  'WINGSHIGH', 'WINGSLOW', 'HEART', 'NOHEART', 'NOCOLOUR', 'RED',
                  'BLUE', 'GREEN', 'CYAN', 'YELLOW', 'PURPLE', 'WHITE', 'LEFT',
                  'RIGHT', 'MIDDLE', 'MIDDLE2'])

class iBuddy:
	## First find the iBuddy. There apparently also have been iBuddy products
	## with other product IDs, such as 0x0001
	def __init__(self, buddy_config):
		self.dev = None
		if not 'productid' in buddy_config:
			return
		if not buddy_config['productid'] in set([0x0001, 0x0002, 0x004]):
			return
		self.dev = usb.core.find(idVendor=0x1130, idProduct=buddy_config['productid'])

		## check if the device was found. If not, return.
		if self.dev is None:
			return

		## first remove all the kernel drivers. Probably better to do this
		## with a udev blacklist rule?
		try:
			if self.dev.is_kernel_driver_active(0) is True:
				self.dev.detach_kernel_driver(0)
		except usb.core.USBError as e:
			self.dev = None
			return

		try:
			if self.dev.is_kernel_driver_active(1) is True:
				self.dev.detach_kernel_driver(1)
		except usb.core.USBError as e:
			self.dev = None
			return

		## there is just one configuration in the iBuddy, so use it
		## (is this necessary?)
		#self.dev.set_configuration()

		## then grab the active configuration (a bit superfluous here though)
		#self.cfg = self.dev.get_active_configuration()
		self.command = 0xff
		self.pos = None
		if 'reset_position' in buddy_config:
			self.resetpos = buddy_config['reset_position']
		else:
			self.resetpos = False
	def reset(self):
		## method to explicitely reset the iBuddy
		## if configured it will also reset its wiggling position
		## to center, although for right this does not always
		## seem to work
		if self.resetpos:
			self.dev.ctrl_transfer(0x21, 0x09, 2, 1, setupmsg)
			if self.pos == 'left':
				self.wiggle('right')
				msg = self.createmsg()
				self.dev.ctrl_transfer(0x21, 0x09, 2, 1, msg)
				time.sleep(0.05)
				self.wiggle('middle')
				msg = self.createmsg()
				self.dev.ctrl_transfer(0x21, 0x09, 2, 1, setupmsg)
				self.dev.ctrl_transfer(0x21, 0x09, 2, 1, msg)
			elif self.pos == 'right':
				self.wiggle('middlereset')
				msg = self.createmsg()
				self.dev.ctrl_transfer(0x21, 0x09, 2, 1, msg)
		self.dev.ctrl_transfer(0x21, 0x09, 2, 1, setupmsg)
		self.dev.ctrl_transfer(0x21, 0x09, 2, 1, resetmsg)
		## reset the command byte
		self.command = 0xff
	def wiggle(self, pos):
		## method to wiggle
		## first reset the status explicitely to "no wiggle"
		## 0b11 == 3
		self.command = self.command | 3
		if pos == 'middle':
			## middle = 0
			## 0b00
			self.command -= 3
			self.pos = 'middle'
		elif pos == 'left':
			## left = 1
			## 0b01
			self.command -= 2
			self.pos = 'left'
		elif pos == 'right':
			## right = 2
			## 0b10
			self.command -= 1
			self.pos = 'right'
		elif pos == 'middlereset':
			## initial position = 3
			## 0b11
			self.command = self.command | 3
			self.pos = 'middlereset'
	def toggleheart(self, heart):
		## method to toggle the heart LED
		## first reset the status explicitely to
		## "no heart LED"
		self.command = self.command | 128
		if heart:
			self.command -= 128
	def wings(self, wings):
		## method to set the position of the wings
		## first reset the status explicitely to
		## "neutral"
		## 0b1100 == 12
		self.command = self.command | 12
		if wings == 'high':
			# 0b0100
			self.command -= 8
		elif wings == 'low':
			# 0b1000 so
			self.command -= 4
	def setcolour(self, colour):
		## method to set the colour of the head LED
		## colour profile: {'r', 'g', 'b'}
		## first reset the status explicitely to
		## "no colour"
		## 0b1110000 == 112
		self.command = self.command | 112
		if colour['red']:
			self.command -= 16
		if colour['green']:
			self.command -= 32
		if colour['blue']:
			self.command -= 64
	def createmsg(self):
		msgbytes = messagebytes + [self.command]
		msg = bytes(msgbytes)
		return msg
	def sendcommand(self):
		msg = self.createmsg()
		self.dev.ctrl_transfer(0x21, 0x09, 2, 1, setupmsg)
		self.dev.ctrl_transfer(0x21, 0x09, 2, 1, msg)
	def executecommand(self, cmd):
		## the original version of pybuddy had a macro-like language:
		## https://github.com/ewall/pybuddy/blob/master/src/pybuddy-daemon.py#L170
		##
		## Do something similar here, but make it a bit easier (no recursive calls,
		## easier to specify colours, different types of sleep)
		##
		## Commands are colon separated
		##
		## For the heart LED:
		## * HEART
		## * NOHEART
		##
		## For the head LED:
		## * colour name (NOCOLOUR, RED, BLUE, GREEN, CYAN, YELLOW, PURPLE, WHITE)
		##
		## For wiggle:
		## * LEFT
		## * RIGHT
		## * MIDDLE
		## * MIDDLE2 (not a good name)
		##
		## For wings:
		## * WINGSHIGH
		## * WINGSLOW
		##
		## For sleep:
		## * SHORTSLEEP
		## * SLEEP
		## * LONGSLEEP
		## * GLACIAL
		##
		## To execute a command:
		## * GO
		##
		## To reset:
		## * RESET
		##
		## First store a list of commands
		msgs = cmd.split(':')

		## check if the list of commands actually makes sense
		## if not, return. Empty commands are allowed.
		if len(list(filter(lambda x: x not in validcmds and x != '', msgs))) != 0:
			print(msgs)
			return
		for i in msgs:
			if i == 'HEART':
				self.toggleheart(True)
			elif i == 'NOHEART':
				self.toggleheart(False)
			elif i == 'NOCOLOUR':
				self.setcolour(NOCOLOUR)
			elif i == 'RED':
				self.setcolour(RED)
			elif i == 'BLUE':
				self.setcolour(BLUE)
			elif i == 'GREEN':
				self.setcolour(GREEN)
			elif i == 'CYAN':
				self.setcolour(CYAN)
			elif i == 'YELLOW':
				self.setcolour(YELLOW)
			elif i == 'PURPLE':
				self.setcolour(PURPLE)
			elif i == 'WHITE':
				self.setcolour(WHITE)
			elif i == 'LEFT':
				self.wiggle('left')
			elif i == 'RIGHT':
				self.wiggle('right')
			elif i == 'MIDDLE':
				self.wiggle('middle')
			elif i == 'MIDDLE2':
				self.wiggle('middlereset')
			elif i == 'WINGSHIGH':
				self.wings('high')
			elif i == 'WINGSLOW':
				self.wings('low')
			elif i == 'GO':
				self.sendcommand()
			elif i == 'RESET':
				self.reset()
			elif i == 'ULTRASHORTSLEEP':
				time.sleep(ULTRASHORTSLEEP)
			elif i == 'SHORTSLEEP':
				time.sleep(SHORTSLEEP)
			elif i == 'SLEEP':
				time.sleep(SLEEP)
			elif i == 'LONGSLEEP':
				time.sleep(LONGSLEEP)
			elif i == 'GLACIAL':
				time.sleep(GLACIAL)
