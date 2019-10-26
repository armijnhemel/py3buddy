#!/usr/bin/env python3

# Demo program to show how to use the py3buddy module with DBus and integrate
# with Pidgin
#
# Uses python3-gobject-base and python3-pydbus (package names from Fedora)
#
# Copyright 2017-2019 - Armijn Hemel for Tjaldur Software Governance Solutions
# SPDX-Identifier: MIT

import sys
import os
import re
import py3buddy
import pydbus
import gi


def processmsg(account, sender, message, conversation, flags):
    # a demo version to show some of the capabilities of
    # the iBuddy

    # first reset the iBuddy
    ibuddy.ExecuteBuddyCommand("RESET")

    # a list of smileys as sent by Google Hangout
    smileys = [':D', ':-D', '^_^', ':-)', ':)', '☺️']

    # a command to execute when a smiley is received: loop through a
    # few colours, show a heartbeet, flap wings
    smilecommand = 'RED:HEART:WINGSHIGH:GO:SHORTSLEEP:YELLOW:NOHEART:WINGSLOW:GO:SHORTSLEEP:HEART:BLUE:WINGSHIGH:GO:SHORTSLEEP:PURPLE:NOHEART:WINGSLOW:GO:SHORTSLEEP:HEART:CYAN:WINGSHIGH:GO:SHORTSLEEP:WHITE:NOHEART:WINGSLOW:GO:SHORTSLEEP:RESET'
    for s in smileys:
        if s in message:
            ibuddy.ExecuteBuddyCommand(smilecommand)
            break

    # send an extra reset, as sometimes the iBuddy doesn't respond
    # to all commands.
    ibuddy.ExecuteBuddyCommand("RESET")


def main(argv):
    # connect to session DBus
    bus = pydbus.SessionBus()

    # This is very ugly, but the only way (I know) to expose the iBuddy to the
    # method processing the message from Pidgin
    global ibuddy

    # register a callback for messages that are received
    try:
        ibuddy = bus.get("nl.tjaldur.IBuddy", "/nl/tjaldur/IBuddy")
    except:
        ibuddy = None

    if ibuddy is None:
        print("iBuddy not found, exiting", file=sys.stderr)
        sys.exit(1)

    # register a callback for messages that are received
    purple = bus.get("im.pidgin.purple.PurpleService",
                     "/im/pidgin/purple/PurpleObject")
    purple.ReceivedImMsg.connect(processmsg)

    gi.repository.GObject.MainLoop().run()

    # finally reset the i-buddy again
    ibuddy.ExecuteBuddyCommand("RESET")

if __name__ == "__main__":
    main(sys.argv)
